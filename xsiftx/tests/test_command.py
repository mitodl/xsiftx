"""
Unit tests for xisftx command line interface
"""
import os
import sys
import unittest

from mock import patch

from .util import nostderr, mkdtemp_clean
from xsiftx.command_line import execute
from xsiftx.util import XsiftxException, get_course_list


class TestCommandLine(unittest.TestCase):
    """
    Test options of command line
    """
    # pylint: disable=R0904

    EDX_ROOT = '/edx/app/edxapp/edx-platform'
    EDX_VENV = '/edx/app/edxapp/venvs/edxapp'

    def test_args(self):
        """
        Test all the argument variations available
        """
        with nostderr():

            # Test no arguments
            with self.assertRaises(SystemExit) as exception_context:
                execute()
            exit_exception = exception_context.exception
            self.assertEqual(exit_exception.code, 2)

            # Test no venv or edx-platform (use defaults), expecting
            # invalid sifter
            with self.assertRaises(SystemExit) as exception_context:
                sys.argv = ['xsiftx', 'sifter', ]
                execute()
            exit_exception = exception_context.exception
            self.assertEqual(exit_exception.code, -1)

            # Invalid venv, good edx-platform - expect invalid sifter
            with self.assertRaises(SystemExit) as exception_context:
                sys.argv = ['xsiftx', '-v', 'sfutt', 'sifter', ]
                execute()
            exit_exception = exception_context.exception
            self.assertEqual(exit_exception.code, -1)

            # Invalid edx-platform, valid venv - expect invalid
            with self.assertRaises(SystemExit) as exception_context:
                sys.argv = ['xsiftx', '-e', 'sfutt', 'sifter', ]
                execute()
            exit_exception = exception_context.exception
            self.assertEqual(exit_exception.code, -1)

    def test_bad_sifter(self):
        """
        Test exit code on non-existent sifter
        """
        with nostderr():
            with self.assertRaises(SystemExit) as exception_context:
                sys.argv = [
                    'xsiftx',
                    '-v', 'blah',
                    '-e', 'stuff',
                    'dontexist',
                ]
                execute()
            exit_exception = exception_context.exception
            self.assertEqual(exit_exception.code, -1)

    def test_bad_course_bad_env(self):
        """
        Test bad course
        """
        with self.assertRaisesRegexp(XsiftxException,
                                     'No such file or dir.*'):
            sys.argv = ['xsiftx',
                        '-v', 'blah',
                        '-e', 'stuff',
                        '-c', 'course',
                        'test_sifters', ]
            execute()

    @unittest.skipUnless(os.environ.get('XSIFTX_TEST_EDX', None),
                         'Requires an edx environment and XSIFTX_TEST_EDX '
                         'environment variable set.')
    def test_bad_course_good_env(self):
        """
        With proper parameters, test an invalid course
        """
        with nostderr():
            with self.assertRaises(SystemExit) as exception_context:
                sys.argv = ['xsiftx',
                            '-v', self.EDX_VENV,
                            '-e', self.EDX_ROOT,
                            '-c', 'not_a_course',
                            'test_sifters', ]
                execute()
            exit_exception = exception_context.exception
            self.assertEqual(exit_exception.code, -2)

    @unittest.skipUnless(os.environ.get('XSIFTX_TEST_EDX', None),
                         'Requires an edx environment and XSIFTX_TEST_EDX '
                         'environment variable set.')
    def test_specified_course(self):
        """
        With proper parameters, test specific course
        """
        temp_dir = mkdtemp_clean(self)
        with patch('xsiftx.util.get_settings') as mock_settings:
            mock_settings.return_value = {
                'use_s3': False,
                'aws_key': '',
                'root_path': temp_dir,
                'bucket': '',
                'aws_key_id': ''
            }
            sys.argv = ['xsiftx',
                        '-v', self.EDX_VENV,
                        '-e', self.EDX_ROOT,
                        '-c', get_course_list(self.EDX_VENV, self.EDX_ROOT)[0],
                        'test_sifters', ]
            execute()
            self.assertTrue(mock_settings.called)

    @unittest.skipUnless(os.environ.get('XSIFTX_TEST_EDX', None),
                         'Requires an edx environment and XSIFTX_TEST_EDX '
                         'environment variable set.')
    def test_valid_sifter_run(self):
        """
        Mock the location of the settings, but run valid sifter
        """
        temp_dir = mkdtemp_clean(self)
        with patch('xsiftx.util.get_settings') as mock_settings:
            mock_settings.return_value = {
                'use_s3': False,
                'aws_key': '',
                'root_path': temp_dir,
                'bucket': '',
                'aws_key_id': ''
            }
            sys.argv = ['xsiftx',
                        '-v', self.EDX_VENV,
                        '-e', self.EDX_ROOT,
                        'test_sifters', ]
            execute()
            self.assertTrue(mock_settings.called)
