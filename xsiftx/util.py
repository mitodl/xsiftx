"""
Utility functions for xsiftx.
"""
import json
import os
import stat
import subprocess
import tempfile

import xsiftx.sifters
import xsiftx.store

ENV_JSON_FILENAME = 'lms.env.json'
AUTH_JSON_FILENAME = 'lms.auth.json'
VENV = ('edx_venv_path', '/edx/app/edxapp/venvs/edxapp')
EDX_PLATFORM = ('edx_platform_path', '/edx/app/edxapp/edx-platform')


class XsiftxException(Exception):
    """
    Customized exception class for handling
    xsiftx errors like missing edx_platform
    configuration
    """
    pass


class SifterException(Exception):
    """
    Customized exception raised for sifter errors
    """
    pass


def get_sifters():
    """
    Get list of currently installed sifters
    """

    sifter_dict = {}
    # List of paths to look for sifters, ordered
    # in reverse precedence (most important last)
    # to replace sifter dictionary
    sifter_paths = [
        os.path.dirname(xsiftx.sifters.__file__),  # Installed sifters
        os.path.join(os.path.expanduser('~'), 'sifters'),  # HOME_DIR sifters
        os.path.join(os.getcwd(), 'sifters'),  # cwd sifters
        os.environ.get('SIFTER_DIR', ''),  # Environment set sifters
    ]

    executable = stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
    for sifter_path in sifter_paths:
        if os.path.isdir(sifter_path):
            for filename in os.listdir(sifter_path):
                fullpath = os.path.join(sifter_path, filename)
                if os.path.isfile(fullpath):
                    fstat = os.stat(fullpath)
                    mode = fstat.st_mode
                    if mode & executable:
                        sifter_dict[filename] = fullpath

    return sifter_dict


def get_course_list(venv, edx_root):
    """
    Get a list of courses by using the management commands in edx.
    """

    # Grab course list
    course_raw = ''
    try:
        course_raw = subprocess.check_output(
            ['{0}/bin/python'.format(venv),
             'manage.py', 'lms', '--settings=aws',
             'dump_course_ids', ],
            cwd=edx_root, stderr=subprocess.PIPE
        )
    except OSError as ex:
        raise XsiftxException(
            'No such file or directory: {0!r}\n'.format(str(ex))
        )

    except subprocess.CalledProcessError as ex:
        raise XsiftxException(
            'Course listing failed, output was: {0!r}\n'.format(ex.output)
        )
    return course_raw.split('\n')[:-1]


def get_settings(edx_root):
    """
    This will pull out the json settings for the
    platform in order to get the bucket, path, key_id, and key
    for uploading to the right place and return them as a dict.
    """
    auth_path = os.path.abspath('{0}/../{1}'.format(
        edx_root, AUTH_JSON_FILENAME))
    if not os.path.isfile(auth_path):
        raise XsiftxException(
            'Cannot find lms authentication file: {0}. '
            'Is the path correct?'.format(auth_path)
        )
    with open(auth_path) as auth_file:
        auth_tokens = json.load(auth_file)

    env_path = os.path.abspath('{0}/../{1}'.format(
        edx_root, ENV_JSON_FILENAME))
    if not os.path.isfile(env_path):
        raise XsiftxException(
            'Cannot find lms environment file: {0}. '
            'Is the path correct?'.format(env_path)
        )
    with open(env_path) as env_file:
        env_tokens = json.load(env_file)

    use_s3 = True
    grades_download = env_tokens['GRADES_DOWNLOAD']
    if grades_download['STORAGE_TYPE'] != 'S3':
        use_s3 = False

    bucket = grades_download['BUCKET']
    root_path = grades_download['ROOT_PATH']

    aws_key_id = auth_tokens['AWS_ACCESS_KEY_ID']
    if aws_key_id == '' and use_s3:
        raise XsiftxException('No AWS_ACCESS_KEY_ID\n')

    aws_key = auth_tokens["AWS_SECRET_ACCESS_KEY"]
    if aws_key == '' and use_s3:
        raise XsiftxException('No AWS_SECRET_ACCESS_KEY\n')

    return dict(aws_key=aws_key, aws_key_id=aws_key_id,
                bucket=bucket, root_path=root_path, use_s3=use_s3)


def run_sifter(sifter, course, venv, edx_platform, extra_args):
    """
    This handles running the actual sifter given a course
    and sifter
    """
    settings = get_settings(edx_platform)
    data_store = None

    if settings['use_s3']:
        data_store = xsiftx.store.S3Store(settings)
    else:
        data_store = xsiftx.store.FSStore(settings)

    with tempfile.NamedTemporaryFile() as tmpfile:
        with tempfile.NamedTemporaryFile() as stderr_tmp:
            cmd = [
                sifter,
                venv,
                edx_platform,
                course,
            ]
            cmd.extend(extra_args)
            sift = subprocess.Popen(cmd, stdout=tmpfile, stderr=stderr_tmp,
                                    universal_newlines=True)
            ret_code = sift.wait()
            if ret_code != 0:
                stderr_tmp.flush()
                stderr_tmp.seek(0)
                error_output = stderr_tmp.read()
                raise SifterException(
                    'Sifter {0} called with {1} failed '
                    'with non zero exit code printing output '
                    'and aborting\nError Output:\n{2}'.format(
                        sifter, ' '.join(cmd), error_output
                    )
                )

            tmpfile.flush()
            tmpfile.seek(0)
            if os.fstat(tmpfile.fileno()).st_size > 0:
                filename = tmpfile.readline()[:-1]
                data_store.store(course, filename, tmpfile)
