import ssl
from abc import ABCMeta, abstractmethod
from wallypub.utils.http import HttpsClient


class ReadItLater(metaclass=ABCMeta):
    def __init__(self, host: str, port: int, timeout: int, context: ssl.SSLContext):
        self._client = HttpsClient(host, port, timeout, context)

    @property
    def client(self) -> HttpsClient:
        return self._client

    @abstractmethod
    def get_entry(self, entry_id: str):
        pass
