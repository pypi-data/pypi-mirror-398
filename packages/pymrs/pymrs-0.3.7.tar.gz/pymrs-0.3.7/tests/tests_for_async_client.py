import configparser
import unittest
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from httpx import HTTPStatusError
from mrs import AsyncMRSClient, MRSClientError

# import logging
# log = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)
import warnings


class TestMRSClient(IsolatedAsyncioTestCase):

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

    async def test_valid_input(self):
        self.client = AsyncMRSClient(
            self.hostname, self.kadme_token, self.username, self.password
        )
        await self.client._authenticate()
        self.assertEqual(self.client.hostname, self.hostname)
        self.assertEqual(self.client.kadme_token, self.kadme_token)
        self.assertEqual(self.client.username, self.username)
        self.assertEqual(self.client.password, self.password)
        await self.client.client.aclose()

    async def test_input_invalid_hostname(self):
        with self.assertRaises(ValueError):
            AsyncMRSClient(
                hostname="",
                kadme_token=self.kadme_token,
                username=self.username,
                password=self.password,
            )

    async def test_input_invalid_kadme_token(self):
        with self.assertRaises(ValueError):
            AsyncMRSClient(
                hostname=self.hostname,
                kadme_token="",
                username=self.username,
                password=self.password,
            )

    async def test_input_invalid_username(self):
        with self.assertRaises(ValueError):
            AsyncMRSClient(
                hostname=self.hostname,
                kadme_token=self.kadme_token,
                username="",
                password=self.password,
            )

    async def test_input_invalid_password(self):
        with self.assertRaises(ValueError):
            AsyncMRSClient(
                hostname=self.hostname,
                kadme_token=self.kadme_token,
                username=self.username,
                password="",
            )

    async def test_authenticate_invalid_username(self):
        with self.assertRaises(MRSClientError):
            self.client = AsyncMRSClient(
                hostname=self.hostname,
                kadme_token=self.kadme_token,
                username="asdgsdv",
                password=self.password,
            )
            await self.client._authenticate()

    async def test_authenticate_invalid_password(self):
        with self.assertRaises(MRSClientError):
            self.client = AsyncMRSClient(
                hostname=self.hostname,
                kadme_token=self.kadme_token,
                username=self.username,
                password="sgasgae",
            )
            await self.client._authenticate()

    async def test_close(self):
        with self.assertRaises(HTTPStatusError):
            self.client = AsyncMRSClient(
                self.hostname, self.kadme_token, self.username, self.password
            )
            await self.client._authenticate()
            await self.client.close()

    async def test_validate_ticket(self):
        self.client = AsyncMRSClient(
            self.hostname, self.kadme_token, self.username, self.password
        )
        await self.client._authenticate()
        mock_response = AsyncMock(status_code=200)
        mock_get = AsyncMock(return_value=mock_response)
        self.client.client.get = mock_get
        self.client._authenticate = AsyncMock()
        self.client._ticket = "valid_ticket"
        await self.client.validate_ticket()
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(self.client._authenticate.call_count, 0)

    async def test_validate_empty_ticket(self):
        self.client = AsyncMRSClient(
            self.hostname, self.kadme_token, self.username, self.password
        )
        await self.client._authenticate()
        self.client._authenticate = AsyncMock()
        self.client._ticket = ""
        await self.client.validate_ticket()
        self.assertEqual(self.client._authenticate.call_count, 1)

    async def test_validate_invalid_ticket(self):
        self.client = AsyncMRSClient(
            self.hostname, self.kadme_token, self.username, self.password
        )
        await self.client._authenticate()
        self.client._authenticate = AsyncMock()
        self.client._ticket = "dsgsdgshs"
        await self.client.validate_ticket()
        self.assertEqual(self.client._authenticate.call_count, 1)

    async def test_request(self):
        self.client = AsyncMRSClient(
            self.hostname, self.kadme_token, self.username, self.password
        )
        await self.client._authenticate()
        await self.client.request(
            "POST",
            "/security/auth/login.json",
            {"userName": self.username, "password": self.password},
        )
        await self.client.client.aclose()

    async def test_request_invalid_rest_method(self):
        with self.assertRaises(ValueError):
            self.client = AsyncMRSClient(
                self.hostname, self.kadme_token, self.username, self.password
            )
            await self.client._authenticate()
            await self.client.request("CHANGE", "/security/auth/log.json")
            await self.client.client.aclose()

    async def test_request_invalid_input(self):
        with self.assertRaises(MRSClientError):
            self.client = AsyncMRSClient(
                self.hostname, self.kadme_token, self.username, self.password
            )
            await self.client._authenticate()
            await self.client.request("GET", "/security/auth/validateticket.json")
            await self.client.client.aclose()

    # async def test_with_as(self):
    #     self.client = AsyncMRSClient(
    #         self.hostname, self.kadme_token, self.username, self.password
    #     )
    #     await self.client._authenticate()
    #     # with self.client as cli:
    #     #     await cli.validate_ticket()
    #     await self.client.client.aclose()


if __name__ == "__main__":
    unittest.main()
