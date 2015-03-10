import sys
import tempfile
import unittest

from mock import MagicMock
import urllib3

from okta_openvpn import OktaAPIAuth
from okta_openvpn import OktaOpenVPNValidator
from okta_openvpn import PinError

from tests.shared import OktaTestCase
from tests.shared import MockEnviron
from tests.shared import MockLoggingHandler


class TestOktaAPIAuthTLSPinning(OktaTestCase):
    def test_connect_to_unencrypted_server(self):
        config = self.config
        config['okta_url'] = 'http://example.com'
        okta = OktaAPIAuth(**config)
        self.assertRaises(urllib3.exceptions.PoolError, okta.preauth)

    def test_connect_to_encrypted_but_unintended_server(self):
        config = self.config
        config['okta_url'] = 'https://example.com'
        okta = OktaAPIAuth(**config)
        self.assertRaises(PinError, okta.preauth)

    def test_connect_to_okta_with_good_pins(self):
        config = self.config
        config['okta_url'] = 'https://example.okta.com'
        okta = OktaAPIAuth(**config)
        result = okta.preauth()
        # This is what we'll get since we're sending an invalid token:
        self.assertIn('errorSummary', result)
        self.assertEquals(result['errorSummary'], 'Invalid token provided')

    def test_connect_to_example_with_good_pin(self):
        config = self.config
        config['assert_pinset'] = [self.herokuapp_dot_com_pin]
        okta = OktaAPIAuth(**config)
        result = okta.preauth()
        self.assertIn('status', result)
        self.assertEquals(result['status'], 'MFA_REQUIRED')

    def test_connect_to_example_with_bad_pin(self):
        config = self.config
        config['assert_pinset'] = ['not-a-sha256']
        okta = OktaAPIAuth(**config)
        self.assertRaises(PinError, okta.preauth)

    def test_validate_conn_checks_is_verified(self):
        from okta_openvpn import PublicKeyPinsetConnectionPool
        pool = PublicKeyPinsetConnectionPool('example.com', 443)
        conn = MagicMock()
        conn.is_verified = False
        self.assertRaises(Exception, pool._validate_conn, conn)