import json
import re
from math import ceil
from typing import Any, List, Optional, Dict, Union

from fastapi import Query


class PaginateRequest:
    """
    FastAPI-friendly request parser for pagination, sorting, and filters.
    Example: ?limit=20&offset=0&sort=created_at:desc,id:asc&filters=status:active,age:30
             or filters='{"status": "active", "age": 30}'
    """

    def __init__(
        self,
        limit: int = 10,
        offset: int = 0,
        sort: Optional[str] = None,
        filters: Optional[str] = Query(None, description="e.g. title:abc"),
        include: Optional[str] = None,
    ) -> None:
        self.limit = max(0, limit)
        self.offset = max(0, offset)
        self.sort = self._parse_sort(sort)
        self.filters = self._parse_filters(filters or "")
        self.include = []
        try:
            self.include = [{item.split(":")[0]: item.split(":")[1]} for item in include.split(",")]
        except:
            pass
        self.include_ids: List[int] = ([int(x) for x in include.split(",") if x.strip().isdigit()] if include else [])[
            :50
        ]

    @staticmethod
    def _parse_sort(sort_str: Optional[str]) -> list[dict[str, str]]:
        if not sort_str:
            return []
        result: list[dict[str, str]] = []
        for part in sort_str.split(","):
            part = part.strip()
            if not part:
                continue
            if ":" in part:
                field, direction = part.split(":", 1)
            else:
                field, direction = part, "desc"  # default
            direction = direction.strip().lower()
            if direction not in {"asc", "desc"}:
                direction = "desc"
            result.append({"field": field.strip(), "order": direction})
        return result

    @staticmethod
    def _parse_filters(filters: str) -> Dict[str, Any]:
        if not filters:
            return {}

        stripped_filters = filters.strip()

        if stripped_filters.startswith(("{", "[")):
            try:
                data = json.loads(stripped_filters)
                return dict(data) if isinstance(data, dict) else {"$": data}
            except (json.JSONDecodeError, TypeError):
                pass

        pattern = re.compile(r"(?P<key>[^:,]+):\s*(?P<value>\[.*?\]|[^,]+)")
        filters_dict: Dict[str, Any] = {}

        for match in pattern.finditer(stripped_filters):
            key = match.group("key").strip().strip("'\"")
            value_raw = match.group("value").strip()

            filters_dict[key] = PaginateRequest._process_value(value_raw)

        return filters_dict

    @staticmethod
    def _process_value(value: str) -> Any:
        if value.startswith("[") and value.endswith("]"):
            content = value[1:-1]
            if not content.strip():
                return []
            return [PaginateRequest._cast_primitive(item.strip()) for item in content.split(",")]

        return PaginateRequest._cast_primitive(value)

    @staticmethod
    def _cast_primitive(value: str) -> Union[int, float, bool, str]:
        clean_value = value.strip("'\"")
        lower_value = clean_value.lower()

        if lower_value == "true":
            return True
        if lower_value == "false":
            return False

        if clean_value.isdigit():
            return int(clean_value)

        try:
            return float(clean_value)
        except ValueError:
            return clean_value

    def remove_deleted(self, deleted_at_field: str = "deleted_at"):
        self.filters = self.filters | {"deleted_at": None}


class PaginateResponse:
    """
    Lightweight response shaper. If total_count is None → returns just items.
    """

    def __init__(
        self,
        data: list[Any],
        total_count: int | None,
        limit: int,
        offset: int,
        use_data_key: bool = True,
    ) -> None:
        self.data = data
        self.total_count = total_count
        self.limit = limit
        self.offset = offset
        self.page = (offset // limit) + 1 if limit > 0 else 1
        self.per_page = limit
        self.total_page = ceil(total_count / limit) if (total_count is not None and limit > 0) else None
        self.result_count = len(data)
        self.use_data_key = use_data_key

    def to_dict(self) -> dict[str, Any]:
        if self.total_count is None:
            # streaming/unk-count mode
            key = "data" if self.use_data_key else "items"
            return {key: self.data}
        return {
            "total_count": self.total_count,
            "total_page": self.total_page,
            ("data" if self.use_data_key else "items"): self.data,
        }
