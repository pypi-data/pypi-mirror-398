from abc import ABC, abstractmethod
from typing import TypeVar, Callable

from pydantic import BaseModel

from foodeo_core.settings.models.app_settings import AppSettings
from foodeo_core.settings.models.digital_card_settings import DigitalCardSettings
from foodeo_core.settings.models.domicile_pickup_settings import DomicilePickupSettings
from foodeo_core.settings.models.fiskaly_settings import FiskalySettings
from foodeo_core.settings.models.global_settings import GlobalSettings
from foodeo_core.settings.models.kitchen_ticket_settings import KitchenTicketSettings
from foodeo_core.settings.models.reservation_settings import ReservationSettings
from foodeo_core.settings.models.stock_settings import StockSettings
from foodeo_core.settings.models.ticket_settings import TicketSettings

T = TypeVar("T")
K = TypeVar("K", bound=BaseModel)


class ISettingsManager(ABC):

    @staticmethod
    @abstractmethod
    def get_key(model: type[T], using=None) -> tuple[str, str]:
        pass

    @staticmethod
    @abstractmethod
    def clear_cache(settings: type[T], using=None):
        pass

    @staticmethod
    @abstractmethod
    def get_cached_model(model: type[T],
                         pmodel: type[K],
                         mapper: Callable[[T], K],
                         using=None) -> K:
        pass

    @staticmethod
    @abstractmethod
    def get_global_settings(using=None) -> GlobalSettings:
        pass

    @staticmethod
    @abstractmethod
    def get_setting(model: type[T], using=None) -> T:
        pass

    @staticmethod
    @abstractmethod
    def get_ticket_settings(using=None) -> TicketSettings:
        pass

    @staticmethod
    @abstractmethod
    def get_ticket_kitchen_settings(using=None) -> KitchenTicketSettings:
        pass

    @staticmethod
    @abstractmethod
    def get_domicile_pickup_settings(using=None) -> DomicilePickupSettings:
        pass

    @staticmethod
    @abstractmethod
    def get_app_settings(using=None) -> AppSettings:
        pass

    @staticmethod
    @abstractmethod
    def get_digital_card_settings(using=None) -> DigitalCardSettings:
        pass

    @staticmethod
    @abstractmethod
    def get_reservation_settings(using=None) -> ReservationSettings:
        pass

    @staticmethod
    @abstractmethod
    def get_stock_settings(using=None) -> StockSettings:
        pass

    @staticmethod
    @abstractmethod
    def get_fiskaly_settings(using=None) -> FiskalySettings:
        pass
