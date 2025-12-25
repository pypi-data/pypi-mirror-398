import configparser
import unittest
from unittest.mock import Mock

from httpx import HTTPStatusError
from mrs import MRSClient, MRSClientError

# import logging
# log = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)
import warnings


class TestMRSClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        warnings.filterwarnings(
            action="ignore", message="unclosed", category=ResourceWarning
        )
        config = configparser.ConfigParser()
        config.read("secrets.ini")
        cls.hostname = config["SANDBOX"]["HOSTNAME"]
        cls.kadme_token = config["SANDBOX"]["KADME_TOKEN"]
        cls.username = config["SANDBOX"]["USERNAME"]
        cls.password = config["SANDBOX"]["PASSWORD"]
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        return super().tearDownClass()

    def test_valid_input(self):
        self.client = MRSClient(
            self.hostname, self.kadme_token, self.username, self.password
        )
        self.assertEqual(self.client.hostname, self.hostname)
        self.assertEqual(self.client.kadme_token, self.kadme_token)
        self.assertEqual(self.client.username, self.username)
        self.assertEqual(self.client.password, self.password)
        self.client.client.close()

    def test_input_invalid_hostname(self):
        with self.assertRaises(ValueError):
            MRSClient(
                hostname="",
                kadme_token=self.kadme_token,
                username=self.username,
                password=self.password,
            )

    def test_input_invalid_kadme_token(self):
        with self.assertRaises(ValueError):
            MRSClient(
                hostname=self.hostname,
                kadme_token="",
                username=self.username,
                password=self.password,
            )

    def test_input_invalid_username(self):
        with self.assertRaises(ValueError):
            MRSClient(
                hostname=self.hostname,
                kadme_token=self.kadme_token,
                username="",
                password=self.password,
            )

    def test_input_invalid_password(self):
        with self.assertRaises(ValueError):
            MRSClient(
                hostname=self.hostname,
                kadme_token=self.kadme_token,
                username=self.username,
                password="",
            )

    def test_authenticate_invalid_username(self):
        with self.assertRaises(MRSClientError):
            MRSClient(
                hostname=self.hostname,
                kadme_token=self.kadme_token,
                username="asdgsdv",
                password=self.password,
            )

    def test_authenticate_invalid_password(self):
        with self.assertRaises(MRSClientError):
            MRSClient(
                hostname=self.hostname,
                kadme_token=self.kadme_token,
                username=self.username,
                password="sgasgae",
            )

    def test_close(self):
        with self.assertRaises(HTTPStatusError):
            self.client = MRSClient(
                self.hostname, self.kadme_token, self.username, self.password
            )
            self.client.close()

    def test_validate_ticket(self):
        self.client = MRSClient(
            self.hostname, self.kadme_token, self.username, self.password
        )
        mock_response = Mock(status_code=200)
        mock_get = Mock(return_value=mock_response)
        self.client.client.get = mock_get
        self.client._authenticate = Mock()
        self.client._ticket = "valid_ticket"
        self.client.validate_ticket()
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(self.client._authenticate.call_count, 0)

    def test_validate_empty_ticket(self):
        self.client = MRSClient(
            self.hostname, self.kadme_token, self.username, self.password
        )
        self.client._authenticate = Mock()
        self.client._ticket = ""
        self.client.validate_ticket()
        self.assertEqual(self.client._authenticate.call_count, 1)

    def test_validate_invalid_ticket(self):
        self.client = MRSClient(
            self.hostname, self.kadme_token, self.username, self.password
        )
        self.client._authenticate = Mock()
        self.client._ticket = "dsgsdgshs"
        self.client.validate_ticket()
        self.assertEqual(self.client._authenticate.call_count, 1)

    def test_request(self):
        self.client = MRSClient(
            self.hostname, self.kadme_token, self.username, self.password
        )
        self.client.request(
            "POST",
            "/security/auth/login.json",
            {"userName": self.username, "password": self.password},
        )
        self.client.client.close()

    def test_request_invalid_rest_method(self):
        with self.assertRaises(ValueError):
            self.client = MRSClient(
                self.hostname, self.kadme_token, self.username, self.password
            )
            self.client.request("CHANGE", "/security/auth/log.json")
            self.client.client.close()

    def test_request_invalid_input(self):
        with self.assertRaises(MRSClientError):
            self.client = MRSClient(
                self.hostname, self.kadme_token, self.username, self.password
            )
            self.client.request("GET", "/security/auth/validateticket.json")
            self.client.client.close()

    def test_with_as(self):
        self.client = MRSClient(
            self.hostname, self.kadme_token, self.username, self.password
        )
        with self.client as cli:
            cli.validate_ticket()
        self.client.client.close()


if __name__ == "__main__":
    unittest.main()
