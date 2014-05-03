"""
Flask application entry for xsiftx LTI
provider application.
"""
from flask import Flask

from lti import xsiftx_lti, celery

from xsiftx.config import settings

app = Flask('xsiftx')
app.config.update(**settings)


# Setup session from config
app.secret_key = settings.get('flask_secret_key', None)

# Register blueprints
app.register_blueprint(xsiftx_lti)

if __name__ == "__main__":
    app
    app.debug = True
    app.run(host='0.0.0.0')
