import time
import unittest

from gyrus.context import Context
from gyrus.cortex_manager import CortexManager
from gyrus.state import State


class TestCortexManager(unittest.IsolatedAsyncioTestCase):
    async def test_early_stopping(self):
        state = State()
        state.set("start_at", time.time())

        cm = CortexManager(
            [{"name": "early_stopping", "path": "tests/cortices/early_stopping.yaml"}]
        )
        cx = cm.get(
            "early_stopping",
        )

        with Context() as ctx:
            success = await cx.run(ctx, state)

            self.assertEqual(state.get("b"), None)
            self.assertEqual(state.get("c"), None)
            self.assertEqual(state.get("d"), 4)
            self.assertEqual(success, True)


if __name__ == "__main__":
    unittest.main()
