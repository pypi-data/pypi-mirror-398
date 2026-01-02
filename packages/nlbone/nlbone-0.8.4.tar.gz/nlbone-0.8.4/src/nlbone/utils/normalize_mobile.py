import re
from typing import List


def normalize_mobile(mobile, strip_zero=True, add_country_code=True):
    if not mobile:
        return ""

    mobile = re.sub(r"\D", "", str(mobile))

    if mobile.startswith("0098"):
        mobile = mobile[4:]
    elif mobile.startswith("98") and len(mobile) > 10:
        mobile = mobile[2:]

    if strip_zero and mobile.startswith("0"):
        mobile = mobile[1:]

    if add_country_code:
        if not mobile.startswith("98"):
            mobile = f"98{mobile}"

    return mobile


def remove_duplicates(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out
