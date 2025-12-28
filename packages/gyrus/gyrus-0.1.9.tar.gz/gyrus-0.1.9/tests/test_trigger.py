import time
import unittest

from gyrus.context import Context
from gyrus.cortex_manager import CortexManager
from gyrus.state import State


class TestTrigger(unittest.IsolatedAsyncioTestCase):
    async def test_trigger(self):
        state = State()
        state.set("start_at", time.time())

        cm = CortexManager([{"name": "trigger", "path": "tests/cortices/trigger.yaml"}])
        cx = cm.get("trigger")

        with Context() as ctx:
            success = await cx.run(ctx, state)

            self.assertEqual(state.get("b"), 3)
            self.assertEqual(state.get("c"), 6)
            self.assertEqual(state.get("d"), 6)
            self.assertEqual(success, True)

    async def test_trigger_with_reentrant(self):
        state = State()
        state.set("start_at", time.time())
        state.set("reentrant_times", 0)

        cm = CortexManager(
            [
                {
                    "name": "trigger_reentrant",
                    "path": "tests/cortices/trigger_reentrant.yaml",
                }
            ]
        )
        cx = cm.get("trigger_reentrant")

        with Context() as ctx:
            success = await cx.run(ctx, state)

            self.assertEqual(state.get("b"), 3)
            self.assertEqual(state.get("c"), 6)
            self.assertEqual(state.get("d"), 6)
            self.assertGreaterEqual(state.get("reentrant_times"), 2)
            self.assertEqual(success, True)


if __name__ == "__main__":
    unittest.main()
