from dataclasses import dataclass
from enum import Enum


class SortOrder(Enum):
    ASC = "ASC"
    DESC = "DESC"


@dataclass
class Sort:
    field: str
    order: SortOrder


@dataclass
class Params:
    """
    Usage:
        params = Params(
            filter={"id_customer": "123"},
            sort=Sort(field="date_add", order=SortOrder.DESC),
            display=["id", "total_paid"],
            limit=10
        )
    """

    filter: dict | None = None
    sort: Sort | None = None
    display: list[str] | None = None
    limit: int | None = None
    date: bool | None = None

    def to_dict(self) -> dict:
        """Convert Params to a dictionary suitable for query parameters."""
        params_dict = {}

        # Add filters
        if self.filter:
            for key, value in self.filter.items():
                # If value already has brackets (date ranges), don't add more
                if isinstance(value, str) and value.startswith("[") and value.endswith("]"):
                    params_dict[f"filter[{key}]"] = value
                else:
                    params_dict[f"filter[{key}]"] = f"[{value}]"

        # Add sorting
        if self.sort:
            params_dict["sort"] = f"[{self.sort.field}_{self.sort.order.value}]"

        # Add display fields
        if self.display:
            params_dict["display"] = f"[{','.join(self.display)}]"

        # Add limit
        if self.limit is not None:
            params_dict["limit"] = str(self.limit)

        ## Add date flag
        if self.date is not None:
            params_dict["date"] = "1" if self.date else "0"

        return params_dict

    def __hash__(self) -> int:
        """Custom hash implementation to make Params hashable for caching purposes."""
        return hash(
            (
                frozenset(self.filter.items()) if self.filter else None,
                (self.sort.field, self.sort.order) if self.sort else None,
                tuple(self.display) if self.display else None,
                self.limit,
            )
        )
