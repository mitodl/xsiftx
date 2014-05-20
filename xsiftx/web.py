"""
Flask application entry for xsiftx LTI
provider application.
"""
import logging
from flask import Flask

from xsiftx.config import settings
from xsiftx.lti import xsiftx_lti


def set_log_level():
    """
    Setup the log level based on configuration, or leave as python default
    """
    # Setup logging from config if defined
    config_log_level = settings.get('log_level', None)
    config_log_int = None

    if config_log_level:
        config_log_int = getattr(logging, config_log_level.upper(), None)
        if not isinstance(config_log_int, int):
            raise ValueError('Invalid log level: {0}'.format(config_log_level))
        logging.basicConfig(level=config_log_int)
    return config_log_int


app = Flask('xsiftx')  # pylint: disable=C0103
app.config.update(**settings)  # pylint: disable=W0142

# Setup session from config
app.secret_key = settings.get('flask_secret_key', None)

set_log_level()

# Register blueprints
app.register_blueprint(xsiftx_lti)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.debug = True
    app.run(host='0.0.0.0')
