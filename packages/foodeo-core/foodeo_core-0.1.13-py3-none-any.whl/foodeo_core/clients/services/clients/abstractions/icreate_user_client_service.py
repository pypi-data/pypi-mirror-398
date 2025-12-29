from abc import ABC, abstractmethod
from dataclasses import dataclass

from foodeo_core.dataclasses.result import ResultWithValue


@dataclass(frozen=True)
class ClientData:
    client_name: str
    client_phone: str
    client_email: str
    communications: bool


class ICreateUserClientService(ABC):

    @abstractmethod
    def get_or_create_client_from_data(self, data: ClientData) -> ResultWithValue[int]:
        pass
