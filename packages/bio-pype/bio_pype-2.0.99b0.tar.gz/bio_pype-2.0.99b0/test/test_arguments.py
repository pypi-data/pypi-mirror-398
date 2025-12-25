import unittest
from pype.utils.arguments import PipelineItemArguments


class TestArguments(unittest.TestCase):

    def test_simple_arguments(self):
        args = PipelineItemArguments()
        arguments = [
            {'prefix': '-i', 'pipeline_arg': '%(input)s'},
            {'prefix': '-o', 'pipeline_arg': '%(output)s'}]
        for argument in arguments:
            args.add_argument(argument)
        dict_args = args.to_dict()
        dict_values = args.to_dict(
            {'input': 'my_input.txt', 'output': 'my_output.txt'})
        self.assertDictEqual(
            dict_args, {'-i': '%(input)s', '-o': '%(output)s'})
        self.assertDictEqual(
            dict_values, {'-i': 'my_input.txt', '-o': 'my_output.txt'})


if __name__ == '__main__':
    unittest.main()
