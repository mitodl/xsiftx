"""
Utility support functions
"""
from xsiftx.util import get_sifters


class LTIException(Exception):
    """
    Custom LTI exception for proper handling
    of LTI specific errors
    """
    pass


class LTIRoleException(Exception):
    """
    Exception class for when LTI user doesn't have the
    right role.
    """
    pass


class InvalidAPIUsage(Exception):
    """
    API Error handler to return helpful json when problems occur.
    Stolen right from the flask docs
    """
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        """
        Setup class with optional arguments for returning later
        """
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """
        Aggregate properties into dictionary for use
        in returning jsonified errors.
        """
        exception_dict = dict(self.payload or ())
        exception_dict['message'] = self.message
        return exception_dict


def get_allowed_sifters(consumer, as_dict=False):
    """
    Returns a list of sifter names allowed by the client
    """
    all_sifters = get_sifters()
    sifters = {}
    allowed_sifters = consumer.get('allowed_sifters', None)
    if allowed_sifters:
        for sifter in all_sifters.keys():
            if sifter in allowed_sifters:
                sifters[sifter] = all_sifters[sifter]
    else:
        sifters = all_sifters
    if not as_dict:
        return sifters.keys()
    else:
        return sifters
