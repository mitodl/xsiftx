"""
Test LTI web components of the application
"""
import json
import logging
import os
import time
import unittest

from mock import patch

import xsiftx.config
from xsiftx.config import get_config, get_consumer, XsiftxNoConfigException
from xsiftx.util import get_sifters
from xsiftx.lti.decorators import LTI_STAFF_ROLES
import xsiftx.web


class TestLTIWebApp(unittest.TestCase):
    """
    Test class for validating LTI interface
    to xsiftx.
    """
    # pylint: disable=e1103,r0904

    def setUp(self):
        """
        grab application test client
        """
        # pylint: disable=C0103
        self.client = xsiftx.web.app.test_client()
        self.settings = get_config()

    def _oauth_request(self, params={}, consumer_id=0):
        """
        Returns the data needed for an oauth request
        and adds those to the passed dictionary to
        keep out of the way.
        """
        # pylint: disable=w0102
        consumer = self.settings['consumers'][consumer_id]
        params.update({
            'oauth_consumer_key': consumer['key'],
            'oauth_signature_method': 'PLAINTEXT',
            'oauth_version': '1.0',
            'oauth_signature': '{0}&'.format(consumer.get('secret', '')),
            'oauth_timestamp': str(int(time.time())),
            'oauth_nonce': '123456789',
            'context_id': 'MITx/A.we/some'
        })
        return params

    def _run_sifter(self, sifter='test_sifters'):
        """
        Run a valid sifter and return json from response
        """
        test_url = 'api/v0.1/run'
        response = self.client.post(
            test_url,
            data=self._oauth_request({'sifter': sifter}, 1)
        )
        self.assertEqual(response.status_code, 200)
        return json.loads(response.data)

    def test_conf_settings(self):
        """
        Test and validate configuration and test rigging
        """
        self.assertEqual(
            self.settings['consumers'],
            [
                {'key': 'test_course1',
                 'secret': 'test_secret1',
                 'allowed_sifters': ['test_sifters']},
                {'key': 'test_course2',
                 'secret': 'test_secret2', },
                {'key': 'testo', },
            ]
        )

        # Test consumer search
        consumer = get_consumer('test_course1')
        self.assertEqual(consumer['secret'], 'test_secret1')

        # Test config exception
        conf_save = os.environ['XSIFTX_CONFIG']
        config_path_save = xsiftx.config.CONFIG_PATHS
        del os.environ['XSIFTX_CONFIG']

        xsiftx.config.CONFIG_PATHS = ['/dev/null', ]
        with self.assertRaisesRegexp(XsiftxNoConfigException,
                                     'No configuration found'):
            settings = get_config()

        # Test config by path
        xsiftx.config.CONFIG_PATHS = [conf_save, ]
        settings = get_config()
        self.assertEqual(settings['awesome_canary_key'], 'test')

        os.environ['XSIFTX_CONFIG'] = conf_save
        xsiftx.config.CONFIG_PATHS = config_path_save

    @patch('xsiftx.lti.oauthstore.log')
    def test_no_consumers(self, mock_logging):
        """
        Make sure we handle a lack of conumers altogether well
        """
        saved_consumers = xsiftx.config.settings['consumers']
        del xsiftx.config.settings['consumers']

        response = self.client.post('/', data=self._oauth_request())
        self.assertEquals(response.status_code, 401)
        self.assertTrue(mock_logging.critical.called_with(
            "No consumers defined in settings."
            "Have you created a configuration file?"
        ))

        # Restore
        xsiftx.config.settings['consumers'] = saved_consumers

    @patch('xsiftx.lti.oauthstore.log')
    def test_consumer_without_secret(self, mock_logging):
        """
        Test a consumer that is missing a secret.
        """
        keyless_consumer = 2
        response = self.client.post(
            '/',
            data=self._oauth_request(
                {'oauth_secret': 'test&'},
                keyless_consumer
            )
        )
        self.assertEquals(response.status_code, 401)
        self.assertTrue(mock_logging.critical.called_with(
            'Consumer {0}, is missing secret'
            'in settings file, and needs correction.'.format(
                self.settings['consumers'][keyless_consumer]['key']
            )
        ))

    def test_lti_authentication(self):
        """
        Test out that LTI authentication is working properly
        and that the decorator is raising the proper exceptions
        """
        # Setup empty request
        response = self.client.get('/')
        self.assertEqual(response.status_code, 401)
        self.assertTrue(
            'This page requires a valid oauth session or request' in
            response.data
        )

        # Test bad key
        params = self._oauth_request()
        params['oauth_consumer_key'] = 'silly'
        response = self.client.post('/', data=params)
        self.assertEqual(response.status_code, 401)
        self.assertTrue(
            'OAuth error: Please check your key' in
            response.data
        )

        # Test bad sig
        params = self._oauth_request()
        params['oauth_signature'] = 'silly&'
        response = self.client.post('/', data=params)
        self.assertEqual(response.status_code, 401)
        self.assertTrue(
            'OAuth error: Please check your key' in
            response.data
        )

        # Valid OAuth, but missing authorization
        response = self.client.post('/', data=self._oauth_request())
        self.assertEqual(response.status_code, 401)
        self.assertTrue(
            'User does not have a role' in
            response.data
        )

        # Test https header
        with xsiftx.web.app.test_client() as client:
            response = client.post(
                '/', data=self._oauth_request(),
                headers={'x-forwarded-proto': 'https'}
            )
        self.assertEqual(response.status_code, 401)
        self.assertTrue(
            'User does not have a role' in
            response.data
        )

    def test_lti_staff_decorator(self):
        """
        Make sure that our authorization of role is happening
        """
        params = self._oauth_request({'roles': 'Student'})
        response = self.client.post('/', data=params)
        self.assertEqual(response.status_code, 401)
        self.assertTrue(
            'You are not in a staff level role. Access is restricted ' in
            response.data
        )

    def test_reauthorization(self):
        """
        Make sure that if my role changes, my access changes as well.
        """
        params = self._oauth_request({'roles': 'Student'})
        response = self.client.post('/', data=params)
        self.assertEqual(response.status_code, 401)
        self.assertTrue(
            'You are not in a staff level role. Access is restricted ' in
            response.data
        )

        params = self._oauth_request({'roles': 'Instructor'})
        response = self.client.post('/', data=params)
        self.assertEqual(response.status_code, 200)

    def test_index(self):
        """
        Several tests of the index page
        """
        params = self._oauth_request({'roles': LTI_STAFF_ROLES[0]})
        response = self.client.post('/', data=params)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            'Available Sifters' in
            response.data
        )

    def test_sifter_acl(self):
        """
        Test with consumer that has access to all sifters
        and ensure they all get loaded
        """
        # Test limited ACL
        with xsiftx.web.app.test_client() as client:
            consumer_id = 0
            params = self._oauth_request(
                {'roles': LTI_STAFF_ROLES[0]},
                consumer_id
            )
            response = client.post('/', data=params)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(
                'Available Sifters' in
                response.data
            )
            # Make sure we don't have extra sifters
            self.assertTrue(
                all(sifter in response.data
                    for sifter in
                    self.settings['consumers'][consumer_id]['allowed_sifters'])
            )

        # Test no ACL
        with xsiftx.web.app.test_client() as client:
            consumer_id = 1
            params = self._oauth_request(
                {'roles': LTI_STAFF_ROLES[0]},
                consumer_id
            )
            response = client.post('/', data=params)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(
                'Available Sifters' in
                response.data
            )
            # Make sure we don't have extra sifters
            self.assertTrue(
                all(sifter in response.data
                    for sifter in get_sifters())
            )

    def test_api_error(self):
        """
        Excercise the API error handler to make sure it returns
        json.
        """

        test_url = '/api/v0.1/run'

        # Test that LTI error on API url returns JSON instead of html
        response = self.client.post(test_url)
        self.assertEqual(response.status_code, 401)
        json.loads(response.data)

        # Test no sifter
        response = self.client.post(
            test_url,
            data=self._oauth_request()
        )
        self.assertEqual(response.status_code, 400)
        # Should raise if we don't get json
        reply_json = json.loads(response.data)
        self.assertTrue(
            u'This api call requires the parameter "sifter".' ==
            reply_json['message']
        )

        # Test invalid sifter
        response = self.client.post(
            test_url,
            data=self._oauth_request({'sifter': 'not_a_real_thing'})
        )
        self.assertEqual(response.status_code, 400)
        # Should raise if we don't get json
        reply_json = json.loads(response.data)
        self.assertTrue(
            u'You have specified an invalid sifter.' ==
            reply_json['message']
        )
        self.assertIsNotNone(reply_json.get('available_sifters', None))

    def test_run_sifter(self):
        """
        Test out the run command
        """
        reply_json = self._run_sifter()
        # Even though the job should fail, we should get
        # back the job id and such
        self.assertTrue(reply_json['tasks'][0]['status'] == 'PENDING')

    def test_task_status_and_delete(self):
        """
        Test task status API point and validate response json
        """
        update_url = '/api/v0.1/update_task_status'
        # Create several runs
        num_runs = 10
        for _ in range(num_runs):
            reply_json = self._run_sifter('xqanalyze')

        # Check we have the right number
        response = self.client.put(
            update_url,
            data=self._oauth_request()
        )
        reply_json = json.loads(response.data)
        self.assertTrue(len(reply_json['tasks']), num_runs)

        # Now delete them
        delete_url = '/api/v0.1/clear_complete_tasks'
        response = self.client.delete(
            delete_url,
            data=self._oauth_request()
        )
        reply_json = json.loads(response.data)
        self.assertTrue(len(reply_json['tasks']), 0)

        # And double check they are gone
        # Check we have the right number
        response = self.client.put(
            update_url,
            data=self._oauth_request()
        )
        reply_json = json.loads(response.data)
        self.assertTrue(len(reply_json['tasks']), 0)

    def test_logging_level(self):
        """
        Tests to make sure logging config happens and handles
        bad output.
        """
        # Check it is the right setting from test config
        self.assertEqual(self.settings['log_level'], 'debug')
        level = xsiftx.web.set_log_level()
        # Check that setting is not applied
        self.assertEqual(logging.DEBUG, level)

        # Set to invalid level and assert the exception
        xsiftx.config.settings['log_level'] = 'awesome'
        with self.assertRaisesRegexp(ValueError, 'Invalid log level.*'):
            level = xsiftx.web.set_log_level()
            self.assertIsNone(level)

        # Make sure it is ok not to have a level set
        del xsiftx.config.settings['log_level']
        level = xsiftx.web.set_log_level()
        self.assertIsNone(level)

        # Restore setting
        xsiftx.config.settings['log_level'] = 'debug'
