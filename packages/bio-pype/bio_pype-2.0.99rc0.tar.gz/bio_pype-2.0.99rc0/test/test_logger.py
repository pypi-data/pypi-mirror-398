import unittest
import os
from pype.logger import PypeLogger
from pype.misc import generate_uid
from pype.modules import profiles


class TestLogger(unittest.TestCase):

    def test_PypeLogger(self):
        profile = profiles.get_profiles({})
        log_name = generate_uid()
        test_str = 'Info %i for %s log'
        prog_1 = 'main'
        test = PypeLogger(log_name, 'test/data/tmp/', profile['test_path'])
        test.log.info(test_str % (1, prog_1))
        test.log.info(test_str % (2, prog_1))
        t1 = 0
        with open(
            os.path.join(
                test.__path__, '%s.log' % log_name), 'rt') as log_main:
            for line in log_main:
                if test_str % (
                    1, prog_1) in line.rstrip() or test_str % (
                        2, prog_1) in line.rstrip():
                    t1 += 1
        self.assertEqual(t1, 2)
        self.assertEqual(list(test.programs_logs.keys()), [])
        prog_x = generate_uid()
        test.add_log(prog_x)
        self.assertEqual(list(test.programs_logs.keys())[0], prog_x)
        test.programs_logs[prog_x].log.info(test_str % (1, prog_x))
        t2 = 0
        with open(
            os.path.join(
                test.__path__, prog_x, '%s.log' % prog_x), 'rt') as log_x:
            for line in log_x:
                t2 += 1
        self.assertEqual(t2, 1)
        t3 = 0
        with open(
            os.path.join(
                test.__path__, '%s.log' % log_name), 'rt') as log_main:
            for line in log_main:
                if test_str % (1, prog_x) in line.rstrip():
                    t3 += 1
        self.assertEqual(t3, 0)


if __name__ == '__main__':
    unittest.main()
