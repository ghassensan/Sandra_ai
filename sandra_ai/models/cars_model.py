from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import JSON
from uuid import UUID


class Base(DeclarativeBase):
    pass


class CarModel(Base):
    __tablename__ = "cars"

    certified: Mapped[bool | None] = mapped_column()
    model_year: Mapped[int | None] = mapped_column()
    odometer: Mapped[int | None] = mapped_column()
    option_codes: Mapped[list[str | None]] = mapped_column(JSON)
    pricing_internet_price: Mapped[str | None] = mapped_column()
    pricing_final_price: Mapped[str | None] = mapped_column()
    account_id: Mapped[str | None] = mapped_column()
    asking_price: Mapped[str | None] = mapped_column()
    autodata_ca_id: Mapped[str | None] = mapped_column()
    body_style: Mapped[str | None] = mapped_column()
    chrome_id: Mapped[str | None] = mapped_column()
    classification: Mapped[str | None] = mapped_column()
    doors: Mapped[str | None] = mapped_column()
    drive_line: Mapped[str | None] = mapped_column()
    exterior_color: Mapped[str | None] = mapped_column()
    fuel_type: Mapped[str | None] = mapped_column()
    normal_fuel_type: Mapped[str | None] = mapped_column()
    interior_color: Mapped[str | None] = mapped_column()
    inventory_date: Mapped[str | None] = mapped_column()
    inventory_type: Mapped[str | None] = mapped_column()
    link: Mapped[str | None] = mapped_column()
    make: Mapped[str | None] = mapped_column()
    model: Mapped[str | None] = mapped_column()
    model_code: Mapped[str | None] = mapped_column()
    new_or_used: Mapped[str | None] = mapped_column()
    sale_price: Mapped[str | None] = mapped_column()
    stock_number: Mapped[str | None] = mapped_column()
    transmission: Mapped[str | None] = mapped_column()
    trim: Mapped[str | None] = mapped_column()
    uuid: Mapped[UUID | None] = mapped_column(primary_key=True)
    vin: Mapped[str | None] = mapped_column()
    year: Mapped[int | None] = mapped_column()
    address_account_name: Mapped[str | None] = mapped_column()
    address_city: Mapped[str | None] = mapped_column()
    address_country: Mapped[str | None] = mapped_column()
    address_postal_code: Mapped[str | None] = mapped_column()
    address_state: Mapped[str | None] = mapped_column()
