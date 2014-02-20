xsiftx
======

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

Sample usage to use the copy file sifter would something like:
`xsiftx -v /edx/app/edxapp/venvs/edxapp -e /edx/app/edxapp/edx-platform copy_file ~/test.jpg`
This would copy the test.jpg to every course available on the local LMS.

## Writing sifters ##

Place whatever executable you like in the sifters folder in the repository and it will be
added to the list of sifters for use in the command.

The expectations of sifters are that the first line output
is the filename to use, and everything else on stdout is
the file to upload to the dashboard.

You can write to stderr without consequence if neccessary,
and returning anything but 0 will cause the upload to be
aborted. Command is run with the following arguments:
<sifter> edx_venv_path edx_platform_path course_id [extra_arg, extra_arg,....]

If you choose to write a sifter in python, there is a convenience function for
loading into the edx-platform virtual environment and assuming the django settings
inside the LMS.  For examples that use this take a look at the content_statisics or
future_grade_dump sifters.  The notable lines are:
```python
from xsiftx.tools import enter_lms
enter_lms(sys.argv[1], sys.argv[2])
```

As you can see, this basically allows you to write a django management command as
though it were inside the platform without having to incoporate it directly into the
code base.
