from logging import getLogger, Handler, DEBUG
import unittest


from conda import exceptions
from conda import instructions
from conda.instructions import execute_instructions, commands, PROGRESS_CMD


def test_expected_operation_order():
    """Ensure expected order of operations"""
    expected = (
        instructions.FETCH,
        instructions.EXTRACT,
        instructions.UNLINK,
        instructions.LINK,
        instructions.SYMLINK_CONDA,
        instructions.RM_EXTRACTED,
        instructions.RM_FETCHED,
    )
    assert expected == instructions.action_codes


class TestHandler(Handler):
    def __init__(self):
        Handler.__init__(self)
        self.setLevel(DEBUG)
        self.records = []

    def handle(self, record):
        self.records.append((record.name, record.msg))



class TestExecutePlan(unittest.TestCase):

    def test_invalid_instruction(self):
        index = {'This is an index': True}

        plan = [('DOES_NOT_EXIST', ())]

        with self.assertRaises(exceptions.InvalidInstruction):
            execute_instructions(plan, index, verbose=False)

    def test_simple_instruction(self):

        index = {'This is an index': True}

        def simple_cmd(state, arg):
            simple_cmd.called = True
            simple_cmd.call_args = (arg,)

        commands['SIMPLE'] = simple_cmd

        plan = [('SIMPLE', ('arg1',))]

        execute_instructions(plan, index, verbose=False)

        self.assertTrue(simple_cmd.called)
        self.assertTrue(simple_cmd.call_args, ('arg1',))

    def test_state(self):

        index = {'This is an index': True}

        def simple_cmd(state, arg):
            expect, x = arg
            state.setdefault('x', 1)
            self.assertEqual(state['x'], expect)
            state['x'] = x
            simple_cmd.called = True

        commands['SIMPLE'] = simple_cmd

        plan = [('SIMPLE', (1, 5)),
                ('SIMPLE', (5, None)),
                ]

        execute_instructions(plan, index, verbose=False)
        self.assertTrue(simple_cmd.called)

    def test_progess(self):

        index = {'This is an index': True}

        plan = [
            ('PROGRESS', '2'),
            ('LINK', 'ipython'),
            ('LINK', 'menuinst'),
        ]

        def cmd(state, arg):
            pass  # NO-OP

        _commands = {'PROGRESS': PROGRESS_CMD, 'LINK': cmd}
        h = TestHandler()

        update_logger = getLogger('progress.update')
        update_logger.setLevel(DEBUG)
        update_logger.addHandler(h)

        stop_logger = getLogger('progress.stop')
        stop_logger.setLevel(DEBUG)
        stop_logger.addHandler(h)

        execute_instructions(plan, index, _commands=_commands)

        update_logger.removeHandler(h)
        stop_logger.removeHandler(h)

        expected = [('progress.update', ('ipython', 0)),
                    ('progress.update', ('menuinst', 1)),
                    ('progress.stop', None)
                    ]

        self.assertEqual(h.records, expected)

if __name__ == '__main__':
    unittest.main()
