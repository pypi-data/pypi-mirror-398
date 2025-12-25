##
# cSpell:word pype

import unittest
import sys
import os
from pype import argparse
from pype.modules import snippets
from pype.misc import generate_uid
from io import StringIO



class TestSnippets(unittest.TestCase):

    def setUp(self):
        self.held, sys.stdout = sys.stdout, StringIO()
        self.parser = argparse.ArgumentParser(prog='pype', description='Test')
        self.subparsers = self.parser.add_subparsers(dest='modules')

    def test_snippets(self):
        a = generate_uid()
        b = generate_uid()
        c = generate_uid()

        tmp_path = os.path.join('test', 'data', 'tmp')
        input_a = os.path.join(tmp_path, '%s.txt' % a)
        output_b = os.path.join(tmp_path, '%s.txt' % b)
        output_c = os.path.join(tmp_path, '%s.txt' % c)
        with open(input_a, 'wt') as file_in:
            file_in.write(a)

        snippets.snippets(self.subparsers, None, [
            '--log', tmp_path, 'test_base', '--input', input_a,
            '--output', output_b], 'test_path')
        with open(output_b, 'rt') as file_out:
            self.assertEqual(
                file_out.read(), '%sthis is a dummy file!\n' % a.lower())
        snippets.snippets(self.subparsers, None, [
            '--log', tmp_path, 'test_adv', '--input', input_a,
            '--output', output_c], 'test_path')
        with open(
            output_b, 'rt') as file_out1, open(
                output_c, 'rt') as file_out2:
            self.assertEqual(
                file_out1.read(), file_out2.read())

    def test_friendly_name(self):
        friendly_name = snippets.PYPE_SNIPPETS_MODULES[
            'reverse_fa'].friendly_name({'--input': 'test_file.txt'})
        self.assertEqual(friendly_name, 'reverse_fa_test_file')

    def test_snippet_exit_code_failure(self):
        """Test that snippet with non-zero exit code causes sys.exit(1)."""
        tmp_path = os.path.join('test', 'data', 'tmp')
        input_file = os.path.join(tmp_path, 'test_fail_input.txt')
        output_file = os.path.join(tmp_path, 'test_fail_output.txt')

        # Create input file
        with open(input_file, 'wt') as f:
            f.write('test data\n')

        # Run snippet that exits with code 1
        # Should catch SystemExit with code 1
        with self.assertRaises(SystemExit) as context:
            snippets.snippets(self.subparsers, None, [
                '--log', tmp_path, 'test_fail_exit_code',
                '--input', input_file,
                '--output', output_file
            ], 'test_path')

        # Verify it exited with code 1 (not 0 or 2)
        self.assertEqual(context.exception.code, 1)

        # Clean up
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

    def test_snippet_missing_output_failure(self):
        """Test that snippet with missing output file causes sys.exit(1)."""
        tmp_path = os.path.join('test', 'data', 'tmp')
        input_file = os.path.join(tmp_path, 'test_missing_input.txt')
        output_file = os.path.join(tmp_path, 'test_missing_output.txt')

        # Create input file
        with open(input_file, 'wt') as f:
            f.write('test data\n')

        # Ensure output doesn't exist
        if os.path.exists(output_file):
            os.remove(output_file)

        # Run snippet that doesn't create output
        # Should catch SystemExit with code 1
        with self.assertRaises(SystemExit) as context:
            snippets.snippets(self.subparsers, None, [
                '--log', tmp_path, 'test_fail_missing_output',
                '--input', input_file,
                '--output', output_file
            ], 'test_path')

        # Verify it exited with code 1
        self.assertEqual(context.exception.code, 1)

        # Verify output was NOT created
        self.assertFalse(os.path.exists(output_file))

        # Clean up
        if os.path.exists(input_file):
            os.remove(input_file)

    def test_snippet_skip_check_results_md(self):
        """Test markdown snippet with check_results=False succeeds even with missing output."""
        tmp_path = os.path.join('test', 'data', 'tmp')
        input_file = os.path.join(tmp_path, 'test_skip_input_md.txt')
        output_file = os.path.join(tmp_path, 'test_skip_output_md.txt')

        # Create input file
        with open(input_file, 'wt') as f:
            f.write('test data\n')

        # Ensure output doesn't exist
        if os.path.exists(output_file):
            os.remove(output_file)

        # Run markdown snippet with check_results=False
        # Should succeed even though output file is not created
        try:
            snippets.snippets(self.subparsers, None, [
                '--log', tmp_path, 'test_skip_check_results_md',
                '--input', input_file,
                '--output', output_file
            ], 'test_path')
        except SystemExit:
            self.fail("Markdown snippet with check_results=False should not exit with error")

        # Verify output was NOT created
        self.assertFalse(os.path.exists(output_file))

        # Clean up
        if os.path.exists(input_file):
            os.remove(input_file)

    def test_snippet_skip_check_results_py(self):
        """Test Python snippet with check_results() returning False succeeds with missing output."""
        tmp_path = os.path.join('test', 'data', 'tmp')
        input_file = os.path.join(tmp_path, 'test_skip_input_py.txt')
        output_file = os.path.join(tmp_path, 'test_skip_output_py.txt')

        # Create input file
        with open(input_file, 'wt') as f:
            f.write('test data\n')

        # Ensure output doesn't exist
        if os.path.exists(output_file):
            os.remove(output_file)

        # Run Python snippet with check_results() returning False
        # Should succeed even though output file is not created
        try:
            snippets.snippets(self.subparsers, None, [
                '--log', tmp_path, 'test_skip_check_results_py',
                '--input', input_file,
                '--output', output_file
            ], 'test_path')
        except SystemExit:
            self.fail("Python snippet with check_results()=False should not exit with error")

        # Verify output was NOT created
        self.assertFalse(os.path.exists(output_file))

        # Clean up
        if os.path.exists(input_file):
            os.remove(input_file)

    def tearDown(self):
        sys.stdout = self.held


if __name__ == '__main__':
    unittest.main()
