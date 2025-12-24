
from ..metamodel import ActionType, Behavior, Task, Action
from ..compiler import Pass

#--------------------------------------------------
# WhyMeta
#--------------------------------------------------

class WhyMeta():

    def __init__(self, task:Task):
        self.task = task

#--------------------------------------------------
# WhyNot
#--------------------------------------------------

class WhyNot(Pass):

    def __init__(self, task):
        super().__init__(copying=False)
        self.why_query = Task(behavior=Behavior.Sequence)
        self.why_meta = WhyMeta(task)
        self.walk(task)

    def query(self, query: Task, parent=None):
        for item in query.items:
            if item.action == ActionType.Get:
                self.explode_get(item, parent)

    def explode_get(self, action: Action, parent=None):
        # create a query for each subset of the parts on the get
        pass