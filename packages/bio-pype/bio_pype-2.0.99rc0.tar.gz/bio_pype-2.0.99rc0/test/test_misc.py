import os
import sys
import unittest
from io import StringIO

from pype import argparse, misc, modules


class TestMisc(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, StringIO()
        self.parser = argparse.ArgumentParser(prog="pype", description="Test")
        self.subparsers = self.parser.add_subparsers(dest="modules")

    def test_generate_uid(self):
        n = 10000
        uid_list = [misc.generate_uid() for rnd in range(n)]
        self.assertEqual(len(set(uid_list)), n)

    def test_package_modules(self):
        mods = misc.package_modules(modules)
        self.assertEqual(len(mods), 7)
        self.assertEqual(type(mods), set)
        self.assertTrue("pype.modules.snippets" in mods)

    def test_package_files(self):
        files = misc.package_files(modules, ".py")
        self.assertEqual(len(files), 8)
        self.assertEqual(type(files), set)
        init_file = "%s/pype/modules/__init__.py" % os.getcwd()
        self.assertTrue(init_file in files)

    # def test_get_modules(self):
    #     mods = misc.get_modules(modules, self.subparsers, {})
    #     a = 'Unit'
    #     b = 'Test'
    #     mods['snippets'](self.subparsers, None, [
    #         '--log', 'test/data/tmp', 'hello',
    #         '-w', b, '-o', '-'], 'test_path')
    #     self.assertEqual(sys.stdout.getvalue(), '%s \n' % a.upper())

    def test_get_modules_names(self):
        names = misc.get_modules_names(modules)
        self.assertEqual(len(names), 7)
        self.assertEqual(type(names), list)
        self.assertTrue("profiles" in names)
        self.assertTrue("snippets" in names)
        self.assertTrue("pipelines" in names)

    def test_get_modules_method(self):
        method = misc.get_module_method(modules, "snippets", "random")
        self.assertFalse(callable(method))
        self.assertTrue(method is None)
        method = misc.get_module_method(modules, "snippets", "add_parser")
        self.assertTrue(callable(method))

    def tearDown(self):
        sys.stdout = self.held


if __name__ == "__main__":
    unittest.main()
