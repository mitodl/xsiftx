"""
This handles getting the application configuration such
as the OAuth key list and what sifters are authorized
for what key.

This uses yaml as the configuration format and tries to load the
configuration from $(pwd)/xsiftx.yml then ~/.xsiftx.yml, and
then /etc/xsiftx.yml using the first one it finds. It can also
be specified with the environment variable XSIFTX_CONFIG set to a
path.

The format is:

edx_venv_path: "/edx/app/edxapp/venvs/edxapp"
edx_platform_path: "/edx/app/edxapp/edx-platform"
consumers:
  - key: <lti_app_identifier. e.g MITx-6.00x>
    secret: <oath_secret>
    allowed_sifters:
      - dump_grades
      - ...

if sifter list is empty or unspecified, all sifters are allowed. It
also requires a server secret in order to use secure client cookies to
store session information as flask_secret_key: <long crypto secret>
"""
import os
import yaml

from xsiftx.util import VENV, EDX_PLATFORM

CONFIG_PATHS = [
    os.path.join(os.getcwd(), 'xsiftx.yml'),
    os.path.join(os.path.expanduser('~'), '.xsiftx.yml'),
    '/etc/xsiftx.yml',
]


class XsiftxNoConfigException(Exception):
    """
    Customized exception for when the configuration doesn't exist
    """
    pass


def get_consumer(key):
    """
    Returns the consumer object based on key
    """
    consumers = settings.get('consumers', None)
    consumer = next(
        (consumer for consumer in consumers
         if consumer.get("key", None) == key),
        None
    )
    return consumer


def get_config():
    """
    Find config file and load or return None
    """
    conf = None
    config_file = None

    var_conf = os.environ.get('XSIFTX_CONFIG', None)
    if var_conf:
        config_file = var_conf
    else:
        for conf_path in CONFIG_PATHS:
            if os.path.isfile(conf_path):
                config_file = conf_path
                break

    if config_file:
        with open(config_file) as conf_yaml:
            conf = yaml.load(conf_yaml)

    if not conf:
        raise XsiftxNoConfigException('No configuration found')

    # Add some defaults for common settings if they aren't there
    if not conf.get(VENV[0], None):
        conf[VENV[0]] = VENV[1]

    if not conf.get(EDX_PLATFORM[0], None):
        conf[EDX_PLATFORM[0]] = EDX_PLATFORM[1]

    return conf

settings = get_config()  # pylint: disable=C0103
