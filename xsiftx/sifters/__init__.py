"""
Place whatever executable you like in here and it will be
added to the list of sifters for use in the command.

The expectations of sifters are that the first line output
is the filename to use, and everything else on stdout is
the file to upload to the dashboard.

You can write to stderr without consequence if neccessary,
and returning anything but 0 will cause the upload to be
aborted. Command is run with the following arguments:
<sifter> edx_venv_path edx_platform_path course_id [extra_arg, extra_arg,....]
"""
