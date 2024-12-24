from fastapi_mail import ConnectionConfig
from pydantic import BaseModel, EmailStr
from sandra_ai.config import app_config


class EmailSchema(BaseModel):
    email: EmailStr


mailing_config = ConnectionConfig(
    MAIL_USERNAME=app_config.mail_username,
    MAIL_PASSWORD=app_config.mail_password,
    MAIL_FROM="testforsandra@example.com",
    MAIL_PORT=2525,
    MAIL_SERVER="smtp.mailmug.net",
    MAIL_FROM_NAME="Desired Name",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False,
)
