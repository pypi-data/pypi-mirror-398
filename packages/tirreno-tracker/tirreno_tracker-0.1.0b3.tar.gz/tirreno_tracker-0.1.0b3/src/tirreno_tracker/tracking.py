import requests
from typing import List, Optional, TypeVar
from uuid import uuid4
from datetime import datetime, timezone
from warnings import warn


PayloadType = TypeVar("PayloadType", bound="Payload")
EventType = TypeVar("EventType", bound="Event")


class Payload:
    PROPERTIES = {
        "_new_value": "new_value",
        "_old_value": "old_value",
        "_field_id": "field_id",
        "_field_name": "field_name",
        "_value": "value",
    }

    def __init__(self) -> None:
        self._new_value = None
        self._old_value = None
        self._field_id = None
        self._field_name = None
        self._value = None

    def set_value(self, value: str) -> PayloadType:
        self._value = value
        return self

    def get_value(self) -> Optional[str]:
        return self._value

    def set_new_value(self, value: str) -> PayloadType:
        self._new_value = value
        return self

    def get_new_value(self) -> Optional[str]:
        return self._new_value

    def set_old_value(self, value: str) -> PayloadType:
        self._old_value = value
        return self

    def get_old_value(self) -> Optional[str]:
        return self._old_value

    def set_field_id(self, value: str) -> PayloadType:
        self._field_id = value
        return self

    def get_field_id(self) -> Optional[str]:
        return self._field_id

    def set_field_name(self, value: str) -> PayloadType:
        self._field_name = value
        return self

    def get_field_name(self) -> Optional[str]:
        return self._field_name

    def dump(self) -> dict:
        out = {}

        for prop in self.PROPERTIES:
            value = getattr(self, prop, None)
            if value is not None:
                out[self.PROPERTIES[prop]] = value

        return out


class Event:
    DEFAULT_PROPERTIES = {
        "_user_name": "userName",
        "_event_time": "eventTime",
        "_ip_address": "ipAddress",
        "_user_agent": "userAgent",
        "_browser_language": "browserLanguage",
        "_http_method": "httpMethod",
        "_http_referer": "httpReferer",
        "_url": "url",
    }

    OPTIONAL_PROPERTIES = {
        "_page_title": "pageTitle",
        "_full_name": "fullName",
        "_first_name": "firstName",
        "_last_name": "lastName",
        "_email_address": "emailAddress",
        "_phone_number": "phoneNumber",
        "_event_type": "eventType",
        "_http_code": "httpCode",
        "_user_created": "userCreated",
    }

    OBJ_PROPERTIES = {
        "_payload": "payload",
        "_field_history": "fieldHistory",
    }

    def __init__(self, uuid: str) -> None:
        self._uuid = uuid
        self._event_type = None
        self._event_time = None
        self._ip_address = None
        self._user_name = None
        self._user_agent = None
        self._browser_language = None
        self._http_code = None
        self._http_method = None
        self._http_referer = None
        self._url = None
        self._page_title = None
        self._payload = None
        self._field_history = None
        self._phone_number = None
        self._email_address = None
        self._first_name = None
        self._last_name = None
        self._full_name = None
        self._user_created = None

        self.set_event_time_now()
        self.set_event_type_page_view()

    def get_uuid(self) -> str:
        return self._uuid

    def set_event_type_page_view(self) -> EventType:
        self._event_type = "page_view"
        return self

    def set_event_type_page_edit(self) -> EventType:
        self._event_type = "page_edit"
        return self

    def set_event_type_page_delete(self) -> EventType:
        self._event_type = "page_delete"
        return self

    def set_event_type_page_search(self) -> EventType:
        self._event_type = "page_search"
        return self

    def set_event_type_account_login(self) -> EventType:
        self._event_type = "account_login"
        return self

    def set_event_type_account_logout(self) -> EventType:
        self._event_type = "account_logout"
        return self

    def set_event_type_account_login_fail(self) -> EventType:
        self._event_type = "account_login_fail"
        return self

    def set_event_type_account_registration(self) -> EventType:
        self._event_type = "account_registration"
        return self

    def set_event_type_account_email_change(self) -> EventType:
        self._event_type = "account_email_change"
        return self

    def set_event_type_account_password_change(self) -> EventType:
        self._event_type = "account_password_change"
        return self

    def set_event_type_account_edit(self) -> EventType:
        self._event_type = "account_edit"
        return self

    def set_event_type_page_error(self) -> EventType:
        self._event_type = "page_error"
        return self

    def set_event_type_field_edit(self) -> EventType:
        self._event_type = "field_edit"
        return self

    def get_event_type(self) -> Optional[str]:
        return self._event_type

    def set_ip_address(self, value: str) -> EventType:
        self._ip_address = value
        return self

    def get_ip_address(self) -> Optional[str]:
        return self._ip_address

    def set_user_name(self, value: str) -> EventType:
        self._user_name = value
        return self

    def get_user_name(self) -> Optional[str]:
        return self._user_name

    def set_user_agent(self, value: str) -> EventType:
        self._user_agent = value
        return self

    def get_user_agent(self) -> Optional[str]:
        return self._user_agent

    def set_browser_language(self, value: str) -> EventType:
        self._browser_language = value
        return self

    def get_browser_language(self) -> Optional[str]:
        return self._browser_language

    def set_http_code(self, value: int) -> EventType:
        self._http_code = value
        return self

    def get_http_code(self) -> Optional[int]:
        return self._http_code

    def set_http_method(self, value: str) -> EventType:
        self._http_method = value
        return self

    def get_http_method(self) -> Optional[str]:
        return self._http_method

    def set_http_referer(self, value: str) -> EventType:
        self._http_referer = value
        return self

    def get_http_referer(self) -> Optional[str]:
        return self._http_referer

    def set_url(self, value: str) -> EventType:
        self._url = value
        return self

    def get_url(self) -> Optional[str]:
        return self._url

    def set_page_title(self, value: str) -> EventType:
        self._page_title = value
        return self

    def get_page_title(self) -> Optional[str]:
        return self._page_title

    def set_phone_number(self, value: str) -> EventType:
        self._phone_number = value
        return self

    def get_phone_number(self) -> Optional[str]:
        return self._phone_number

    def set_email_address(self, value: str) -> EventType:
        self._email_address = value
        return self

    def get_email_address(self) -> Optional[str]:
        return self._email_address

    def set_first_name(self, value: str) -> EventType:
        self._first_name = value
        return self

    def get_first_name(self) -> Optional[str]:
        return self._first_name

    def set_last_name(self, value: str) -> EventType:
        self._last_name = value
        return self

    def get_last_name(self) -> Optional[str]:
        return self._last_name

    def set_full_name(self, value: str) -> EventType:
        self._full_name = value
        return self

    def get_full_name(self) -> Optional[str]:
        return self._full_name

    def set_user_created(self, value: str) -> EventType:
        self._user_created = value
        return self

    def get_user_created(self) -> Optional[str]:
        return self._user_created

    def set_payload(self, value: Payload) -> EventType:
        self._payload = value
        return self

    def get_payload(self) -> Optional[Payload]:
        return self._payload

    def set_field_history(self, value: List[Payload]) -> EventType:
        self._field_history = value
        return self

    def get_field_history(self) -> Optional[List[Payload]]:
        return self._field_history

    def add_field_history(self, value: Payload) -> EventType:
        if self._field_history is None:
            self._field_history = []

        self._field_history.append(value)
        return self

    def set_event_time(self, value: str) -> EventType:
        self._event_time = value
        return self

    def get_event_time(self) -> Optional[str]:
        return self._event_time

    def set_event_time_now(self) -> EventType:
        self._event_time = (
            datetime.now(timezone.utc)
            .replace(tzinfo=None)
            .isoformat(sep=" ", timespec="milliseconds")
        )
        return self

    def dump(self) -> dict:
        out = {}

        value = None
        missing = []

        for prop in self.DEFAULT_PROPERTIES:
            value = getattr(self, prop, None)
            if value is None:
                missing.append(prop)
            else:
                out[self.DEFAULT_PROPERTIES[prop]] = value

        if len(missing):
            missing = ", ".join(missing)
            warn(f"Event properties {missing} should not be None")

        for prop in self.OPTIONAL_PROPERTIES:
            value = getattr(self, prop, None)
            if value is not None:
                out[self.OPTIONAL_PROPERTIES[prop]] = value

        for prop in self.OBJ_PROPERTIES:
            value = getattr(self, prop, None)
            if value is not None:
                if isinstance(value, list):
                    obj = []
                    for el in value:
                        if el is not None and isinstance(el, Payload):
                            obj.append(el.dump())
                    out[self.OBJ_PROPERTIES[prop]] = obj
                elif isinstance(value, Payload):
                    out[self.OBJ_PROPERTIES[prop]] = value.dump()

        return out


