import unittest
from cooptools.commandDesignPattern import CommandBatch, CommandProtocol, CommandController
from dataclasses import dataclass
from cooptools.commandDesignPattern.exceptions import ResolveBatchException, ResolveStateException

@dataclass
class Dummy_State:
    amount: int = 0

@dataclass
class Dummy_Command(CommandProtocol):
    adjustment: int

    def execute(self, state):
        state.amount += self.adjustment
        return state
        # return Dummy_State(amount=state.amount + self.adjustment)

@dataclass
class Dummy_CommandThatFails(CommandProtocol):
    adjustment: int

    def execute(self, state):
        raise Exception(f"Dummy Exception")

class Test_CommandDesignPattern(unittest.TestCase):

    def test__register_commands(self):
        # arrange
        state = Dummy_State()
        controller = CommandController(state)
        commands = [
            Dummy_Command(adjustment=1000),
            Dummy_Command(adjustment=500)
        ]


        # act
        controller.execute(commands=commands)

        # assert
        self.assertEqual(len(controller.ActiveCommands), len(commands))
        self.assertEqual(controller.cursor, len(commands))

    def test__resolve_state(self):

        # arrange
        state = Dummy_State()
        controller = CommandController(state)
        commands = [
            Dummy_Command(adjustment=1000),
            Dummy_Command(adjustment=500)
        ]

        # act
        state = controller.execute(commands=commands)

        # assert
        self.assertEqual(len(controller.ActiveCommands), len(commands))
        self.assertEqual(state.amount, 1500)
        self.assertEqual(controller.cursor, len(commands))

    def test__add_batch_command(self):
        # arrange
        state = Dummy_State()
        controller = CommandController(state)
        commands =[
            Dummy_Command(adjustment=1000),
            Dummy_Command(adjustment=500)
        ]
        batch = CommandBatch(commands=commands)

        # act
        state = controller.execute(commands=[batch])

        # assert
        self.assertEqual(len(controller.ActiveCommands), 1)
        self.assertEqual(state.amount, 1500)
        self.assertEqual(controller.cursor, 1)

    def test__add_batch_and_command(self):
        # arrange
        state = Dummy_State()
        controller = CommandController(state)

        batch = CommandBatch(commands=[
            Dummy_Command(adjustment=1000),
            Dummy_Command(adjustment=500)
        ])
        commands = [
            batch,
            Dummy_Command(adjustment=500)
        ]

        # act
        state = controller.execute(commands=commands)

        # assert
        self.assertEqual(len(controller.ActiveCommands), 2)
        self.assertEqual(state.amount, 2000)

    def test__undo_resolve(self):
        # arrange
        state = Dummy_State()
        controller = CommandController(state)

        batch = CommandBatch(commands=[
            Dummy_Command(adjustment=1000),
            Dummy_Command(adjustment=500)
        ])
        commands = [
            batch,
            Dummy_Command(adjustment=500)
        ]

        # act
        state = controller.execute(commands=commands)
        state = controller.undo()

        # assert
        self.assertEqual(len(controller.ActiveCommands), 1)
        self.assertEqual(state.amount, 1500)
        self.assertEqual(controller.cursor, len(commands) - 1)

    def test__undo_redo_resolve(self):
        # arrange
        state = Dummy_State()
        controller = CommandController(state)

        batch = CommandBatch(commands=[
            Dummy_Command(adjustment=1000),
            Dummy_Command(adjustment=500)
        ])
        commands = [
            batch,
            Dummy_Command(adjustment=500)
        ]

        # act
        state = controller.execute(commands=commands)
        state = controller.undo()
        state = controller.redo()

        # assert
        self.assertEqual(len(controller.ActiveCommands), 2)
        self.assertEqual(state.amount, 2000)

        self.assertEqual(controller.cursor, len(commands))

    def test__resolve_fails_revert(self):
        # arrange
        state = Dummy_State()
        controller = CommandController(state)

        commands=[
            Dummy_Command(adjustment=1000),
            Dummy_CommandThatFails(adjustment=500)
        ]

        # act


        # assert
        self.assertRaises(ResolveStateException, lambda: controller.execute(commands=commands))
        self.assertEqual(state.amount, 0)


    def test__resolve_fails_no_revert(self):
        # arrange
        state = Dummy_State()
        controller = CommandController(state)

        commands=[
            Dummy_Command(adjustment=1000),
            Dummy_CommandThatFails(adjustment=500)
        ]

        # act

        # assert
        self.assertRaises(ResolveStateException, lambda: controller.execute(commands=commands))

