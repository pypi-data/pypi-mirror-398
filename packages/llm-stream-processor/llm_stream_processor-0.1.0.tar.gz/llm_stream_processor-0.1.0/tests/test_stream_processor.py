"""
Unit tests for llm_stream_processor functionality.
"""
import unittest
import asyncio
import os
import sys

# Ensure the project root is on the import path when tests are executed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from stream_processor import (
    drop,
    replace,
    passthrough,
    halt,
    continuous_drop,
    continuous_pass,
)
from stream_processor.engine.history import StreamHistory, NullHistory
from stream_processor.engine.types import ActionType, ActionDecision
from stream_processor.engine.registry import KeywordRegistry
from stream_processor.engine.processor import StreamProcessor
from stream_processor.engine.exceptions import StreamHalted
from stream_processor import llm_stream_processor


class TestActions(unittest.TestCase):
    def test_drop(self):
        d = drop()
        self.assertIsInstance(d, ActionDecision)
        self.assertEqual(d.type, ActionType.DROP)

    def test_replace(self):
        txt = 'X'
        d = replace(txt)
        self.assertEqual(d.type, ActionType.REPLACE)
        self.assertEqual(d.replacement, txt)

    def test_passthrough(self):
        d = passthrough()
        self.assertEqual(d.type, ActionType.PASS)

    def test_halt(self):
        d = halt()
        self.assertEqual(d.type, ActionType.HALT)

    def test_continuous(self):
        self.assertEqual(continuous_drop().type, ActionType.CONTINUE_DROP)
        self.assertEqual(continuous_pass().type, ActionType.CONTINUE_PASS)


class TestHistory(unittest.TestCase):
    def test_stream_history(self):
        hist = StreamHistory()
        hist.record_input('a')
        hist.record_output('b')
        dec = ActionDecision(ActionType.PASS)
        hist.record_action(1, 'kw', dec)
        self.assertEqual(hist.get_inputs(), ['a'])
        self.assertEqual(hist.get_outputs(), ['b'])
        self.assertEqual(hist.get_actions(), [(1, 'kw', dec)])

    def test_null_history(self):
        hist = NullHistory()
        hist.record_input('x')
        hist.record_output('y')
        hist.record_action(0, 'z', ActionDecision(ActionType.DROP))
        self.assertEqual(hist.get_inputs(), [])
        self.assertEqual(hist.get_outputs(), [])
        self.assertEqual(hist.get_actions(), [])


class TestRegistry(unittest.TestCase):
    def test_register_and_maxlen(self):
        reg = KeywordRegistry()
        self.assertEqual(reg.max_len(), 0)
        cb = lambda ctx: ActionDecision(ActionType.PASS)
        reg.register('foo', cb)
        self.assertEqual(reg.max_len(), 3)
        reg.register('longer', cb)
        self.assertEqual(reg.max_len(), len('longer'))

    def test_deregister(self):
        reg = KeywordRegistry()
        cb = lambda ctx: ActionDecision(ActionType.PASS)
        reg.register('a', cb)
        self.assertEqual(reg.max_len(), 1)
        reg.deregister('a', cb)
        self.assertEqual(reg.max_len(), 0)
        reg.deregister('nope')  # should not error

    def test_compile_trie(self):
        reg = KeywordRegistry()
        cb = lambda ctx: ActionDecision(ActionType.PASS)
        reg.register('ab', cb)
        reg.register('bc', cb)
        reg.compile()
        root = reg._root
        self.assertIn('a', root.children)
        self.assertIn('b', root.children)
        self.assertTrue(root.children['a'].children['b'].output)
        self.assertTrue(root.children['b'].children['c'].output)
    
    def test_register_invalid_keyword(self):
        reg = KeywordRegistry()
        with self.assertRaises(ValueError):
            reg.register('', lambda ctx: None)

    def test_register_non_callable(self):
        reg = KeywordRegistry()
        with self.assertRaises(TypeError):
            reg.register('foo', 'not_callable')

    def test_deregister_invalid_keyword(self):
        reg = KeywordRegistry()
        with self.assertRaises(ValueError):
            reg.deregister('', None)

    def test_deregister_non_callable(self):
        reg = KeywordRegistry()
        with self.assertRaises(TypeError):
            reg.deregister('foo', callback=123)