class Tracker:
    def __init__(
        self,
        api_url: str,
        api_key: str,
        event_timeout: int = 30,
        connection_timeout: int = 3,
    ) -> None:
        self._url = api_url
        self._headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Api-Key": api_key,
        }
        self._timeout = connection_timeout
        self._events = {}
        self._event_timeout = event_timeout

    def create_event(self) -> Event:
        now = int(datetime.now(timezone.utc).timestamp())
        diff = now - self._event_timeout
        uuids = list(self._events.keys())
        ev = None
        for uuid in uuids:
            ev = self._events.get(uuid)
            if ev and ev.get("ts") is not None and ev.get("ts") < diff:
                ev = self._events.pop(uuid)
                if ev is not None:
                    ev = ev.get("event")
                    if ev is not None:
                        content = ev.dump()
                        warn(f"Event {uuid} was outdated, dropping event with content {str(content)}")

        uuid = uuid4()
        self._events[uuid] = {
            "event": Event(uuid),
            "ts": now,
        }

        return self._events[uuid]["event"]

    def get_event(self, uuid: str) -> Optional[Event]:
        event = self._events.get(uuid, None)
        return event["event"] if event is not None else None

    def track(self, event: Event):
        uuid = event.get_uuid()

        event_collected = self._events.pop(uuid, None)
        if event_collected is None:
            warn(
                f"Tracker misses Event object with uuid {uuid}, create Event objects via Tracker.create_event() method and do not reuse them."
            )
            return self

        event = event_collected.get("event")
        data = event.dump() if event is not None else None

        if data is None:
            warn(
                f"Tracker misses Event object with uuid {uuid}, create Event objects via Tracker.create_event() method and do not reuse them."
            )
            return self

        self._send(data)

        return self

    def _send(self, data: dict):
        try:
            requests.post(
                url=self._url,
                data=data,
                headers=self._headers,
                timeout=self._timeout,
            )
        except requests.RequestException as e:
            warn(e)
