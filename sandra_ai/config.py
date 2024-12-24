from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    database_url: str
    openai_api_key: str

    mail_username: str
    mail_password: str

    model_config = SettingsConfigDict(env_file=".env")


def get_app_config() -> Config:
    return Config()


app_config = get_app_config()
