"""
Classes to handle oauth portion of LTI
"""
# pylint: disable=C0103
import logging

import oauth.oauth as oauth

from xsiftx.config import settings, get_consumer

log = logging.getLogger('xsiftx')


class LTIOAuthDataStore(oauth.OAuthDataStore):
    """
    Largely taken from reference implementation
    for app engine at https://code.google.com/p/ims-dev/
    """

    def __init__(self):
        """
        Create OAuth store
        """
        oauth.OAuthDataStore.__init__(self)
        self.consumers = settings.get('consumers', None)

    def lookup_consumer(self, key):
        """
        Search through keys
        """
        if not self.consumers:
            log.critical(("No consumers defined in settings."
                          "Have you created a configuration file?"))
            return None

        consumer = get_consumer(key)
        if not consumer:
            log.info("Did not find consumer, using key: %s ", key)
            return None

        secret = consumer.get('secret', None)
        if not secret:
            log.critical(('Consumer %s, is missing secret'
                          'in settings file, and needs correction.'), key)
            return None
        return oauth.OAuthConsumer(key, secret)

    def lookup_token(self, oauth_consumer, token_type, token):
        """We don't do request_tokens"""
        # pylint: disable=W0613
        return oauth.OAuthToken(None, None)  # pragma: no cover

    def lookup_nonce(self, oauth_consumer, oauth_token, nonce):
        """Trust all nonces"""
        return None  # pragma: no cover

    def fetch_request_token(self, oauth_consumer, oauth_callback):
        """We don't do request_tokens"""
        return None  # pragma: no cover

    def fetch_access_token(self, oauth_consumer, oauth_token, oauth_verifier):
        """We don't do request_tokens"""
        return None  # pragma: no cover

    def authorize_request_token(self, oauth_token, user):
        """We don't do request_tokens"""
        return None  # pragma: no cover
