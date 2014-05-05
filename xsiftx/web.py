"""
Flask application entry for xsiftx LTI
provider application.
"""
from flask import Flask

from xsiftx.config import settings
from xsiftx.lti import xsiftx_lti


app = Flask('xsiftx')  # pylint: disable=C0103
app.config.update(**settings)  # pylint: disable=W0142


# Setup session from config
app.secret_key = settings.get('flask_secret_key', None)

# Register blueprints
app.register_blueprint(xsiftx_lti)

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
