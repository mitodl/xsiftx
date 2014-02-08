"""
xsiftx is a program to run scripts against edx-platform data for a
course or all courses and then writing that to the grade book s3
bucket to show up on the instructor dashboard.

The scripts can be anything that is executable and just need to output
the filename they want to use as the first line, and the file contents
as the rest.  ie:
student_report_20140207.csv
name,datum
johnsmith,things
.
.
.

The script is passed the virtualenv path, edx root path, course id, and any
extra arguments that were passed to sifter
"""

import argparse
import json
import os
import stat
import subprocess
import sys
import tempfile

import xsiftx.sifters
import xsiftx.store

ENV_JSON_FILENAME = 'lms.env.json'
AUTH_JSON_FILENAME = 'lms.auth.json'

def get_sifters():
    """
    Get list of currently installed sifters
    """

    sifter_list = []
    sifter_path = os.path.dirname(xsiftx.sifters.__file__)
    executable = stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
    for filename in os.listdir(sifter_path):
        fullpath = os.path.join(sifter_path, filename)
        if os.path.isfile(fullpath):
            st = os.stat(fullpath)
            mode = st.st_mode
            if mode & executable:
                sifter_list.append(filename)

    return sifter_list

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
            cwd=edx_root
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

def get_settings(venv, edx_root):
    """
    This will pull out the json settings for the
    platform in order to get the bucket, path, key_id, and key
    for uploading to the right place and return them as a dict.
    """
    with open(os.path.abspath('{0}/../{1}'.format(edx_root, AUTH_JSON_FILENAME))) as auth_file:
        auth_tokens = json.load(auth_file)

    with open(os.path.abspath('{0}/../{1}'.format(edx_root, ENV_JSON_FILENAME))) as env_file:
        env_tokens = json.load(env_file)

    settings = {}
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

def execute():
    """
    Begin command processing
    """
    sifter_list = get_sifters()
    parser = argparse.ArgumentParser(
        prog='xsiftx.py',
        formatter_class=argparse.RawTextHelpFormatter,
        description=('Run a sifter against one or all courses.\n'
                     'Current available sifters:\n{0}'.format(
                         '\n'.join(sifter_list))
                 )
    )
    parser.add_argument('sifter',
                        help='script in sifter library to run')
    parser.add_argument('-c', '--course', type=str,
                        help='Course ID e.g. org/number/term')
    parser.add_argument('-v', '--venv', type=str, required=True,
                        help='Virtualenv root path for edx-platform')
    parser.add_argument('-e', '--edx-platform', type=str, required=True,
                        help='Root path to edx-platform')

    # Grab any extra arguments passed in
    parser.add_argument('extra_args', nargs=argparse.REMAINDER)

    args = parser.parse_args()

    if args.sifter not in sifter_list:
        sys.stderr.write("You have specified a sifter that doesn't exist\n")
        sys.exit(-1)

    courses = get_course_list(args.venv, args.edx_platform)
    # If course specified, make sure the edx platform has that class
    if args.course:
        if args.course not in courses:
            sys.stderr.write(
                "Course doesn't exist, please pick from:\n{0}\n".format(
                    '\n'.join(courses)
                )
            )
            sys.exit(-1)

    settings = get_settings(args.venv, args.edx_platform)

    # Everything is all setup, now run the sifter and write the output to the grade
    # download location.
    sifter_path = '{0}/{1}'.format(os.path.dirname(xsiftx.sifters.__file__),
                                   args.sifter)
    data_store = None
    if settings['use_s3']:
        data_store = xsiftx.store.S3Store(settings)
    else:
        data_store = xsiftx.store.FSStore(settings)

    courses_to_run = []
    if args.course:
        courses_to_run = [args.course, ]
    else:
        courses_to_run = courses
    for course in courses_to_run:
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            cmd = [ sifter_path, args.venv, args.edx_platform, course, ]
            cmd.extend(args.extra_args)
            sift = subprocess.Popen(cmd, stdout=tmpfile, universal_newlines=True)
            ret_code = sift.wait()
            if ret_code != 0:
                sys.stderr.write('Sifter failed with non zero exit code, aborting\n')
                sys.exit(-3)
            tmpfile.flush()
            tmpfile.seek(0)
            filename = tmpfile.readline()[:-1]
            data_store.store(course, filename, tmpfile)
    
if __name__ == '__main__':
    execute()
