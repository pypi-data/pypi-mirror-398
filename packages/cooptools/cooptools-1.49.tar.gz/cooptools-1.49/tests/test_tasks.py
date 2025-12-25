import unittest
import datetime
import cooptools.taskProcessing as tsk
import cooptools.date_utils as du

class TestTaskClasses(unittest.TestCase):
    def test_task_link(self):
        link = tsk.TaskLink(task_link_type='predecessor', linked_task_id='123')
        self.assertEqual(link.task_link_type, tsk.TaskLinkType.PREDECESSOR)
        self.assertEqual(link.linked_task_id, '123')

    def test_predecessor_task_link(self):
        link = tsk.PredecessorTaskLink(linked_task_id='123', require_same_agent=True, prevent_intermediate_tasks=False)
        self.assertEqual(link.task_link_type, tsk.TaskLinkType.PREDECESSOR)
        self.assertTrue(link.require_same_agent)
        self.assertFalse(link.prevent_intermediate_tasks)

    def test_execution_criteria_defaults(self):
        criteria = tsk.ExecutionCriteria()
        self.assertEqual(criteria.criteria_payload, {})
        self.assertEqual(criteria.required_agent_id_options, [])
        self.assertEqual(criteria.required_agent_type_options, [])

    def test_task_meta_initialization(self):
        meta = tsk.TaskMeta(task_type='test_task')
        self.assertEqual(meta.task_type, 'test_task')
        self.assertIsInstance(meta.created_date, datetime.datetime)
        self.assertEqual(meta.priority, 999)

    def test_task_initialization(self):
        meta = tsk.TaskMeta(task_type='test_task')
        execution_criteria = tsk.ExecutionCriteria()
        task = tsk.Task(meta=meta, execution_criteria=execution_criteria)
        self.assertEqual(task.meta.task_type, 'test_task')
        self.assertIsInstance(task.execution_criteria, tsk.ExecutionCriteria)

    def test_mission_criteria_payload(self):
        payload = tsk.MissionCriteriaPayload(task_names=['Task1', 'Task2'])
        instruction_payload = payload.resolve_instruction_payload()
        self.assertIsInstance(instruction_payload, tsk.MissionInstructionPayload)
        self.assertEqual(instruction_payload.task_names, ['Task1', 'Task2'])

    def test_move_criteria_payload(self):
        payload = tsk.MoveCriteriaPayload(waypoints=['WP1', 'WP2'])
        instruction_payload = payload.resolve_instruction_payload()
        self.assertIsInstance(instruction_payload, tsk.MoveInstructionPayload)
        self.assertEqual(instruction_payload.waypoints, ['WP1', 'WP2'])


    def test__HeirarchyCriteria__init_today_01(self):
        hc = tsk.HeirarchyCriteria(
            task_group_id='TODAY'
        )
        self.assertEqual(hc.task_group_id, str(du.date_to_condensed_string(
            du.today(remove_hrs=True, remove_min=True, remove_sec=True, remove_ms=True))))

    def test__HeirarchyCriteria__init_today_02(self):
        hc = tsk.HeirarchyCriteria(
            task_group_id='test_<TODAY>'
        )
        value = str(du.date_to_condensed_string(
            du.today(remove_hrs=True, remove_min=True, remove_sec=True, remove_ms=True)))

        self.assertEqual(hc.task_group_id, f"test_{value}")

if __name__ == "__main__":
    unittest.main()
