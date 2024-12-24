import typing as t

from sqlalchemy import text
from sandra_ai.config import app_config
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


engine = create_async_engine(app_config.database_url)

async_session_local = async_sessionmaker(autocommit=False, bind=engine)


async def get_db() -> t.AsyncGenerator[AsyncSession, None]:
    async with async_session_local() as session:
        yield session


async def create_cars_table() -> None:
    async with async_session_local() as db:
        await db.execute(text(DB_SCHEMA))


DB_SCHEMA = """
                CREATE TABLE cars (
                certified BOOLEAN,
                model_year INTEGER,
                odometer INTEGER,
                option_codes TEXT,
                dealer_codes TEXT,
                pricing_internet_price TEXT,
                pricing_final_price TEXT,
                account_id TEXT,
                asking_price TEXT,
                autodata_ca_id TEXT,
                body_style TEXT,
                chrome_id TEXT,
                classification TEXT,
                doors TEXT,
                drive_line TEXT,
                exterior_color TEXT,
                fuel_type TEXT,
                normal_fuel_type TEXT,
                interior_color TEXT,
                inventory_date DATE,
                inventory_type TEXT,
                link TEXT,
                make TEXT,
                model TEXT,
                model_code TEXT,
                new_or_used TEXT,
                sale_price TEXT,
                stock_number TEXT,
                transmission TEXT,
                trim TEXT,
                uuid TEXT PRIMARY KEY,
                vin TEXT,
                year INTEGER,
                address_account_name TEXT,
                address_city TEXT,
                address_country TEXT,
                address_postal_code TEXT,
                address_state TEXT
                )
            """
