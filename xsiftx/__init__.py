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

The script is passed along the course, venv and path to the edx platform
as the first three arguments.  All other arguments passed to xsiftx.py are
passed along as is.
"""

VERSION = "0.5.1"
