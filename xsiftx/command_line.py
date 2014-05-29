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
import sys

from xsiftx.util import VENV, EDX_PLATFORM
from xsiftx.util import (
    get_sifters,
    get_course_list,
    run_sifter,
    SifterException
)


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
    parser.add_argument('-v', '--venv', type=str, default=VENV[1],
                        help='Virtualenv root path for edx-platform')
    parser.add_argument('-e', '--edx-platform', type=str,
                        default=EDX_PLATFORM[1],
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
            sys.exit(-2)

    # Everything is all setup, now run the sifter and write the output
    # to the grade download location.
    courses_to_run = []
    if args.course:
        courses_to_run = [args.course, ]
    else:
        courses_to_run = courses
    for course in courses_to_run:
        try:
            run_sifter(
                sifter_dict[args.sifter],
                course,
                args.venv,
                args.edx_platform,
                args.extra_args
            )
        except SifterException, error:
            sys.stderr.write(unicode(error))

if __name__ == '__main__':
    execute()
