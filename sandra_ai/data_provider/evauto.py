from abc import ABC, abstractmethod
from pydantic import BaseModel
from uuid import UUID
import httpx
import typing as t

from sandra_ai.models.cars_model import CarModel
from sandra_ai.repositories.cars_repository import Repository

T = t.TypeVar("T")


class DataProvider(ABC, BaseModel, t.Generic[T]):
    db_repository: Repository[T]

    @abstractmethod
    async def fetch_and_store_data(self) -> None:
        pass


class PageInfo(BaseModel):
    page_size: int
    page_start: int
    total_count: int


class EVautoInventaryResponse(BaseModel):
    page_info: PageInfo
    row_data: list[t.Any]

    @classmethod
    def from_row_data(cls, data: t.Any) -> "EVautoInventaryResponse":
        try:
            return cls(
                page_info=PageInfo(
                    page_size=data["pageInfo"]["pageSize"],
                    page_start=data["pageInfo"]["pageStart"],
                    total_count=data["pageInfo"]["totalCount"],
                ),
                row_data=data["pageInfo"]["trackingData"],
            )
        except KeyError as e:
            raise e

    @classmethod
    def to_car_model(cls, data: t.Any) -> CarModel:
        return CarModel(
            certified=data.get("certified", None),
            model_year=data.get("modelYear", None),
            odometer=data.get("odometer", None),
            option_codes=data.get("optionCodes", None),
            pricing_internet_price=data.get("pricing", None)["internetPrice"],
            pricing_final_price=data.get("pricing", None)["finalPrice"],
            account_id=data.get("accountId", None),
            asking_price=data.get("askingPrice", None),
            autodata_ca_id=data.get("autodataCaId", None),
            body_style=data.get("bodyStyle", None),
            chrome_id=data.get("chromeId", None),
            classification=data.get("classification", None),
            doors=data.get("doors", None),
            drive_line=data.get("driveLine", None),
            exterior_color=data.get("exteriorColor", None),
            fuel_type=data.get("fuelType", None),
            normal_fuel_type=data.get("normalFuelType", None),
            interior_color=data.get("interiorColor", None),
            inventory_date=data.get("inventoryDate", None),
            inventory_type=data.get("inventoryType", None),
            link=data.get("link", None),
            make=data.get("make", None),
            model=data.get("model", None),
            model_code=data.get("modelCode", None),
            new_or_used=data.get("newOrUsed", None),
            sale_price=data.get("salePrice", None),
            stock_number=data.get("stockNumber", None),
            transmission=data.get("transmission", None),
            trim=data.get("trim", None),
            uuid=UUID(data.get("uuid", None)),
            vin=data.get("vin", None),
            year=data.get("year", None),
            address_account_name=data.get("address", None)["accountName"],
            address_city=data.get("address", None)["city"],
            address_country=data.get("address", None)["country"],
            address_postal_code=data.get("address", None)["postalCode"],
            address_state=data.get("address", None)["state"],
        )


class EVAutoDataProvider(DataProvider[CarModel]):
    async def fetch_page(self, start: int) -> EVautoInventaryResponse:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.evauto.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_USED:inventory-data-bus1/getInventory?start={start}"
            )
        return EVautoInventaryResponse.from_row_data(response.json())

    async def fetch_and_store_data(
        self,
    ) -> None:
        await self.db_repository.delete_all()
        start = 0
        while True:
            fetched_page = await self.fetch_page(start)

            for f in fetched_page.row_data:
                car = EVautoInventaryResponse.to_car_model(f)
                await self.db_repository.add(car)
            start = fetched_page.page_info.page_size + fetched_page.page_info.page_start

            if fetched_page.page_info.total_count <= start:
                break
