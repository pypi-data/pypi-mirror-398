import os
import importlib
from datetime import datetime, timezone
import pytest

PKG = os.getenv("PKG", "tirreno_tracker")
pkg = importlib.import_module(PKG)
tr = importlib.import_module(f"{PKG}.tracking")

Tracker = pkg.Tracker
Event = pkg.Event


def test_create_and_track_success(monkeypatch, recwarn):
    calls = {}

    def fake_post(*, url=None, data=None, headers=None, timeout=None, **kw):
        calls.update(url=url, data=data, headers=headers, timeout=timeout, kw=kw)

        class R:
            status_code = 204
        return R()

    monkeypatch.setattr(tr.requests, "post", fake_post)

    t = Tracker(api_url="https://localhost/tirreno/sensor/", api_key="k", event_timeout=30)
    ev = t.create_event()
    ev.set_user_name("alice").set_ip_address("1.2.3.4").set_user_agent("UA") \
      .set_http_method("GET").set_http_referer("https://ref/").set_url("https://page/")

    t.track(ev)

    assert calls["url"] == "https://localhost/tirreno/sensor/"
    assert calls["headers"]["Api-Key"] == "k"
    assert calls["timeout"] == 3
    assert isinstance(calls["data"], dict)

    assert t.get_event(ev.get_uuid()) is None


def test_track_missing_event_warns(recwarn):
    t = Tracker(api_url="https://localhost/tirreno/sensor/", api_key="k")
    stray = Event("fake-uuid")
    t.track(stray)
    assert any("Tracker misses Event object" in str(w.message) for w in recwarn.list)


def test_outdated_cleanup_drop(monkeypatch, recwarn):
    called = {"n": 0}

    def fake_post(*, url=None, data=None, headers=None, timeout=None, **kw):
        called["n"] += 1

        class R:
            status_code = 204
        return R()

    monkeypatch.setattr(tr.requests, "post", fake_post)

    t1 = Tracker(api_url="https://localhost/tirreno/sensor/", api_key="k", event_timeout=1)
    old_ts = int(datetime.now(timezone.utc).timestamp()) - 999
    ev = t1.create_event()
    t1._events[ev.get_uuid()]["ts"] = old_ts

    t1.create_event()

    assert any("dropping event" in str(w.message).lower() for w in recwarn.list)
    assert called["n"] == 0


def test_http_exception_warns(monkeypatch, recwarn):
    def boom(**kwargs):
        raise tr.requests.RequestException("network down")

    monkeypatch.setattr(tr.requests, "post", boom)

    t = Tracker(api_url="https://localhost/tirreno/sensor/", api_key="k")
    ev = t.create_event()
    ev.set_user_name("alice").set_url("https://page/").set_http_method("GET")

    t.track(ev)
    assert any("network down" in str(w.message).lower() for w in recwarn.list)