class TestProcessor(unittest.TestCase):
    def run_seq(self, reg, text, history=True):
        sp = StreamProcessor(reg, record_history=history)
        out = []
        for ch in text:
            try:
                out.extend(sp.process(ch))
            except StreamHalted:
                break
        out.extend(sp.flush())
        return ''.join(out)

    def test_replace(self):
        reg = KeywordRegistry()
        reg.register('foo', lambda ctx: replace('X'))
        self.assertEqual(self.run_seq(reg, 'afood'), 'aXd')

    def test_drop(self):
        reg = KeywordRegistry()
        reg.register('xy', drop)
        self.assertEqual(self.run_seq(reg, 'axyz'), 'az')

    def test_passthrough(self):
        reg = KeywordRegistry()
        reg.register('no', passthrough)
        self.assertEqual(self.run_seq(reg, 'nonsense'), 'nonsense')

    def test_halt(self):
        reg = KeywordRegistry()
        reg.register('stop', halt)
        self.assertEqual(self.run_seq(reg, 'abstopcd'), 'ab')

    def test_halt_during_drop_mode(self):
        reg = KeywordRegistry()
        reg.register('<s>', continuous_drop)
        reg.register('stop', halt)
        txt = 'ab<s>cdstop'
        self.assertEqual(self.run_seq(reg, txt), 'ab')

    def test_continuous(self):
        reg = KeywordRegistry()
        reg.register('<s>', continuous_drop)
        reg.register('<e>', continuous_pass)
        txt = '123<s>456<e>789'
        self.assertEqual(self.run_seq(reg, txt), '123<e>789')

    def test_overlap(self):
        reg = KeywordRegistry()
        reg.register('he', lambda ctx: replace('H'))
        reg.register('she', lambda ctx: replace('S'))
        self.assertEqual(self.run_seq(reg, 'shehe'), 'SH')

    def test_prefix_safety(self):
        reg = KeywordRegistry()
        reg.register('abc', drop)
        self.assertEqual(self.run_seq(reg, 'xabc'), 'x')

    def test_history_enabled(self):
        reg = KeywordRegistry()
        rec = []
        def cb(ctx):
            rec.append((ctx.absolute_pos, ''.join(ctx.buffer)))
            return replace('X')
        reg.register('ab', cb)
        self.assertEqual(self.run_seq(reg, 'xabcd'), 'xXcd')
        self.assertIn((3, 'xab'), rec)

    def test_history_disabled(self):
        reg = KeywordRegistry()
        def cb(ctx):
            self.assertEqual(ctx.history.get_inputs(), [])
            self.assertEqual(ctx.history.get_outputs(), [])
            self.assertEqual(ctx.history.get_actions(), [])
            return replace('X')
        reg.register('a', cb)
        self.assertEqual(self.run_seq(reg, 'a', history=False), 'X')

    def test_callback_exception(self):
        reg = KeywordRegistry()
        def cb(ctx): raise ValueError('boom')
        reg.register('a', cb)
        with self.assertRaises(ValueError):
            self.run_seq(reg, 'a')


class TestDecorator(unittest.TestCase):
    def collect_async(self, gen_fn):
        return asyncio.run(self._collect(gen_fn))

    async def _collect(self, gen_fn):
        out = []
        async for item in gen_fn():
            out.append(item)
        return out

    def test_sync_token(self):
        reg = KeywordRegistry()
        reg.register('o', lambda ctx: replace('X'))
        @llm_stream_processor(reg, yield_mode='token')
        def gen():
            yield 'hello'
            yield ' world'
        self.assertEqual(list(gen()), ['hellX', ' wXrld'])

    def test_sync_char(self):
        reg = KeywordRegistry()
        reg.register('lo', lambda ctx: replace('Z'))
        @llm_stream_processor(reg, yield_mode='char')
        def gen(): yield 'hello'
        self.assertEqual(''.join(gen()), 'helZ')

    def test_sync_chunk(self):
        reg = KeywordRegistry()
        @llm_stream_processor(reg, yield_mode='chunk:3')
        def gen(): yield 'abcdefg'
        self.assertEqual(list(gen()), ['abc', 'def', 'g'])

    def test_async_token(self):
        reg = KeywordRegistry()
        reg.register('a', lambda ctx: replace('X'))
        @llm_stream_processor(reg, yield_mode='token')
        async def gen():
            yield 'a'; yield 'bc'
        self.assertEqual(self.collect_async(gen), ['X', 'bc'])

    def test_async_char(self):
        reg = KeywordRegistry()
        reg.register('ab', lambda ctx: replace('Y'))
        @llm_stream_processor(reg, yield_mode='char')
        async def gen(): yield 'ab'
        self.assertEqual(''.join(self.collect_async(gen)), 'Y')

    def test_async_chunk(self):
        reg = KeywordRegistry()
        @llm_stream_processor(reg, yield_mode='chunk:2')
        async def gen(): yield 'abcd'
        self.assertEqual(self.collect_async(gen), ['ab', 'cd'])

    def test_halt_decorator(self):
        reg = KeywordRegistry()
        reg.register('stop', halt)
        @llm_stream_processor(reg, yield_mode='token')
        def gen():
            yield 'foo'; yield 'stop'; yield 'bar'
        self.assertEqual(list(gen()), ['foo'])


if __name__ == '__main__':
    unittest.main()