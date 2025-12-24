from v0.relationalai.early_access.dsl.core.stack import Stack


class ContextStack(Stack):

    def __init__(self):
        super().__init__()

    def root_context(self):
        ctx = self.top()
        if ctx is None:
            raise Exception('Context stack is empty')
        return ctx