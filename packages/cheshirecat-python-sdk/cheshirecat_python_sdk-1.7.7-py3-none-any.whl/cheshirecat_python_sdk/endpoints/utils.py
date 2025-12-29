from typing import List

from cheshirecat_python_sdk.endpoints.base import AbstractEndpoint
from cheshirecat_python_sdk.models.api.admins import ResetOutput, ClonedOutput, CreatedOutput
from cheshirecat_python_sdk.utils import deserialize


class UtilsEndpoint(AbstractEndpoint):
    def __init__(self, client: "CheshireCatClient"):
        super().__init__(client)
        self.prefix = "/utils"

    def post_factory_reset(self) -> ResetOutput:
        """
        Reset the system to the factory settings.
        :return: ResetOutput, the details of the reset.
        """
        return self.post_json(self.format_url("/factory/reset/"), self.system_id, output_class=ResetOutput)

    def get_agents(self) -> List[str]:
        """
        Get a list of all agents.
        :return: List[str], the IDs of the agents.
        """
        return self.get(self.format_url("/agents/"), self.system_id)

    def post_agent_create(self, agent_id: str) -> CreatedOutput:
        """
        Create a new agent.
        :param agent_id: The ID of the agent.
        :return: CreatedOutput, the details of the agent.
        """
        response = self.get_http_client().post(
            self.format_url("/agents/create/"),
            json={
                "agent_id": agent_id,
            },
        )
        response.raise_for_status()

        return deserialize(response.json(), CreatedOutput)

    def post_agent_reset(self, agent_id: str) -> ResetOutput:
        """
        Reset an agent to the factory settings.
        :param agent_id: The ID of the agent.
        :return: ResetOutput, the details of the reset.
        """
        return self.post_json(self.format_url("/agents/reset/"), agent_id, output_class=ResetOutput)

    def post_agent_destroy(self, agent_id: str) -> ResetOutput:
        """
        Destroy an agent.
        :param agent_id: The ID of the agent.
        :return: ResetOutput, the details of the reset.
        """
        return self.post_json(self.format_url("/agents/destroy/"), agent_id, output_class=ResetOutput)

    def post_agent_clone(self, agent_id: str, new_agent_id: str) -> ClonedOutput:
        """
        Destroy an agent.
        :param agent_id: The ID of the agent.
        :param new_agent_id: The ID of the new cloned agent.
        :return: ClonedOutput, the details of the cloning.
        """
        return self.post_json(
            self.format_url("/agents/clone/"),
            agent_id,
            payload={"agent_id": new_agent_id},
            output_class=ClonedOutput
        )