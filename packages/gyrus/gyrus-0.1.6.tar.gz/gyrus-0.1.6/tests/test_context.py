import time
import unittest

from gyrus.context import Context
from gyrus.cortex_manager import CortexManager
from gyrus.state import State


class TestContext(unittest.IsolatedAsyncioTestCase):
    async def test_context(self):
        state = State()
        state.set("start_at", time.time())

        cm = CortexManager([{"name": "context", "path": "tests/cortices/context.yaml"}])
        cx = cm.get("context")

        with Context() as ctx:
            ctx.object_in_context = "this is value in context"
            success = await cx.run(ctx, state)

            self.assertEqual(state.get("context_from_case_b"), 2)
            self.assertEqual(state.get("context_from_case_c"), 2)
            self.assertEqual(state.get("object_in_context"), "this is value in context")
            self.assertEqual(success, True)


if __name__ == "__main__":
    unittest.main()
