import re
import uuid
import warnings
from datetime import datetime

from dateutil.tz import UTC
from pydantic import validator


def _uuid_validator(cls, data, values, **kwargs):
    try:
        uuid.UUID(data)
    except (TypeError, ValueError):
        raise ValueError("must be a uuid string")
    return data


def uuid_validator(field):
    return validator(field, allow_reuse=True)(_uuid_validator)


def _hhmm_validator(cls, data, values, **kwargs):
    if re.search(r"^(0\d|1\d|2[0-3]):[0-5]\d$", data) is None:
        raise ValueError("Field must be string of form HH:MM")
    return data


def hhmm_validator(field):
    return validator(field, allow_reuse=True)(_hhmm_validator)


def _timezone_validator(cls, dt: datetime, values, **kwargs):
    if dt and dt.tzinfo:
        return dt.astimezone(UTC).replace(tzinfo=None)
    else:
        return dt


def timezone_validator(field):
    return validator(field, allow_reuse=True)(_timezone_validator)


def _domain_validator(cls, data, values, **kwargs):
    if data.endswith("/"):
        raise ValueError("Domains must not have a trailing /")
    return data


def domain_validator(field):
    return validator(field, allow_reuse=True)(_domain_validator)


def _account_id_validator_wrapper(lower_limit, upper_limit):
    def _account_id_validator(cls, account_id, values, **kwargs):
        bad_range = False
        try:
            if not (lower_limit <= int(account_id) <= upper_limit):
                bad_range = True
        except ValueError:
            raise ValueError("account_id must be an integer as string")
        if bad_range:
            raise ValueError('account_id must be a value between "%s" and "%s"' % (lower_limit, upper_limit))
        return account_id

    return _account_id_validator


def account_id_range_validator(field, lower_limit=0, upper_limit=1000):
    return validator(field, allow_reuse=True, pre=True, each_item=True)(
        _account_id_validator_wrapper(lower_limit, upper_limit))


def _deprecated_validator(cls, value, values, **kwargs):
    """
    Validator to mark fields as deprecated. It will raise a warning when the field is used.
    """
    warnings.warn(
        f"The field `{cls.__name__}.{kwargs['field'].name}` is deprecated and will be removed in a future version.",
        DeprecationWarning,
        stacklevel=2
    )
    return value


def deprecated_validator(field):
    return validator(field, allow_reuse=True)(_deprecated_validator)
