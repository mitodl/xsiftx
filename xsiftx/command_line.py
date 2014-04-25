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
import os
import StringIO
import subprocess
import sys
import tempfile

import xsiftx.sifters
import xsiftx.store
from xsiftx.util import get_sifters, get_course_list, get_settings


def execute():
    """
    Begin command processing
    """
    sifter_dict = get_sifters()
    parser = argparse.ArgumentParser(
        prog='xsiftx.py',
        formatter_class=argparse.RawTextHelpFormatter,
        description=(
            'Run a sifter against one or all courses.\n'
            'Current available sifters:\n{0}'.format(
                '\n'.join(sifter_dict.keys())
            )
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

    if args.sifter not in sifter_dict.keys():
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

    settings = get_settings(args.edx_platform)

    # Everything is all setup, now run the sifter and write the output
    # to the grade download location.

    data_store = None
    if settings['use_s3']:
        data_store = xsiftx.store.S3Store(settings)
    else:
        data_store = xsiftx.store.FSStore(settings)

    exit_val = 0
    courses_to_run = []
    if args.course:
        courses_to_run = [args.course, ]
    else:
        courses_to_run = courses
    for course in courses_to_run:
        with tempfile.NamedTemporaryFile() as tmpfile:
            with tempfile.NamedTemporaryFile() as stderr_tmp:
                cmd = [
                    sifter_dict[args.sifter],
                    args.venv,
                    args.edx_platform,
                    course,
                    ]
                cmd.extend(args.extra_args)
                sift = subprocess.Popen(cmd, stdout=tmpfile, stderr=stderr_tmp,
                                        universal_newlines=True)
                ret_code = sift.wait()
                if ret_code != 0:
                    sys.stderr.write('Sifter {0} called with {1} failed '
                                     'with non zero exit code printing output '
                                     'and aborting\n'.format(args.sifter, cmd))
                    stderr_tmp.flush()
                    stderr_tmp.seek(0)
                    sys.stderr.write(stderr_tmp.read())
                    exit_val = 128
                    continue
                tmpfile.flush()
                tmpfile.seek(0)
                if os.fstat(tmpfile.fileno()).st_size > 0:
                    filename = tmpfile.readline()[:-1]
                    data_store.store(course, filename, tmpfile)

if __name__ == '__main__':
    execute()
