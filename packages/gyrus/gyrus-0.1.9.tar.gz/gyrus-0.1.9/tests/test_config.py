import time
import unittest

from gyrus.context import Context
from gyrus.cortex_manager import CortexManager
from gyrus.state import State


class TestConfig(unittest.IsolatedAsyncioTestCase):
    async def test_context(self):
        state = State()
        state.set("start_at", time.time())

        cm = CortexManager([{"name": "config", "path": "tests/cortices/config.yaml"}])
        cx = cm.get("config")

        with Context() as ctx:
            success = await cx.run(ctx, state)

            self.assertEqual(success, True)
            self.assertEqual(state.get("name"), "nerdduan")
            self.assertEqual(state.get("age"), 10086)


if __name__ == "__main__":
    unittest.main()
