import time
import unittest

from gyrus.context import Context
from gyrus.cortex_manager import CortexManager
from gyrus.enums import Status
from gyrus.exception import CortexException
from gyrus.state import State


class TestCortexManager(unittest.IsolatedAsyncioTestCase):
    async def test_circle(self):
        with self.assertRaises(CortexException) as cm:
            cm = CortexManager(
                [{"name": "circle", "path": "tests/cortices/circle.yaml"}]
            )

        self.assertEqual(cm.exception.status, Status.CORTEX_HAS_CYCLE)

    async def test_node_missing(self):
        with self.assertRaises(CortexException) as cm:
            cm = CortexManager(
                [{"name": "node_missing", "path": "tests/cortices/node_missing.yaml"}]
            )

        self.assertEqual(cm.exception.status, Status.CORTEX_NODE_MISSING)

    async def test_complex_dag(self):
        state = State()
        state.set("start_at", time.time())

        cm = CortexManager(
            [{"name": "complex_dag", "path": "tests/cortices/complex_dag.yaml"}]
        )
        cx = cm.get("complex_dag")

        with Context() as ctx:
            success = await cx.run(ctx, state)

            self.assertEqual(success, True)
            self.assertEqual(state.get("b"), 3)
            self.assertEqual(state.get("c"), 3)
            self.assertEqual(state.get("d"), 6)
            self.assertEqual(state.get("e"), 9)

    async def test_condition_simple(self):
        state = State()
        state.set("start_at", time.time())
        state.set("condition_a", "nerdduan")
        state.set("condition_b", "nerddeng")

        cm = CortexManager(
            [
                {
                    "name": "condition_simple",
                    "path": "tests/cortices/condition_simple.yaml",
                }
            ]
        )
        cx = cm.get("condition_simple")

        with Context() as ctx:
            success = await cx.run(ctx, state)

            self.assertEqual(state.get("b"), 3)
            self.assertEqual(state.get("c"), None)
            self.assertEqual(state.get("d"), 3)
            self.assertEqual(state.get("e"), 3)
            self.assertEqual(state.get("f"), 3)
            self.assertEqual(success, True)

    async def test_condition_nested(self):
        state = State()
        state.set("start_at", time.time())
        state.set("condition_a", "nerdduan")
        state.set("condition_b", "nerddeng")

        cm = CortexManager(
            [
                {
                    "name": "condition_nested",
                    "path": "tests/cortices/condition_nested.yaml",
                }
            ]
        )
        cx = cm.get("condition_nested")

        with Context() as ctx:
            success = await cx.run(ctx, state)

            self.assertEqual(state.get("b"), None)
            self.assertEqual(state.get("c"), 3)
            self.assertEqual(state.get("d"), 3)
            self.assertEqual(state.get("e"), 3)
            self.assertEqual(success, True)


if __name__ == "__main__":
    unittest.main()
