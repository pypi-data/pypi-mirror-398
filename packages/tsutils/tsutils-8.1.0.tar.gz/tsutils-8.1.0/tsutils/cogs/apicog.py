import inspect
import logging
from typing import Any

from redbot.core import commands

logger = logging.getLogger('tsutils.cogs.apicog')

def endpoint(name: str):
    """Tag a method to be registered as an API endpoint"""

    def decorator(func):
        func.__api_endpoint_name__ = name
        return func

    return decorator


def mark_unused_endpoint(bot: commands.Bot, name: str):
    """Remove an endpoint from the API"""
    async def _register_cog_endpoints():
        await bot.wait_until_ready()

        api_cog: Any = bot.get_cog("APICog")
        if not api_cog:
            logger.warning(f"[{self.__class__.__name__}] APICog is not loaded.")
            return
        api_cog.remove_endpoint(name)
    bot.loop.create_task(_register_cog_endpoints())


class CogWithEndpoints(commands.Cog):
    bot: commands.Bot

    async def cog_load(self):
        if hasattr(super(), "cog_load"):
            await super().cog_load()

        if not hasattr(self, "bot"):
            raise AttributeError("Cog does not have a bot attribute.")

        self.bot.loop.create_task(self._register_cog_endpoints())

    async def _register_cog_endpoints(self):
        await self.bot.wait_until_ready()

        api_cog: Any = self.bot.get_cog("APICog")
        if not api_cog:
            logger.warning(
                f"[{self.__class__.__name__}] APICog is not loaded."
            )
            return

        for method_name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method.__func__, "__api_endpoint_name__"):
                endpoint_name = method.__func__.__api_endpoint_name__

                await api_cog.add_endpoint(
                    endpoint_name,
                    self.__class__.__name__,
                    method.__name__
                )

            if hasattr(method.__func__, "__removed_endpoint_name__"):
                endpoint_name = method.__func__.__removed_endpoint_name__

                await api_cog.remove_endpoint(endpoint_name)

