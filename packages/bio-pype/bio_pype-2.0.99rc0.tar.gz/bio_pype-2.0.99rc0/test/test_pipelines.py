##
# cSpell:word pype, compl, fasta

import unittest
import sys
from pype import argparse
from pype.utils.pipeline import get_pipelines
from pype.modules.pipelines import pipelines
from io import StringIO


class TestPipelines(unittest.TestCase):

    def setUp(self):
        self.held, sys.stdout = sys.stdout, StringIO()
        self.parser = argparse.ArgumentParser(prog='pype', description='Test')
        self.subparsers = self.parser.add_subparsers(dest='modules')

    def test_get_pipelines(self):
        pip_dict = get_pipelines(self.subparsers, {})
        self.assertEqual(type(pip_dict), dict)
        self.assertEqual(
            pip_dict['rev_compl_low_fa'].info['description'],
            'Reverse Complement Lower case a fasta')

    def test_pipelines(self):
        input_fa = 'test/data/files/input.fa'
        rev_fa = 'test/data/tmp/rev.fa'
        compl_fa = 'test/data/tmp/rev_comp.fa'
        out_fa = 'test/data/tmp/rev_comp_low.fa'
        pipelines(self.subparsers, None, [
                  '--queue', 'none', '--log', 'test/data/tmp',
                  'rev_compl_low_fa', '--input_fa', input_fa,
                  '--reverse_fa', rev_fa, '--complement_fa',
                  compl_fa, '--output', out_fa], 'test_path')
        with open(input_fa, 'rt') as orig_fa, open(
            rev_fa, 'rt') as orig_rev_fa, open(
                compl_fa, 'rt') as orig_rev_compl_fa, open(
                    out_fa, 'rt') as orig_rev_compl_low_fa:
            orig_entries = []
            rev_entries = []
            compl_entries = []
            low_entries = []
            for line in orig_fa:
                if line.startswith('>'):
                    orig_entries.append(line.rstrip())
            for line in orig_rev_fa:
                if line.startswith('>'):
                    rev_entries.append(line.rstrip())
            for line in orig_rev_compl_fa:
                if line.startswith('>'):
                    compl_entries.append(line.rstrip())
            for line in orig_rev_compl_low_fa:
                if line.startswith('>'):
                    low_entries.append(line.rstrip())
        self.assertEqual("%s reverse" % orig_entries[0], rev_entries[0])
        self.assertEqual("%s reverse complement" %
                         orig_entries[1], compl_entries[1])
        self.assertEqual("%s reverse complement lowered" %
                         orig_entries[0], low_entries[0])

    def test_pipelines210(self):
        input_fa = 'test/data/files/input.fa'
        rev_fa = 'test/data/tmp/rev210.fa'
        compl_fa = 'test/data/tmp/rev_comp210.fa'
        out_fa = 'test/data/tmp/rev_comp_low210.fa'
        pipelines(self.subparsers, None, [
                  '--queue', 'none', '--log', 'test/data/tmp',
                  'rev_compl_low_fa_210', '--input_fa', input_fa,
                  '--reverse_fa', rev_fa, '--complement_fa',
                  compl_fa, '--output', out_fa], 'test_path')
        with open(input_fa, 'rt') as orig_fa, open(
            rev_fa, 'rt') as orig_rev_fa, open(
                compl_fa, 'rt') as orig_rev_compl_fa, open(
                    out_fa, 'rt') as orig_rev_compl_low_fa:
            orig_entries = []
            rev_entries = []
            compl_entries = []
            low_entries = []
            for line in orig_fa:
                if line.startswith('>'):
                    orig_entries.append(line.rstrip())
            for line in orig_rev_fa:
                if line.startswith('>'):
                    rev_entries.append(line.rstrip())
            for line in orig_rev_compl_fa:
                if line.startswith('>'):
                    compl_entries.append(line.rstrip())
            for line in orig_rev_compl_low_fa:
                if line.startswith('>'):
                    low_entries.append(line.rstrip())
        self.assertEqual("%s reverse" % orig_entries[0], rev_entries[0])
        self.assertEqual("%s reverse complement" %
                         orig_entries[1], compl_entries[1])
        self.assertEqual("%s reverse complement lowered" %
                         orig_entries[0], low_entries[0])

    # def test_parallel_pipelines(self):
    #     input_fa = 'test/data/files/input.fa'
    #     rev_fa = 'test/data/tmp/rev_par.fa'
    #     compl_fa = 'test/data/tmp/rev_comp_par.fa'
    #     out_fa = 'test/data/tmp/rev_comp_low_par.fa'
    #     pipelines(self.subparsers, None, [
    #               '--queue', 'parallel', '--log', 'test/data/tmp',
    #               'rev_compl_low_fa', '--input_fa', input_fa,
    #               '--reverse_fa', rev_fa, '--complement_fa',
    #               compl_fa, '--output', out_fa], 'test_path')
    #     with open(input_fa, 'rt') as orig_fa, open(
    #         rev_fa, 'rt') as orig_rev_fa, open(
    #             compl_fa, 'rt') as orig_rev_compl_fa, open(
    #                 out_fa, 'rt') as orig_rev_compl_low_fa:
    #         orig_entries = []
    #         rev_entries = []
    #         compl_entries = []
    #         low_entries = []
    #         for line in orig_fa:
    #             if line.startswith('>'):
    #                 orig_entries.append(line.rstrip())
    #         for line in orig_rev_fa:
    #             if line.startswith('>'):
    #                 rev_entries.append(line.rstrip())
    #         for line in orig_rev_compl_fa:
    #             if line.startswith('>'):
    #                 compl_entries.append(line.rstrip())
    #         for line in orig_rev_compl_low_fa:
    #             if line.startswith('>'):
    #                 low_entries.append(line.rstrip())
    #     self.assertEqual("%s reverse" % orig_entries[0], rev_entries[0])
    #     self.assertEqual("%s reverse complement" %
    #                      orig_entries[1], compl_entries[1])
    #     self.assertEqual("%s reverse complement lowered" %
    #                      orig_entries[0], low_entries[0])

    def tearDown(self):
        sys.stdout = self.held


if __name__ == '__main__':
    unittest.main()
