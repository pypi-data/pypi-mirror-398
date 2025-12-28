from .processor import Processor
from .state import State


class Node(object):
    def __init__(self, processor: Processor, childs: set, parent: str = "root"):
        self.processor = processor
        self.childs = childs
        self.parent = parent
        self.in_degree = processor.in_degree

    def check(self, state: State = None, conditions: dict = {}, validator=None):
        if not conditions:
            conditions = self.processor.conditions

        if isinstance(conditions, tuple):
            return state.get(conditions[0]) == conditions[1]

        if isinstance(conditions, dict) and not conditions:
            return True

        results = []

        if isinstance(conditions, dict):
            for key, value in conditions.items():
                if key == "not":
                    return not self.check(state, value)

                if key == "all":
                    return self.check(state, value, all)

                if key == "any":
                    return self.check(state, value, any)

                results.append(self.check(state, (key, value)))

        if isinstance(conditions, list):
            for condition in conditions:
                results.append(self.check(state, condition))

        if not validator:
            validator = all

        return validator(results)
