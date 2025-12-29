##
# cSpell:word pype


import unittest
import sys
from pype import argparse
from pype.modules import profiles
from pype.utils.profiles import Profile, get_profiles
from io import StringIO


class TestProfiles(unittest.TestCase):

    def setUp(self):
        self.held, sys.stdout = sys.stdout, StringIO()
        self.parser = argparse.ArgumentParser(prog='pype', description='Test')
        self.subparsers = self.parser.add_subparsers(dest='modules')

    def test_get_profiles(self):
        profs = get_profiles({})
        self.assertEqual(profs['test_path'].info['description'], 'Test Profile')
        self.assertEqual(profs['test_path'].__name__, "test_path")
        self.assertTrue(isinstance(profs['test_path'], Profile))

    def test_profiles(self):
        profiles.profiles(self.subparsers, None, ['info', '-p', 'test_path'], None)
        self.assertEqual(sys.stdout.getvalue()[0:22], "Name       : test_path")

    def tearDown(self):
        sys.stdout = self.held


if __name__ == '__main__':
    unittest.main()
