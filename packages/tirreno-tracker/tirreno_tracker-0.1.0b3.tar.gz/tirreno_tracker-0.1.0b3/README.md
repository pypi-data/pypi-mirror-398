# tirreno Python tracker library

Send data from your Python application to tirreno console.

```python
from tirreno_tracker import Tracker

tirreno_url = "https://example.tld"
tracking_id = "XXX"

tracker = Tracker(tirreno_url, tracking_id)

event = tracker.create_event()

event.set_user_name('johndoe42') \
    .set_ip_address('1.1.1.1') \
    .set_url('/url') \
    .set_user_agent('Mozilla/5.0 (X11; Linux x86_64)') \
    .set_browser_language('fr-FR,fr;q=0.9') \
    .set_http_method('POST') \
    .set_event_type_account_login()

tracker.track(event)
```

## Requirements

* Python 3.6+.

## Installation

### pip

Make sure that `pip` is installed.
Unix-based systems:
```
python -m ensurepip --upgrade
```
Windows:
```
py -m ensurepip --upgrade
```
Install the `tirreno_tracker` module.
```
python -m pip install tirreno_tracker
```

## License

Released under the [BSD License](https://opensource.org/license/bsd-3-clause). tirreno is a
registered trademark of tirreno technologies sàrl, Switzerland.
