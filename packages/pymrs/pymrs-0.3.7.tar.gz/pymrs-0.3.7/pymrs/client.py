import asyncio
import threading
from .asyncclient import AsyncMRSClient
from typing import Callable, Any, Dict


class MRSClient:
    """
    A synchronous wrapper around AsyncMRSClient, providing the same methods by
    calling the asynchronous methods without closing the event loop.
    """

    def __init__(self, hostname, kadme_token, username, password=None, ticket=None, timeout=120):
        self.async_client = AsyncMRSClient(
            hostname, kadme_token, username, password, ticket, timeout
        )
        self._loop = None
        self._loop_thread = None

    def __enter__(self):
        """
        Enter method for context management.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit method for context management.
        Ensures that shutdown is called when the context exits.
        """
        self.shutdown()

    def _get_or_create_event_loop(self):
        if self._loop is None:
            # Create a new event loop in a separate thread
            self._loop = asyncio.new_event_loop()
            self._loop_thread = threading.Thread(target=self._loop.run_forever)
            self._loop_thread.start()
        return self._loop

    def _run_async(self, coro):
        loop = self._get_or_create_event_loop()
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()

    def _authenticate(self, oauth_token=None):
        return self._run_async(self.async_client._authenticate(oauth_token))

    def validate_ticket(self):
        self._run_async(self.async_client.validate_ticket())

    @property
    def headers(self):
        return self._run_async(self.async_client.headers)

    @property
    def ticket(self):
        return self._run_async(self.async_client.ticket)

    def close(self):
        self._run_async(self.async_client.close())

    def request(
        self,
        method: str,
        endpoint: str,
        data=None,
        json=None,
        headers=None,
        enable_validation=True,
    ):
        return self._run_async(
            self.async_client.request(
                method, endpoint, data, json, headers, enable_validation
            )
        )

    def get_all_namespaces(self):
        return self._run_async(self.async_client.get_all_namespaces())

    def get_namespace(self, namespace):
        return self._run_async(self.async_client.get_namespace(namespace))

    def get_datatype(self, namespace, datatype):
        return self._run_async(self.async_client.get_datatype(namespace, datatype))

    def es_request(
        self,
        es_host: str,
        es_port: int,
        memoza_namespace: str,
        memoza_class: str,
        es_index: str,
        es_query: Callable[[str, bool, list[str]], Dict[str, Any]],
        enable_validation: bool = True,
    ):
        return self._run_async(
            self.async_client.es_request(
                es_host,
                es_port,
                memoza_namespace,
                memoza_class,
                es_index,
                es_query,
                enable_validation,
            )
        )

    def get_user_roles(self, namespace: str):
        return self._run_async(self.async_client.get_user_roles(namespace))

    def upload_file(self, domain: dict, destinationPath: str, data: bytes):
        return self._run_async(
            self.async_client.upload_file(domain, destinationPath, data)
        )

    def shutdown(self):
        """
        Shuts down the event loop and the background thread.
        """
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
            if self._loop_thread is not None:
                self._loop_thread.join()
            self._loop = None
            self._loop_thread = None

    def __del__(self):
        self.shutdown()
