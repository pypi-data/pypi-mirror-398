from typing import List

from cheshirecat_python_sdk.endpoints.base import AbstractEndpoint
from cheshirecat_python_sdk.models.api.conversations import (
    ConversationHistoryOutput,
    ConversationDeleteOutput,
    ConversationsResponse,
    ConversationNameChangeOutput,
)
from cheshirecat_python_sdk.utils import deserialize


class ConversationEndpoint(AbstractEndpoint):
    def __init__(self, client: "CheshireCatClient"):
        super().__init__(client)
        self.prefix = "/conversation"

    def get_conversation_history(self, agent_id: str, user_id: str, chat_id: str) -> ConversationHistoryOutput:
        """
        This endpoint returns the conversation history.
        :param agent_id: The agent ID.
        :param user_id: The user ID to filter the conversation history.
        :param chat_id: The chat ID to filter the conversation history.
        :return: ConversationHistoryOutput, a list of conversation history entries.
        """
        return self.get(
            self.format_url(chat_id),
            agent_id,
            user_id=user_id,
            output_class=ConversationHistoryOutput,
        )

    def get_conversations(self, agent_id: str, user_id: str) -> List[ConversationsResponse]:
        """
        This endpoint returns the attributes of the different conversations, given the `agent_id` and the `user_id`.
        :param agent_id: The agent ID.
        :param user_id: The user ID to filter the conversation history.
        :return: List[ConversationsResponse], a list of conversation attributes.
        """
        response = self.get_http_client(agent_id, user_id).get(self.prefix)
        response.raise_for_status()

        return [deserialize(item, ConversationsResponse) for item in response.json()]

    def delete_conversation(self, agent_id: str, user_id: str, chat_id: str) -> ConversationDeleteOutput:
        """
        This endpoint deletes the conversation.
        :param agent_id: The agent ID.
        :param user_id: The user ID to filter the conversation history.
        :param chat_id: The chat ID to filter the conversation history.
        :return: ConversationDeleteOutput, a message indicating whether the conversation was deleted.
        """
        return self.delete(
            self.format_url(chat_id),
            agent_id,
            output_class=ConversationDeleteOutput,
            user_id=user_id,
        )

    def post_conversation_name(
        self,
        name: str,
        agent_id: str,
        user_id: str,
        chat_id: str,
    ) -> ConversationNameChangeOutput:
        """
        This endpoint creates a new element in the conversation history.
        :param name: The new name to assign to the conversation
        :param agent_id: The agent ID.
        :param user_id: The user ID to filter the conversation history.
        :param chat_id: The chat ID to filter the conversation history.
        :return: ConversationNameChangeOutput, a message indicating whether the conversation name was changed.
        """
        payload = {"name": name}

        return self.post_json(
            self.format_url(chat_id),
            agent_id,
            output_class=ConversationNameChangeOutput,
            payload=payload,
            user_id=user_id,
        )
