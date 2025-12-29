from foodeo_core.shared.entities.commands import BarraCommand, LocalCommand, DomicileCommand, PickupCommand, \
    Command, KioskoCommand
from foodeo_core.shared.entities.requests import *


def bulk_to_model(request: type[Request], params: dict) -> Request:
    if "discount" in params and "all_discounted" in params:
        params["discount"]["all_discounted"] = params["all_discounted"]

    return request(**params)


def bulk_to_model_command(command: type[Command], params: dict) -> Command:
    if "discount" in params and "all_discounted" in params:
        params["discount"]["all_discounted"] = params["all_discounted"]

    return command(**params)


def get_request_model(request_type: str) -> type[Request]:
    return {
        "local": LocalRequest,
        "barra": BarraRequest,
        "kiosko": KioskoRequest,
        "domicilio": DomicileRequest,
        "domicile": DomicileRequest,
        "recoger": PickupRequest
    }[request_type]


def get_command_model(command_type: str) -> type[Command]:
    return {
        "local": LocalCommand,
        "barra": BarraCommand,
        "kiosko": KioskoCommand,
        "domicilio": DomicileCommand,
        "domicile": DomicileCommand,
        "recoger": PickupCommand
    }[command_type]
