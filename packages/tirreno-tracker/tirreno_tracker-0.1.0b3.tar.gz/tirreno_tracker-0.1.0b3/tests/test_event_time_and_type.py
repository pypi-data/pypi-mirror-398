import os
import importlib
import re
from datetime import datetime, timezone
import pytest

PKG = os.getenv("PKG", "tirreno_tracker")
tracking = importlib.import_module(f"{PKG}.tracking")
Event = tracking.Event
Tracker = getattr(importlib.import_module(PKG), "Tracker")


def _parse_event_time(s: str) -> datetime:
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}", s)
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")


def test_event_time_set_now_parses_and_is_recent():
    ev = Event("u-now").set_event_time_now()
    ts = ev.get_event_time()
    assert isinstance(ts, str)
    dt = _parse_event_time(ts)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    assert abs((now - dt).total_seconds()) < 5


def test_event_time_manual_set_preserved(recwarn):
    ev = Event("u-manual")
    custom = "2024-01-02 03:04:05.123"
    ev.set_event_time(custom)
    assert ev.get_event_time() == custom
    d = ev.dump()
    assert d.get("eventTime") == custom
    assert any("Event properties" in str(w.message) for w in recwarn.list)


@pytest.mark.parametrize(
    "setter, expected",
    [
        ("set_event_type_page_view", "page_view"),
        ("set_event_type_page_edit", "page_edit"),
        ("set_event_type_page_delete", "page_delete"),
        ("set_event_type_page_search", "page_search"),
        ("set_event_type_account_login", "account_login"),
        ("set_event_type_account_logout", "account_logout"),
        ("set_event_type_account_login_fail", "account_login_fail"),
        ("set_event_type_account_registration", "account_registration"),
        ("set_event_type_account_email_change", "account_email_change"),
        ("set_event_type_account_password_change", "account_password_change"),
        ("set_event_type_account_edit", "account_edit"),
        ("set_event_type_page_error", "page_error"),
        ("set_event_type_field_edit", "field_edit"),
    ],
)
def test_event_type_setters(setter, expected):
    ev = Event("u-type")
    getattr(ev, setter)()
    assert ev.get_event_type() == expected


def test_event_time_present_in_tracker_created_event():
    t = Tracker(api_url="https://localhost/tirreno/sensor/", api_key="k")
    ev = t.create_event()
    ts = ev.get_event_time()
    assert ts and isinstance(ts, str)
    _ = _parse_event_time(ts)
