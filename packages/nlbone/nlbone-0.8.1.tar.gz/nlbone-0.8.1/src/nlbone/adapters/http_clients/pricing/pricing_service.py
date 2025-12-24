from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

import httpx
import requests
from pydantic import BaseModel, Field, NonNegativeInt, RootModel

from nlbone.adapters.auth.token_provider import ClientTokenProvider
from nlbone.config.settings import get_settings
from nlbone.utils.http import auth_headers, normalize_https_base


class PricingError(Exception):
    pass


class CalculatePriceIn(BaseModel):
    params: dict[str, Any]
    product_id: NonNegativeInt | None = None
    product_title: str | None = None


class DiscountType(str, Enum):
    percent = "percent"
    amount = "amount"


class Product(BaseModel):
    id: Optional[int] = Field(None, description="Nullable product id")
    service_product_id: NonNegativeInt
    title: Optional[str] = None


class Pricing(BaseModel):
    source: Optional[Literal["formula", "static"]] = None
    price: Optional[float] = None
    discount: Optional[float] = None
    discount_type: Optional[DiscountType] = None
    params: Optional[dict] = None


class Segment(BaseModel):
    id: str
    name: str
    specificity: int
    matched_fields: list


class Formula(BaseModel):
    id: int
    title: str
    key: str
    status: str | None
    description: str | None


class PricingRule(BaseModel):
    product: Product
    segment: Segment | None
    formula: Optional[Formula] = None
    pricing: Pricing


class CalculatePriceOut(RootModel[Union[List[PricingRule], Dict[str, PricingRule]]]):
    pass


class PricingService:
    def __init__(
        self,
        token_provider: ClientTokenProvider,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        client: httpx.Client | None = None,
    ) -> None:
        s = get_settings()
        self._base_url = normalize_https_base(base_url or str(s.PRICING_SERVICE_URL), enforce_https=False)
        self._timeout = timeout_seconds or float(s.HTTP_TIMEOUT_SECONDS)
        self._client = client or requests.session()
        self._token_provider = token_provider

    def calculate(self, items: list[CalculatePriceIn], response: Literal["list", "dict"] = "dict") -> CalculatePriceOut:
        body = {"items": [i.model_dump() for i in items]}

        r = self._client.post(
            f"{self._base_url}/price/calculate",
            params={"response": response},
            headers={"X-Api-Key": get_settings().PRICING_API_SECRET, "X-Client-Id": get_settings().KEYCLOAK_CLIENT_ID},
            # headers=auth_headers(self._token_provider.get_access_token()),
            json=body,
            timeout=self._timeout,
            verify=False,
        )

        if r.status_code not in (200, 204):
            raise PricingError(r.status_code, r.text)

        if r.status_code == 204 or not r.content:
            return CalculatePriceOut.model_validate(root=[])

        return CalculatePriceOut.model_validate(r.json())

    def exchange_rates(self) -> Dict[str, Decimal]:
        r = self._client.get(
            f"{self._base_url}/variables/key/exchange_rates",
            headers=auth_headers(self._token_provider.get_access_token()),
            timeout=self._timeout,
            verify=False,
        )

        if r.status_code != 200:
            raise PricingError(r.status_code, r.text)

        values = r.json().get("values")

        return {f"{value['key']}": Decimal(value["value"]) for value in values}
