"""
Decorators to handle LTI session management,
authentication, etc.
"""
# pylint: disable=C0103
from functools import wraps
import logging

from flask import request, session
import oauth.oauth as oauth

from .oauthstore import LTIOAuthDataStore
from .util import LTIException, LTIRoleException

log = logging.getLogger('xsiftx')

LTI_PROPERTY_LIST = [
    'oauth_consumer_key',
    'launch_presentation_return_url',
    'user_id',
    'oauth_nonce',
    'context_label',
    'context_id',
    'resource_link_title',
    'resource_link_id',
    'lis_person_contact_email_primary',
    'lis_person_contact_emailprimary',
    'lis_person_name_full',
    'lis_person_name_family',
    'lis_person_name_given',
    'lis_result_sourcedid',
    'launch_type',
    'lti_message',
    'lti_version',
    'roles',
]

LTI_STAFF_ROLES = ['Instructor', 'Administrator', ]

LTI_SESSION_KEY = 'lti_authenticated'


def lti_authentication(func):
    """
    This is a middleware to handle LTI session
    and authorization for a given view.
    """
    @wraps(func)
    def decorator(*args, **kwargs):
        """
        Actual wrapper to handle LTI/OAuth
        """
        # pylint: disable=W0212

        # Get lti GET or POST params as dict
        if request.method == 'POST':
            params = request.form.to_dict()
        else:
            params = request.args.to_dict()
        log.debug(params)

        # If we are already authenticated and not requesting oauth, return
        if (session.get(LTI_SESSION_KEY, False)
                and not params.get('oauth_consumer_key', None)):
            return func(*args, **kwargs)

        # Clear session to ensure authorization is happening fresh for
        # each lti instance.
        for prop in LTI_PROPERTY_LIST:
            if session.get(prop, None):
                del session[prop]

        # Try and authentication if session is being initiated
        oauth_server = oauth.OAuthServer(LTIOAuthDataStore())
        oauth_server.add_signature_method(
            oauth.OAuthSignatureMethod_PLAINTEXT())
        oauth_server.add_signature_method(
            oauth.OAuthSignatureMethod_HMAC_SHA1())

        # Check header for SSL before selecting the url
        url = request.url
        if request.headers.get('X-Forwarded-Proto', 'http') == 'https':
            url = request.url.replace('http', 'https', 1)

        oauth_request = oauth.OAuthRequest.from_request(
            request.method,
            url,
            headers=dict(request.headers),
            parameters=params
        )

        if not oauth_request:
            log.info('Received non oauth request on oauth protected page')
            raise LTIException('This page requires a valid oauth session '
                               'or request')
        try:
            consumer = oauth_server._get_consumer(oauth_request)
            oauth_server._check_signature(oauth_request, consumer, None)
        except oauth.OAuthError as err:
            # Rethrow our own for nice error handling (don't print
            # error message as it will contain the key
            log.info(err.message)
            raise LTIException("OAuth error: Please check your key and secret")

        # All good to go, store all of the LTI params into a
        # session dict for use in views
        for prop in LTI_PROPERTY_LIST:
            if params.get(prop, None):
                session[prop] = params[prop]

        # Set logged in session key
        session[LTI_SESSION_KEY] = True

        return func(*args, **kwargs)

    return decorator


def lti_staff_required(func):
    """
    Decorator to make sure that person is a
    member of one of the course staff roles
    before allowing them to the view. Requires that
    lti_authentication has occurred
    """
    @wraps(func)
    def decorator(*args, **kwargs):
        """
        Check session['role'] against known list of course staff
        roles and raise if it isn't in that set.
        """
        log.debug(session)
        role = session.get('roles', None)
        if not role:
            raise LTIRoleException(
                'User does not have a role. One is required'
            )
        if role not in LTI_STAFF_ROLES:
            raise LTIRoleException(
                'You are not in a staff level role. Access is restricted '
                'to course staff.'
            )
        return func(*args, **kwargs)

    return decorator
