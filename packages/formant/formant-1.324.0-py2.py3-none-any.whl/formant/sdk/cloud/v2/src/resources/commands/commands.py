
from formant.sdk.cloud.v2.src.resources.resources import Resources
from . import Command, CommandQuery, Response, command_controller_post, command_controller_query

class Commands(Resources):

    def create(self, command: Command):
        'Creates a command'
        client = self._get_client()
        response: Response[Command] = command_controller_post.sync_detailed(client=client, json_body=command)
        return response

    async def create_async(self, command: Command):
        'Creates a command'
        client = self._get_client()
        response: Response[Command] = (await command_controller_post.asyncio_detailed(client=client, json_body=command))
        return response

    def query(self, command_query: CommandQuery):
        'Query undelivered commands by device ID'
        client = self._get_client()
        response: Response[CommandQuery] = command_controller_query.sync_detailed(client=client, json_body=command_query)
        return response

    async def query_async(self, command_query: CommandQuery):
        'Query undelivered commands by device ID'
        client = self._get_client()
        response: Response[CommandQuery] = (await command_controller_query.asyncio_detailed(client=client, json_body=command_query))
        return response
