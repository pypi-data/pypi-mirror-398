from typing import List, Dict, Iterable, Self, Optional
from cooptools.taskProcessing import dcs
from cooptools.dataStore import InMemoryDataStore, DataStoreProtocol
from cooptools.protocols import UniqueIdentifier
from cooptools.coopEnum import CoopEnum
from dataclasses import dataclass, field

class ExecutionStatus(CoopEnum):
    NEW = 100
    ASSIGNED = 400
    DISPATCHED = 500
    ENDED = 900

class EndState(CoopEnum):
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    FAULTED = 'faulted'


@dataclass(slots=True)
class TaskExecutionMonitor:
    task: dcs.TaskMeta
    execution_status: ExecutionStatus = field(default=ExecutionStatus.NEW)
    end_state: Optional[EndState] = None

    def update_state(self,
                     new_state: ExecutionStatus,
                     end_state: EndState = None) -> Self:
        if end_state is not None and new_state != ExecutionStatus.ENDED:
            raise ValueError(f"Unable to set an end state if the new_state is not ended")

        if new_state == ExecutionStatus.ENDED and end_state is None:
            raise ValueError(f"Unable to set execution status without providing and end_state")

        self.execution_status = new_state
        self.end_state = end_state

        return self

    @property
    def Id(self):
        return self.task.id

class TaskProcessor:
    def __init__(self,
                 task_store: DataStoreProtocol = None,
                 execution_status_store: DataStoreProtocol = None):
        self._tasks_store: DataStoreProtocol = task_store or InMemoryDataStore()
        self._execution_status_store: DataStoreProtocol = execution_status_store or InMemoryDataStore()

    def update_loop(self):
        tasks_to_process = self.OpenTasks

        for task_execution in tasks_to_process:
            if task_execution.execution_status == ExecutionStatus.NEW:
                ''' Check if can be assigned & assign'''
                self.update_task(task_execution.task.id,
                                 new_state=ExecutionStatus.ASSIGNED)
            if task_execution.execution_status == ExecutionStatus.ASSIGNED:
                continue
            if task_execution.execution_status == ExecutionStatus.DISPATCHED:
                raise NotImplementedError()

    def new_tasks(self,
                  tasks: Iterable[dcs.TaskMeta]) -> Self:
        self._tasks_store.add(tasks)
        self._execution_status_store.add([TaskExecutionMonitor(task) for task in tasks])
        return self

    def update_task(self,
                    task_id: UniqueIdentifier,
                    new_state: ExecutionStatus,
                    end_state: EndState = None):
        status_tracker: TaskExecutionMonitor = self._execution_status_store.get(ids=[task_id])[task_id]
        status_tracker.update_state(new_state=new_state, end_state=end_state)
        self._execution_status_store.update(items=[status_tracker])
        return self

    def get_task_state(self, task_id: UniqueIdentifier) -> TaskExecutionMonitor:
        return self._execution_status_store.get(ids=[task_id])[task_id]

    @property
    def Tasks(self) -> Dict[UniqueIdentifier, dcs.TaskMeta]:
        return self._tasks_store.get()

    @property
    def TaskExecutionStates(self) -> Dict[UniqueIdentifier, TaskExecutionMonitor]:
        return self._execution_status_store.get()

    @property
    def OpenTasks(self) -> List[TaskExecutionMonitor]:
        return [x for x in self.TaskExecutionStates.values() if x.execution_status != ExecutionStatus.ENDED]

if __name__ == "__main__":
    from pprint import pprint

    def _init_a_task_processor(n_tasks: int):
        tp = TaskProcessor()
        tp.new_tasks(
            tasks=[
                dcs.TaskMeta(
                    id=x,
                    task_group_id='tg1',
                    task_type="user type",
                )
            for x in range(n_tasks)]
        )
        return tp

    def test_add_tasks():
        n_tasks = 5
        tp = _init_a_task_processor(n_tasks)

        assert len(tp.Tasks) == n_tasks
        assert [status_monitor.execution_status == ExecutionStatus.NEW for task_id, status_monitor in tp.TaskExecutionStates.items()]

    def test_update_tasks():
        n_tasks = 5
        tp = _init_a_task_processor(n_tasks)
        id_to_update = tp.Tasks[0].id
        new_state = ExecutionStatus.NOTELIGIBLE
        tp.update_task(id_to_update, new_state=new_state)

        task_execution_state = tp.get_task_state(id_to_update)

        assert task_execution_state.execution_status == new_state

    test_add_tasks()
    test_update_tasks()