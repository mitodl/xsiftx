"""
Tests for xsiftx.util functions
"""
import os
import stat
import unittest

from mock import patch

from .util import mkdtemp_clean
from xsiftx.util import (
    get_sifters,
    get_course_list,
    get_settings,
    run_sifter,
    XsiftxException,
    SifterException
)


class TestUtils(unittest.TestCase):
    """
    Test series for util functions in xsiftx.util
    """
    # pylint: disable=r0904

    KNOWN_SIFTERS = [
        'copy_file',
        'xqanalyze',
        'content_statistics',
        'test_sifters',
        'dump_grades',
    ]

    EDX_ROOT = '/edx/app/edxapp/edx-platform'
    EDX_VENV = '/edx/app/edxapp/venvs/edxapp'

    BAD_SIFTER = 'testenv_sifter'

    def _make_bad_sifter(self):
        """
        Create a sifter that raises an exception
        """
        temp_dir = mkdtemp_clean(self)
        sifter_path = os.path.join(temp_dir, self.BAD_SIFTER)
        with open(sifter_path, 'w+') as temp_sifter:
            temp_sifter.write('#!/bin/bash\nfalse')
        perms = os.stat(sifter_path)
        os.chmod(sifter_path, perms.st_mode | stat.S_IEXEC)
        os.environ['SIFTER_DIR'] = temp_dir

    def test_sifter_list_locations(self):
        """
        Make sure sifter search paths work
        """
        # check default sifters
        self.assertTrue(set(self.KNOWN_SIFTERS).issubset(get_sifters()))

        # Add environment variable of extra sifter folder, ensure it is added
        # to list
        self._make_bad_sifter()
        self.assertTrue(self.BAD_SIFTER in get_sifters())

    @unittest.skipUnless(os.environ.get('XSIFTX_TEST_EDX', None),
                         'Requires an edx environment and XSIFTX_TEST_EDX '
                         'environment variable set.')
    def test_course_list(self):
        """
        Make sure we can get a course list.
        Requires that we have an edx-platform environment at default
        coords
        """
        with self.assertRaisesRegexp(XsiftxException,
                                     'No such file or dir.*'):
            get_course_list('nope', 'nope')

        self.assertTrue(len(get_course_list(self.EDX_VENV, self.EDX_ROOT)) > 0)

    @unittest.skipUnless(os.environ.get('XSIFTX_TEST_EDX', None),
                         'Requires an edx environment and XSIFTX_TEST_EDX '
                         'environment variable set.')
    def test_get_settings(self):
        """
        Test that we can get settings and fail nicely without them
        """
        settings_keys = [
            'use_s3',
            'aws_key',
            'root_path',
            'bucket',
            'aws_key_id',
        ]
        with self.assertRaisesRegexp(XsiftxException,
                                     'Cannot find lms.*'):
            get_settings('nope')
        settings = get_settings(self.EDX_ROOT)
        self.assertEqual(settings_keys, settings.keys())
        self.assertIsNotNone(settings.get('root_path'))
        self.assertIsNotNone(settings.get('bucket'))

    @unittest.skipUnless(os.environ.get('XSIFTX_TEST_EDX', None),
                         'Requires an edx environment and XSIFTX_TEST_EDX '
                         'environment variable set.')
    def test_run_sifter(self):
        """
        Run sifters to make sure the runner is working right
        """
        # Try with bad root
        with self.assertRaisesRegexp(XsiftxException,
                                     'Cannot find lms*'):
            run_sifter('nope', 'nope', 'nope', 'nope', 'nope')

        # Mock out settings so we know where output is going
        bucket = 'reports'
        course = 'stuff'
        temp_dir = mkdtemp_clean(self)

        with patch('xsiftx.util.get_settings') as mock_settings:
            mock_settings.return_value = {
                'use_s3': False,
                'aws_key': '',
                'root_path': temp_dir,
                'bucket': bucket,
                'aws_key_id': ''
            }
            # Test that a bad sifter raises
            with self.assertRaisesRegexp(SifterException,
                                         'Sifter .+ called with'):
                self._make_bad_sifter()
                run_sifter(get_sifters()[self.BAD_SIFTER],
                           course, self.EDX_VENV, self.EDX_ROOT, [])

            # Test that a good sifter creates the expected file
            run_sifter(get_sifters()['test_sifters'],
                       course, self.EDX_VENV, self.EDX_ROOT, [])
            self.assertTrue(mock_settings.called)
            self.assertTrue(os.path.exists(
                os.path.join(temp_dir, course, 'test_sifter.txt')
            ))
