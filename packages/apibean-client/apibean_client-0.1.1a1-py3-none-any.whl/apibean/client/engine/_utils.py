from datetime import datetime, timezone


def to_datetime(datetime_str: str|None) -> datetime|None:
    if str is None:
        return None
    return datetime.fromisoformat(datetime_str).replace(tzinfo=timezone.utc)


def get_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_header(headers: dict[str, str], canonical_key: str) -> dict[str, str]:
    normalized = {}
    for key, value in headers.items():
        if key.casefold() == canonical_key.casefold():
            normalized[canonical_key] = value
            break
        else:
            normalized[key] = value
    return normalized


def normalize_headers(headers: dict[str, str], canonical_keys: list[str]) -> dict[str, str]:
    normalized = {}
    for key, value in headers.items():
        for canonical in canonical_keys:
            if key.casefold() == canonical.casefold():
                normalized[canonical] = value
                break
        else:
            # Không khớp: giữ nguyên key gốc
            normalized[key] = value
    return normalized


def comma_delimited_string(s: str):
    return comma_delimited_string_to_cls_list(s, str)


def comma_delimited_string_to_cls_list(s: str, as_cls = str):
    return [as_cls(x.strip()) for x in s.split(',')] if s is not None else None


def comma_delimited_string_to_int_list(s: str):
    return comma_delimited_string_to_cls_list(s, int)
