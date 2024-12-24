from enum import StrEnum
import typing as t
from abc import ABC, abstractmethod

from openai import OpenAI
from pydantic import BaseModel, Field
from sandra_ai.config import app_config
from sandra_ai.conversation_store import conversation_store


default_open_ai_client = OpenAI(api_key=app_config.openai_api_key)


def get_open_ai_client() -> OpenAI:
    return default_open_ai_client


T = t.TypeVar("T")


class Role(StrEnum):
    DEVELOPER = "developer"
    ASSISTANT = "assistant"
    USER = "user"


class Message(BaseModel):
    role: str
    content: str = Field(default="")


class ConversationContext(BaseModel):
    messages: list[Message] = Field(default=[])

    def _add_message(
        self,
        role: str,
        content: str,
    ) -> None:
        new_message = Message(
            role=role,
            content=content,
        )
        self.messages.append(new_message)

    def add_developer_message(self, content: str) -> None:
        self._add_message(role=Role.DEVELOPER, content=content)

    def add_assistant_message(self, content: str) -> None:
        self._add_message(role=Role.ASSISTANT, content=content)

    def add_user_message(self, content: str) -> None:
        self._add_message(role=Role.USER, content=content)

    def merge(self, conversation_context_2: "ConversationContext") -> None:
        for message in conversation_context_2.messages:
            self.messages.append(message)

    def from_conversation_store_messages(self, messages: list[conversation_store.Message]) -> None:
        for message in messages:
            match message.sayer:
                case conversation_store.Sayer.CHAT:
                    self.add_assistant_message(content=message.content)
                case conversation_store.Sayer.USER:
                    self.add_user_message(content=message.content)
                case _:
                    raise ValueError("Unknown message sayer")


class Agent(ABC):
    @abstractmethod
    def generate_response(self, conversation_context: ConversationContext) -> str:
        pass

    @abstractmethod
    def generate_formatted_response(self, conversation_context: ConversationContext, format: t.Type[T]) -> T:
        pass

    def greet(self) -> str:
        return "Hello!"


class OpenAiAgent(Agent, BaseModel):
    client: OpenAI
    gpt_model: str = Field(default="gpt-4o-mini")

    class Config:
        arbitrary_types_allowed = True

    def _from_conversation_context_format(self, conversation_context: ConversationContext) -> t.Iterable[t.Any]:
        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in conversation_context.messages
        ]

    def generate_formatted_response(self, conversation_context: ConversationContext, format: t.Type[T]) -> T:
        response = self.client.beta.chat.completions.parse(
            temperature=0,
            model=self.gpt_model,
            messages=self._from_conversation_context_format(conversation_context),
            response_format=format,
        )

        return response.choices[0].message.parsed  # type: ignore

    def generate_response(self, conversation_context: ConversationContext) -> str:
        response = self.client.chat.completions.create(
            temperature=0,
            model=self.gpt_model,
            messages=self._from_conversation_context_format(conversation_context),
        )
        return response.choices[0].message.content or ""


class DependenciesIdentifierAgentResponseStockRelated(StrEnum):
    NO = "NO"
    YES = "YES"


class DependenciesIdentifierAgentResponseModel(BaseModel):
    stock_related: DependenciesIdentifierAgentResponseStockRelated
    msg: str


class DependenciesIdentifierAgent(OpenAiAgent):
    def _generate_formatted_response(
        self, conversation_context: ConversationContext
    ) -> DependenciesIdentifierAgentResponseModel:
        return super().generate_formatted_response(conversation_context, DependenciesIdentifierAgentResponseModel)

    def respond_to_user_prompt(
        self, prompt: str, old_conversation_context: ConversationContext = ConversationContext()
    ) -> DependenciesIdentifierAgentResponseModel:
        conversation_context = ConversationContext()
        conversation_context.add_developer_message(
            """
            You are a chatbot capable of assisting potential car buyers.
            You can answer questions about cars in stock.
            Identify if the prompt requires a stock knowledge or if it's a general question.
            format the response as a json: {stock_related: YES/NO, msg: Your response}
            """
        )
        conversation_context.merge(old_conversation_context)
        conversation_context.add_user_message(prompt)
        return self._generate_formatted_response(conversation_context)


class SqlGeneratorAgentIsQuery(StrEnum):
    NO = "NO"
    YES = "YES"


class SqlGeneratorAgentResponseModel(BaseModel):
    is_query: SqlGeneratorAgentIsQuery
    msg: str


