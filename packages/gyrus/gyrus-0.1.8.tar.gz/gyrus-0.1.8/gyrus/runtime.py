import asyncio
from typing import Dict, Optional

from .context import Context
from .enums import Status
from .exception import CortexException
from .node import Node
from .processor import Processor
from .state import State


class Runtime(object):
    def __init__(self):
        self.waiting: Dict[str, Node] = {}
        self.running: Dict[str, asyncio.Task] = {}
        self.completed: Dict[str, Status] = {}

        # When concurrent execution causes multiple processors to return and
        # trigger the same event simultaneously, this event should only be
        # executed once. The execution logic conflicts caused by concurrency
        # should be resolved by the triggered processor itself.
        #
        # eg:
        # processor_a -> trigger(["event_a"])
        # processor_b -> trigger(["event_a"])
        #
        # class Node(Processor):
        #     async def process(self, ctx: Context, state: State) -> bool:
        #         if state.get("something_from_processor_a") is True:
        #             do_something_a()
        #
        #         if state.get("something_from_processor_b") is True:
        #             do_something_b()
        # ...

        self.events: Dict[str, str] = {}

    def is_visited(self, node: Processor) -> bool:
        if node.reentrant:
            return False
        if node.name in self.waiting:
            return True
        if node.name in self.running:
            return True
        if node.name in self.completed:
            return True
        return False

    def add_waiting(self, parent: str, name: str, nodes: Dict, nexts: Dict) -> bool:
        if self.is_visited(nodes[name]):
            return False

        nodes[name].trigger = self.trigger(parent)
        nodes[name].stop = self.stop

        self.waiting[name] = Node(nodes[name], nexts[name], parent=parent)
        return True

    def add_running(
        self,
        ctx: Context,
        state: State,
        name: str,
        executor,
        nodes: Optional[Dict] = None,
        nexts: Optional[Dict] = None,
    ) -> bool:
        if name in self.running:
            raise CortexException(
                Status.RUN_TIME_ERROR, f"node({name}) has been already in running"
            )

        node = self.waiting.pop(name)

        # Check if the node can be executed, if not, mark as completed and reduce in-degree of downstream nodes.
        if not node.check(state):
            # Mark the node as completed (skipped due to condition not met)
            self.completed[name] = Status.SUCCESS
            # Reduce in-degree of downstream nodes
            if nodes is not None and nexts is not None:
                self.on_node_completed(name, nodes, nexts)
            return True

        task = asyncio.get_event_loop().create_task(
            self.executor_wrapper(executor, [ctx.clone(node.parent), node, state])
        )

        # Set the name of the task to the group of the processor.
        task.set_name(node.processor.group)

        self.running[name] = task
        return True

    def get_running(self) -> list:
        return self.running.values()

    def get_task_status(self, task) -> tuple[Status, str]:
        if task.cancelled():
            return Status.NODE_CANCELLED, "Node execution cancelled"

        exception = task.exception()
        if exception is not None:
            # Convert exception object to string representation
            exception_str = str(exception)
            if not exception_str:
                exception_str = repr(exception)
            return Status.NODE_EXECUTE_FAIL, exception_str

        if task.result() is False:
            return (
                Status.NODE_EXECUTE_FAIL,
                "Node execution failed without exception details",
            )

        return Status.SUCCESS, "Node execution successful"

    def add_completed(self, node: Processor) -> tuple[Status, str]:
        if node.name in self.completed and not node.reentrant:
            raise CortexException(
                Status.RUN_TIME_ERROR,
                f"node({node.name}) has been already in completed",
            )

        task = self.running.pop(node.name)
        status, message = self.get_task_status(task)

        self.completed[node.name] = status
        return status, message

    def on_node_completed(self, name: str, nodes: Dict, nexts: Dict) -> bool:
        if name not in nexts:
            raise CortexException(
                Status.CORTEX_CONFIG_ERROR, f"get next nodes of {name} failed"
            )

        node_nexts = nexts[name]

        for child in node_nexts:
            self.add_waiting(name, child, nodes, nexts)

        for name, node in self.waiting.items():
            if name in node_nexts:
                node.in_degree -= 1
        return True

    def has_pending_nodes(self):
        return len(self.waiting) + len(self.running) > 0

    def executor_wrapper(self, executor, args):
        try:
            return executor(*args)
        except asyncio.CancelledError as _:
            return True

    def trigger(self, parent: str):
        def currying(events: list) -> bool:
            for event in events:
                self.events[event] = parent
            return True

        return currying

    def stop(self, group: str):
        if not group:
            return

        for _, node in self.running.items():
            if node.get_name() == group:
                node.cancel()

        for name, node in self.waiting.items():
            if node.processor.group == group:
                self.waiting.pop(name)
