"""
Utility functions for xsiftx.
"""
import json
import os
import stat
import subprocess
import sys

import xsiftx.sifters

ENV_JSON_FILENAME = 'lms.env.json'
AUTH_JSON_FILENAME = 'lms.auth.json'


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
    try:
        course_raw = subprocess.check_output(
            ['{0}/bin/python'.format(venv),
             'manage.py', 'lms', '--settings=aws',
             'dump_course_ids', ],
            cwd=edx_root, stderr=subprocess.PIPE
        )
    except OSError as ex:
        sys.stderr.write(
            'No such file or directory: {0!r}\n'.format(str(ex))
        )
        sys.exit(-1)

    except subprocess.CalledProcessError as ex:
        sys.stderr.write(
            'Course listing failed, output was: {0!r}\n'.format(ex.output)
        )
        sys.exit(-1)
    return course_raw.split('\n')[:-1]


def get_settings(edx_root):
    """
    This will pull out the json settings for the
    platform in order to get the bucket, path, key_id, and key
    for uploading to the right place and return them as a dict.
    """
    with open(os.path.abspath('{0}/../{1}'.format(
                edx_root, AUTH_JSON_FILENAME))) as auth_file:
        auth_tokens = json.load(auth_file)

    with open(os.path.abspath('{0}/../{1}'.format(
                edx_root, ENV_JSON_FILENAME))) as env_file:
        env_tokens = json.load(env_file)

    use_s3 = True
    grades_download = env_tokens['GRADES_DOWNLOAD']
    if grades_download['STORAGE_TYPE'] != 'S3':
        use_s3 = False

    bucket = grades_download['BUCKET']
    root_path = grades_download['ROOT_PATH']

    aws_key_id = auth_tokens['AWS_ACCESS_KEY_ID']
    if aws_key_id == '' and use_s3:
        sys.stderr.write('No AWS_ACCESS_KEY_ID\n')
        sys.exit(-2)

    aws_key = auth_tokens["AWS_SECRET_ACCESS_KEY"]
    if aws_key == '' and use_s3:
        sys.stderr.write('No AWS_SECRET_ACCESS_KEY\n')
        sys.exit(-2)

    return dict(aws_key=aws_key, aws_key_id=aws_key_id,
                bucket=bucket, root_path=root_path, use_s3=use_s3)
