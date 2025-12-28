import asyncio
import logging
import sys
import time

from .class_factory import ClassFactory
from .context import Context
from .enums import Status
from .exception import CortexException
from .node import Node
from .runtime import Runtime
from .state import State

PROCESSOR_CLASS_NAME = "Node"


class Cortex(object):
    def __init__(self):
        self.name = ""
        self.nodes = {}
        self.nexts = {}
        self.state = None
        self.factory = ClassFactory()

    def build(self, cortex_name: str, config: dict):
        for step in config:
            # Load the processor class from the specified file and register it
            # with the given name.
            self.factory.load(step["name"], step["file"], PROCESSOR_CLASS_NAME)

            node = self._create_node(step)
            if node is None:
                return False

            self._add_node_to_cortex(node, step)

        if not self._validate_cortex():
            raise CortexException(Status.CORTEX_NODE_MISSING)

        self._increment_in_degree()

        for node in self.nodes.values():
            if node.in_degree == 0:
                return True

        # If there is no node with in-degree 0, the graph has a cycle.
        raise CortexException(Status.CORTEX_HAS_CYCLE)

    async def run(self, ctx: Context, state: State) -> bool:
        try:
            runtime = Runtime()
            return await self._schedule_loop(ctx, state, runtime)
        except CortexException as e:
            ctx.status = e.status
            ctx.status_message = e.message
        except Exception as e:
            ctx.status = Status.RUN_TIME_ERROR
            raise e

        # Close the stream.
        ctx.stream.close()
        return False

    async def executor(self, ctx: Context, node: Node, state: State):
        logging.debug(f"processor begin, name:{node.processor.name}")

        state.timer_start(node.processor.name)
        if node.in_degree > 0:
            logging.error(
                f"execute node:{node.processor.name} in_degree > 0, value:{node.in_degree}"
            )
            state.timer_end(node.processor.name)
            return False

        start_at = time.time()
        process_ret = await node.processor.process(ctx, state)

        logging.info(
            f"processor:{node.processor.name} executed, result:{process_ret} cost:{time.time() - start_at}"
        )

        if node.processor.is_required and not process_ret:
            logging.error(f"node execute fail:{node.processor.name}")
            state.timer_end(node.processor.name)
            return False

        state.timer_end(node.processor.name)
        return True

    def _create_node(self, step):
        node_name = step.get("name", "")
        node_file = step.get("file", "")

        node = self.factory.get(node_name)
        if node is None:
            logging.error(f"create class failed, name:{node_name}({node_file})")
            return None

        node.name = node_name
        node.cortex = self.name
        node.group = step.get("group", "")
        node.conditions = step.get("when", {})
        node.events = step.get("listen", [])
        node.reentrant = step.get("reentrant", False)
        node.init()

        return node

    def _add_node_to_cortex(self, node, step):
        self.nodes[node.name] = node

        if node.name not in self.nexts:
            self.nexts[node.name] = set()

        for item in step.get("nexts", []):
            self.nexts[node.name].add(item)

    def _validate_cortex(self):
        for nodes_set in self.nexts.values():
            for node_name in nodes_set:
                if node_name not in self.nodes:
                    return False
        return True

    def _increment_in_degree(self):
        # Increment the in-degree of all nodes in the cortex.
        for nodes_set in self.nexts.values():
            for name in nodes_set:
                self.nodes[name].increment_in_degree()

    async def _schedule_loop(
        self, ctx: Context, state: State, runtime: Runtime
    ) -> bool:
        self._initialize_nodes(runtime)

        error = None

        try:
            while runtime.has_pending_nodes():
                self._schedule_nodes(ctx, state, runtime)
                await self._execute_nodes(runtime)
        except Exception as e:
            error = e

        # Safe check before accessing stream
        if hasattr(ctx, "_attributes") and "stream" in ctx._attributes:
            ctx.stream.close()

        if error:
            raise error

        return True

    def _initialize_nodes(self, runtime: Runtime):
        for _, node in self.nodes.items():
            if node.in_degree == 0 and len(node.events) == 0:
                runtime.add_waiting("root", node.name, self.nodes, self.nexts)

    def _schedule_nodes(self, ctx: Context, state: State, runtime: Runtime):
        nodes_to_run = [
            name for name, node in runtime.waiting.items() if node.in_degree == 0
        ]

        for name in nodes_to_run:
            runtime.add_running(ctx, state, name, self.executor, self.nodes, self.nexts)

    async def _execute_nodes(self, runtime: Runtime):
        done, _ = await asyncio.wait(
            runtime.get_running(), return_when=asyncio.FIRST_COMPLETED
        )

        # Processor the events that have been triggered.
        self._process_events(runtime)

        nodes_to_complete = [
            name for name, task in runtime.running.items() if task in done
        ]

        for name in nodes_to_complete:
            status, message = self._add_completed(name, runtime)

            if status == Status.NODE_CANCELLED:
                continue

            if status != Status.SUCCESS:
                raise CortexException(status, message)

    def _add_completed(self, name: str, runtime: Runtime) -> tuple[Status, str]:
        status, message = runtime.add_completed(self.nodes[name])

        if status in [Status.SUCCESS, Status.NODE_CANCELLED]:
            runtime.on_node_completed(name, self.nodes, self.nexts)

        return status, message

    def _process_events(self, runtime):
        for name, node in self.nodes.items():
            for event in node.events:
                if event in runtime.events:
                    parent = runtime.events[event]
                    runtime.add_waiting(parent, name, self.nodes, self.nexts)
                    continue

        runtime.events.clear()
