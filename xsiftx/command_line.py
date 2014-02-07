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

The script is passed the virtualenv path, edx root path, and any
extra arguments that were passed to sifter
"""

import argparse
import os
import stat
import subprocess
import sys

import xsiftx.sifters

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
    return course_raw.split('\n')

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

    print(args.course)
    print(args.venv)
    print(args.edx_platform)
    
if __name__ == '__main__':
    execute()
