<!-- markdown-extras: code-friendly, footnotes, fenced-code-blocks -->
xsiftx
======
[![Build Status](http://img.shields.io/travis/mitocw/xsiftx.svg?style=flat)](https://travis-ci.org/mitocw/xsiftx)
[![Coverage Status](https://coveralls.io/repos/mitocw/xsiftx/badge.png?branch=master)](https://coveralls.io/r/mitocw/xsiftx)
[![PyPi Downloads](http://img.shields.io/pypi/dm/xsiftx.svg?style=flat)](https://pypi.python.org/pypi/xsiftx)
[![PyPi Version](http://img.shields.io/pypi/v/xsiftx.svg?style=flat)](https://pypi.python.org/pypi/xsiftx)

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

Place whatever executable you like in the sifters folder in the
repository and it will be added to the list of sifters for use in the
command.

The expectations of sifters are that the first line output is the
filename to use, and everything else on stdout is the file to upload
to the dashboard.

You can write to stderr without consequence if neccessary, and
returning anything but 0 will cause the upload to be aborted. Command
is run with the following arguments: `<sifter> edx_venv_path
edx_platform_path course_id [extra_arg, extra_arg,....]`

If you choose to write a sifter in python, there is a convenience
function for loading into the edx-platform virtual environment and
assuming the django settings inside the LMS.  For examples that use
this take a look at the content_statisics or future_grade_dump
sifters.  The notable lines are:

```python
from xsiftx.tools import enter_lms
enter_lms(sys.argv[1], sys.argv[2])
```

As you can see, this basically allows you to write a django management command as
though it were inside the platform without having to incoporate it directly into the
code base.

This does require that GRADE_DOWNLOADS are turned on in your
edx-platform install to show up. Sample settings for lms.env.json
would look like:

```javascript
    "GRADES_DOWNLOAD": {
        "BUCKET": "my-sample-bucket", 
        "ROOT_PATH": "term/grades", 
        "STORAGE_TYPE": "S3"
    },
```

with the following FEATURE flags set in that same file:

```javascript
"ALLOW_COURSE_STAFF_GRADE_DOWNLOADS": true, 
"ENABLE_S3_GRADE_DOWNLOADS": true,
```

## LTI Web Interface ##

There is now an LTI Web interface and service inside xsiftx for
allowing course staff to run their own sifters on demand via a course
component.  It is quite simple to setup, and adds a lot of
flexibility.  The application offers fine grained access control to
limit what sifters can be run by which users with a simple yaml based
configuration file.  It also uses celery to asynchronously manage jobs
and the number of jobs that can be running at any given time.

To setup, create a configuration file at /etc/xsiftx.yml (or
~/.xsiftx.yml) and something similar to:

```yaml
# LTI Test config
# The path to edx platform, defaults are shown below and if you have the same
# paths, they don't need to be specified
edx_venv_path: "/edx/app/edxapp/venvs/edxapp"
edx_platform_path: "/edx/app/edxapp/edx-platform"
flask_secret_key: "some_crazy_long_randomized_string_for_securing_client_cookies"
# What celery backend to use, redis is probably simplest,
# but rabbit works just as well
CELERY_BROKER_URL: "redis://"
CELERY_RESULT_BACKEND: "redis://"
# Here we define ACLs.  The key and secret are needed by the course team
# to add the LTI component to their courseware. Instructions at:
# http://ca.readthedocs.org/en/latest/exercises_tools/lti_component.html
consumers:
  - key: "testing"
    secret: "super_secret"
      allowed_sifters:
        - 'test_sifters'
```

So the course staff (instructor, course staff, or global staff) will only
have access to run the "test_sifters" sifter with the above config.

To run the LTI application, use your favorite wsgi application server
with xsiftx.web:app. For uwsgi, that would be something like
`uwsgi --http :5000 -w xsiftx.web:app`, for gunicorn it would be:
`gunicorn xsiftx.web:app -b 0.0.0.0:5000`. You will also need to
start your celery worker to process jobs with something like:
`celery --app=xsiftx.lti worker -l info` and you should be good to
go.  For production, you will want to put these into some type of
startup file, and the application still needs to run on a system with
edx-platform installed and the user running the workers will need
access to the configuration files and code repository. You will likely
also want to specify the number of workers allowed to run.


## Sifters provided ##

Several sifters are provided in this repository:

- `dump_grades` -- dumps grades of all students to a CSV file.  The
  grades can both be the aggregated grades (as defined by the edX
  graders configuration) or raw grades (un-aggregated grades for
  individual problems).  Being able to dump raw grades can be very
  helpful to instructors who are debugging edX graders configurations.

- `content_statistics` -- dumps a CSV file with course content usage
  statistics, including, information about each module in the course,
  how many times it has been accessed, and now many times it has been
  attempted (for problems).

- `copy_file` -- Copies any arbitrary local file into the data
  download section

- `xqanalyze` -- Generates a zip file of CSVs where each CSV is a
  problem and each row in the CSV is a students response to that
  question.  Applies only to capa problems.

- `compute_grades` -- Doesn't generate a report but does calculate
  grades for a course and stores them in the SQL data store for use by
  legacy dashboard actions.

- `remote_grades` -- Posts a course's grades to a remote gradebook
  specified in the the course's XML and as defined by the edx-platform
  feature flag `REMOTE_GRADEBOOK_URL`.  It optionally takes an
  assignment name, but will post grades for every assignment if one
  isn't specified.
