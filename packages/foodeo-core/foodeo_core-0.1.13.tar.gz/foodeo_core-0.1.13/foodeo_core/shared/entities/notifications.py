from typing import Any, Optional

from pydantic import BaseModel

from foodeo_core.shared.enums import TYPE_ALERT_NOTIFICATION, COLOR_ALERT_NOTIFICATION


class WebSocketNotification(BaseModel):
    tpv: str
    command: Optional[Any] = None
    type_method: Optional[str] = "delete"
    status: Optional[str] = ""
    is_payed: Optional[bool] = False
    data_to_send: Optional[dict[str, Any]] = None


class WebAllSocketNotification(BaseModel):
    type: TYPE_ALERT_NOTIFICATION
    activate: bool
    text: str
    color: COLOR_ALERT_NOTIFICATION = COLOR_ALERT_NOTIFICATION.INFO