class SqlGeneratorAgent(OpenAiAgent):
    def _generate_formatted_response(self, conversation_context: ConversationContext) -> SqlGeneratorAgentResponseModel:
        return super().generate_formatted_response(conversation_context, SqlGeneratorAgentResponseModel)

    def generate_sql(
        self, prompt: str, old_conversation_context: ConversationContext = ConversationContext()
    ) -> SqlGeneratorAgentResponseModel:
        conversation_context = ConversationContext()
        conversation_context.add_developer_message(
            """
            You are a chatbot capable of assisting potential car buyers.
            You can answer questions about cars in stock.
            Always try to give choices and guide to buy a car.
            Don't assume things that may narrow the selection.
            Step1: Identify if the prompt can be transformed into a select sql query to look for a car in a sql db? Only queries starting with select are acceptable.
            Step2: If step 1 = to YES, Identify what the prompt can be parsed according to the schema and few data else just answer the prompt as described in the final step
            Step3: Verify if the filters are meaningful. When comapring text choose the like over the equal.
            Step4: format the response as a json: {is_query: YES/NO, msg: Provide me with with sql queries that would be used later on on tables. Don't add the ```sql\n etc surroundings or the response}
            """
        )
        conversation_context.merge(old_conversation_context)
        conversation_context.add_user_message(prompt)
        return self._generate_formatted_response(conversation_context)


class SQLToHumanAgent(OpenAiAgent):
    def transform(self, prompt: str, old_conversation_context: ConversationContext = ConversationContext()) -> str:
        conversation_context = ConversationContext()
        conversation_context.add_developer_message(
            """
            You are a chatbot capable of assisting potential car buyers.
            You can answer questions about cars in stock.
            Given a row data from an sql result formulate it to a human readable information to give the needed infos.
            Do not include sql language in the response.
            """
        )
        conversation_context.merge(old_conversation_context)
        conversation_context.add_user_message(prompt)
        return self.generate_response(conversation_context)


class NextSteps(StrEnum):
    TEST_DRIVE = "TEST_DRIVE"
    SAVE_CUSTOMER_INFO = "SAVE_CUSTOMER_INFO"
    UPDATE_CRM = "UPDATE_CRM"


class NextStepSuggestorAgentResponseModel(BaseModel):
    known_next_step: NextSteps | None
    msg: str


class NextStepSuggestorAgent(OpenAiAgent):
    def _generate_formatted_response(
        self, conversation_context: ConversationContext
    ) -> NextStepSuggestorAgentResponseModel:
        return super().generate_formatted_response(conversation_context, NextStepSuggestorAgentResponseModel)

    def suggest(
        self, prompt: str, old_conversation_context: ConversationContext = ConversationContext()
    ) -> NextStepSuggestorAgentResponseModel:
        conversation_context = ConversationContext()
        conversation_context.add_developer_message(
            """
            You are a chatbot capable of assisting potential car buyers.
            You can answer questions about cars in stock.
            According to the discussion you can suggest one of the following:
            * Book a Test Drive: Capture user details and schedule a test drive tagged by 'TEST_DRIVE'.
            * Save Customer Information: Store user contact details for follow-up by a salesperson tagged by 'SAVE_CUSTOMER_INFO'.
            * Update CRM: If the user prefers not to be contacted, update their status in the CRM system accordingly tagged by 'UPDATE_CRM'.
            * Or maintain a discussion but encourage to buy a car, not a known next step so no tag is available
            You are encouraged to ask for the next step and ask about informations accordingly. Be cheerful and welcoming.
            Respond with the following format {known_next_step: with tag or null otherwise, msg: what received as prompt and what you formulated as a suggestion seperated by 2 empty lines}
            """
        )
        conversation_context.merge(old_conversation_context)
        conversation_context.add_user_message(
            f"Okay now suggest what should be the next step after such a response: {prompt}"
        )
        return self._generate_formatted_response(conversation_context)


class NextStepDetectorAgentResponseModel(BaseModel):
    known_next_step: NextSteps | None
    msg: str


class NextStepDetectorAgent(OpenAiAgent):
    def _generate_formatted_response(
        self, conversation_context: ConversationContext
    ) -> NextStepDetectorAgentResponseModel:
        return super().generate_formatted_response(conversation_context, NextStepDetectorAgentResponseModel)

    def detect_next_step(
        self, prompt: str, old_conversation_context: ConversationContext = ConversationContext()
    ) -> NextStepDetectorAgentResponseModel:
        conversation_context = ConversationContext()
        conversation_context.add_developer_message(
            """
            You are a chatbot capable of assisting potential car buyers.
            You can answer questions about cars in stock.
            According to the discussion you can detect if user want to do one of the following:
            * Book a Test Drive: Capture user details and schedule a test drive tagged by 'TEST_DRIVE'.
            * Save Customer Information: Store user contact details for follow-up by a salesperson tagged by 'SAVE_CUSTOMER_INFO'.
            * Update CRM: If the user prefers not to be contacted, update their status in the CRM system accordingly tagged by 'UPDATE_CRM'.
            * Or maintain a discussion but encourage to buy a car, not a known next step so no tag is available
            Respond with the following format {known_next_step: with tag or null otherwise, msg: Confirmation that the step is handled or the msg to maintain discussion}
            """
        )
        conversation_context.merge(old_conversation_context)
        conversation_context.add_user_message(f"detect the step the user wants to do according to his prompt :{prompt}")
        return self._generate_formatted_response(conversation_context)
