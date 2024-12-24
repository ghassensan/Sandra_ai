from contextlib import asynccontextmanager
from enum import StrEnum
import uuid
from fastapi import BackgroundTasks, Depends, FastAPI
from http import HTTPStatus
import typing as t
from fastapi_mail import FastMail, MessageSchema, MessageType
from pydantic import BaseModel

from sandra_ai.mailing.mailing import mailing_config

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sandra_ai.agent.agent import (
    ConversationContext,
    DependenciesIdentifierAgent,
    DependenciesIdentifierAgentResponseStockRelated,
    NextStepDetectorAgent,
    NextStepSuggestorAgent,
    NextSteps,
    SQLToHumanAgent,
    SqlGeneratorAgent,
    SqlGeneratorAgentIsQuery,
    get_open_ai_client,
)
from sandra_ai.conversation_store.conversation_store import app_conversation_store
from sandra_ai.data_provider.evauto import EVAutoDataProvider
from sandra_ai.db import DB_SCHEMA, create_cars_table, get_db
from sandra_ai.mailing.mailing import EmailSchema
from sandra_ai.models.cars_model import CarModel
from sandra_ai.repositories.cars_repository import CarsRepository


@asynccontextmanager
async def lifespan(_: FastAPI) -> t.AsyncGenerator[None, None]:
    await create_cars_table()
    yield


app = FastAPI(lifespan=lifespan)


class HealthCheckResponse(BaseModel):
    message: str


@app.get(
    path="/",
    status_code=HTTPStatus.OK,
    response_model=HealthCheckResponse,
)
async def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(message="👍")


class AskResponse(BaseModel):
    uuid: uuid.UUID


@app.post("/ask")
async def start_discussion() -> AskResponse:
    return AskResponse(uuid=uuid.uuid4())


@app.delete("/ask/:uuid", status_code=HTTPStatus.NO_CONTENT)
async def end_discussion(uuid: uuid.UUID, background_tasks: BackgroundTasks) -> None:
    messages = app_conversation_store.get_conversation(uuid)

    mail_to_me = EmailSchema(email="ghassen_chaabane@hotmail.fr")
    mail_to_sandra = EmailSchema(email="infos.sandrai@gmail.com")
    message = MessageSchema(
        subject="Fastapi mail module",
        recipients=[mail_to_me.email, mail_to_sandra.email],
        body=("\n").join([message.model_dump_json() for message in messages]),
        subtype=MessageType.plain,
    )

    fm = FastMail(mailing_config)

    background_tasks.add_task(fm.send_message, message)


class UserMessage(BaseModel):
    prompt: str


class WorkflowStatus(StrEnum):
    CONTINUE = "CONTINUE"
    BREAK = "BREAK"


@app.post("/ask/:uuid")
async def try_chatbot(
    uuid: uuid.UUID,
    user_message: UserMessage,
    db: AsyncSession = Depends(get_db),
) -> dict[str, t.Any]:
    client = get_open_ai_client()

    on_going_discussion = ConversationContext()
    on_going_discussion.from_conversation_store_messages(app_conversation_store.get_conversation(uuid))

    app_conversation_store.add_user_msg(uuid, user_message.prompt)

    workflow_status = WorkflowStatus.CONTINUE
    pre_suggestion = ""

    if workflow_status == WorkflowStatus.CONTINUE:
        next_step_detector_agent = NextStepDetectorAgent(client=client)
        next_step_detector_agent_response = next_step_detector_agent.detect_next_step(
            user_message.prompt, on_going_discussion
        )
        if next_step_detector_agent_response.known_next_step is not None:
            match next_step_detector_agent_response.known_next_step:
                case NextSteps.TEST_DRIVE:
                    workflow_status = WorkflowStatus.BREAK
                    pre_suggestion = next_step_detector_agent_response.msg
                    print(f"handle {NextSteps.TEST_DRIVE}")  # noqa: T201
                case NextSteps.SAVE_CUSTOMER_INFO:
                    workflow_status = WorkflowStatus.BREAK
                    pre_suggestion = next_step_detector_agent_response.msg
                    print(f"handle {NextSteps.SAVE_CUSTOMER_INFO}")  # noqa: T201
                case NextSteps.UPDATE_CRM:
                    workflow_status = WorkflowStatus.BREAK
                    pre_suggestion = next_step_detector_agent_response.msg
                    print(f"handle {NextSteps.UPDATE_CRM}")  # noqa: T201
                case _:
                    raise Exception("This shouldn't happen")

    if workflow_status == WorkflowStatus.CONTINUE:
        dependencies_identifier_agent = DependenciesIdentifierAgent(client=client)
        dependencies_identifier_agent_response = dependencies_identifier_agent.respond_to_user_prompt(
            user_message.prompt, on_going_discussion
        )
        if dependencies_identifier_agent_response.stock_related == DependenciesIdentifierAgentResponseStockRelated.NO:
            workflow_status = WorkflowStatus.BREAK
            pre_suggestion = dependencies_identifier_agent_response.msg

    if workflow_status == WorkflowStatus.CONTINUE:
        car_repository = CarsRepository(model=CarModel, session=db)
        ev_provider = EVAutoDataProvider(db_repository=car_repository)

        await ev_provider.fetch_and_store_data()
        data = await ev_provider.db_repository.get_some()

        sql_generator_agent = SqlGeneratorAgent(client=client)
        sql_generator_agent_response = sql_generator_agent.generate_sql(
            f"""given this schema {DB_SCHEMA} and those few data {data}
            respond with only the sql query that describe this prompt.
            the prompt: {user_message.prompt}
            """,
            on_going_discussion,
        )

        if sql_generator_agent_response.is_query == SqlGeneratorAgentIsQuery.NO:
            workflow_status = WorkflowStatus.BREAK
            pre_suggestion = sql_generator_agent_response.msg

        if workflow_status == WorkflowStatus.CONTINUE:
            response = await ev_provider.db_repository.session.execute(text(sql_generator_agent_response.msg))
            rows = response.fetchall()

            sql_to_human_agent = SQLToHumanAgent(client=client)
            sql_to_human_agent_response = sql_to_human_agent.transform(
                f"reformulate the resulst {rows} of running this sql query {sql_generator_agent_response.msg} in a human way",
                on_going_discussion,
            )
            pre_suggestion = sql_to_human_agent_response if sql_to_human_agent_response is not None else ""

    next_step_suggestor_agent = NextStepSuggestorAgent(client=client)
    next_step_suggestor_agent_response = next_step_suggestor_agent.suggest(pre_suggestion, on_going_discussion)

    app_conversation_store.add_chat_msg(uuid, next_step_suggestor_agent_response.msg)
    return {"message": next_step_suggestor_agent_response.msg}
