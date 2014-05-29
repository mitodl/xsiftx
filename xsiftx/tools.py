"""
Tools for use by sifters to assist in setting up
the django environment, output files, etc.
"""

import os
import sys


def use_edx_venv(venv_path):
    """
    For use by a script wanting to use the edx environment.
    It will activate that environment within the script.
    """
    activator = '{0}/bin/activate_this.py'.format(venv_path)
    execfile(activator, dict(__file__=activator))


def enter_lms(venv_path, edx_path):
    """
    This will activate the edx virtual environment, and
    setup the environment as though the script was included
    in the lms project.
    """
    # pylint: disable=F0401
    use_edx_venv(venv_path)
    sys.path.append(edx_path)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'lms.envs.aws'
    os.environ['SERVICE_VARIANT'] = 'lms'
    import lms.startup as startup
    startup.run()
