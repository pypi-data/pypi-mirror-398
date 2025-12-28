from datetime import datetime, timezone

import pytest

from wallaroo.utils import _ensure_tz, _unwrap


def test_ensure_tz():
    now = datetime.now()
    nowutz = _ensure_tz(now)
    assert now != nowutz

    now = datetime.now(tz=timezone.utc)
    nowutz = _ensure_tz(now)
    assert now == nowutz


def test_unwrap():
    v = _unwrap(3)
    assert v == 3

    with pytest.raises(Exception):
        v = _unwrap(None)
