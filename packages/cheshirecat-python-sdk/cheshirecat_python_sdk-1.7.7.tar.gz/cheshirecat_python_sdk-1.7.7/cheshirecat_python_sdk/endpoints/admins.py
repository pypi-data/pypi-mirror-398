from typing import List

from cheshirecat_python_sdk.endpoints.base import AbstractEndpoint, MultipartPayload
from cheshirecat_python_sdk.models.api.admins import (
    AdminOutput,
    PluginInstallOutput,
    PluginInstallFromRegistryOutput,
    PluginDetailsOutput,
    PluginDeleteOutput,
)
from cheshirecat_python_sdk.models.api.nested.plugins import PluginSettingsOutput
from cheshirecat_python_sdk.models.api.plugins import PluginCollectionOutput, PluginsSettingsOutput, PluginToggleOutput
from cheshirecat_python_sdk.utils import deserialize, file_attributes


class AdminsEndpoint(AbstractEndpoint):
    def __init__(self, client: "CheshireCatClient"):
        super().__init__(client)
        self.prefix = "/admins"

    def post_admin(self, username: str, password: str, permissions: dict | None = None) -> AdminOutput:
        """
        Create a new admin user.
        :param username: The username of the user.
        :param password: The password of the user.
        :param permissions: The permissions of the user.
        :return: AdminOutput, the details of the user.
        """
        payload = {"username": username, "password": password}
        if permissions:
            payload["permissions"] = permissions  # type: ignore

        return self.post_json(self.format_url("/users"), self.system_id, output_class=AdminOutput, payload=payload)

    def get_admins(self, limit: int | None = None, skip: int | None = None) -> List[AdminOutput]:
        """
        Get a list of all admin users.
        :param limit: The maximum number of users to return.
        :param skip: The number of users to skip.
        :return: List[AdminOutput], the details
        """
        query = {}
        if limit:
            query["limit"] = limit
        if skip:
            query["skip"] = skip

        response = self.get_http_client(self.system_id).get(self.format_url("/users"), params=query)
        response.raise_for_status()

        result = []
        for item in response.json():
            result.append(deserialize(item, AdminOutput))
        return result

    def get_admin(self, admin_id: str) -> AdminOutput:
        """
        Get the details of an admin user.
        :param admin_id: The ID of the user.
        :return: AdminOutput, the details of the user.
        """
        return self.get(self.format_url(f"/users/{admin_id}"), self.system_id, output_class=AdminOutput)

    def put_admin(
        self,
        admin_id: str,
        username: str | None = None,
        password: str | None = None,
        permissions: dict | None = None,
    ) -> AdminOutput:
        """
        Update the details of an admin user.
        :param admin_id: The ID of the user.
        :param username: The new username.
        :param password: The new password.
        :param permissions: The new permissions.
        :return: AdminOutput, the details of the user.
        """
        payload = {}
        if username:
            payload["username"] = username
        if password:
            payload["password"] = password
        if permissions:
            payload["permissions"] = permissions

        return self.put(self.format_url(f"/users/{admin_id}"), self.system_id, output_class=AdminOutput, payload=payload)

    def delete_admin(self, admin_id: str) -> AdminOutput:
        """
        Delete an admin user.
        :param admin_id: The ID of the user.
        :return: AdminOutput, the details of the user.
        """
        return self.delete(self.format_url(f"/users/{admin_id}"), self.system_id, output_class=AdminOutput)

    def get_available_plugins(self, plugin_name: str | None = None) -> PluginCollectionOutput:
        """
        Get a list of all available plugins.
        :param plugin_name: The name of the plugin.
        :return: PluginCollectionOutput, the details of the plugins.
        """
        return self.get(
            self.format_url("/plugins"),
            self.system_id,
            output_class=PluginCollectionOutput,
            query={"query": plugin_name} if plugin_name else None,
        )

    def post_install_plugin_from_zip(self, path_zip: str) -> PluginInstallOutput:
        payload = MultipartPayload()

        with open(path_zip, "rb") as file:
            payload.files = [("file", file_attributes(path_zip, file))]
            result = self.post_multipart(
                self.format_url("/plugins/upload"),
                self.system_id,
                output_class=PluginInstallOutput,
                payload=payload,
            )
        return result

    def post_install_plugin_from_registry(self, url: str) -> PluginInstallFromRegistryOutput:
        """
        Install a new plugin from a registry. The plugin is installed asynchronously.
        :param url: The URL of the plugin.
        :return: PluginInstallFromRegistryOutput, the details of the installation.
        """
        return self.post_json(
            self.format_url("/plugins/upload/registry"),
            self.system_id,
            output_class=PluginInstallFromRegistryOutput,
            payload={"url": url},
        )

    def get_plugins_settings(self) -> PluginsSettingsOutput:
        """
        Get the default settings of all the plugins.
        :return: PluginsSettingsOutput, the details of the settings.
        """
        return self.get(self.format_url("/plugins/settings"), self.system_id, output_class=PluginsSettingsOutput)

    def get_plugin_settings(self, plugin_id: str) -> PluginSettingsOutput:
        """
        Get the default settings of a specific plugin.
        :param plugin_id: The ID of the plugin.
        :return: PluginSettingsOutput, the details of the settings.
        """
        return self.get(
            self.format_url(f"/plugins/settings/{plugin_id}"), self.system_id, output_class=PluginSettingsOutput
        )

    def get_plugin_details(self, plugin_id: str) -> PluginDetailsOutput:
        """
        Get the details of a specific plugin.
        :param plugin_id: The ID of the plugin.
        :return: PluginDetailsOutput, the details of the plugin.
        """
        return self.get(self.format_url(f"/plugins/{plugin_id}"), self.system_id, output_class=PluginDetailsOutput)

    def delete_plugin(self, plugin_id: str) -> PluginDeleteOutput:
        """
        Delete a specific plugin.
        :param plugin_id: The ID of the plugin.
        :return: PluginDeleteOutput, the details of the plugin.
        """
        return self.delete(self.format_url(f"/plugins/{plugin_id}"), self.system_id, output_class=PluginDeleteOutput)

    def put_toggle_plugin(self, plugin_id: str) -> PluginToggleOutput:
        """
        This endpoint toggles a plugin, on a system level
        :param plugin_id: The id of the plugin to toggle
        :return: PluginToggleOutput, the toggled plugin
        """
        return self.put(
            self.format_url(f"/plugins/toggle/{plugin_id}"),
            self.system_id,
            output_class=PluginToggleOutput,
        )
