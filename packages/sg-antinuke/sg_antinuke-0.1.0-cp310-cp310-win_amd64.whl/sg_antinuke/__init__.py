"""
sg_antinuke: Reusable Anti-Nuke Discord cog

Usage options:
- Load as an extension: bot.load_extension('sg_antinuke')
- Or import the cog: from sg_antinuke import AntiNuke
"""
try:
    from .antinuke import AntiNuke, AntiNukeConfig, RedisCache, RateLimiter
except ImportError:
    pass

__all__ = [
    "AntiNuke",
    "AntiNukeConfig",
    "RedisCache",
    "RateLimiter",
]


async def setup(bot):
    """discord.py extension entry point.

    Adds the cog and wires up an on_ready listener to start background tasks.
    """
    cog = AntiNuke(bot)
    await bot.add_cog(cog)

    async def _on_ready():
        try:
            await cog.start_antinuke_tasks()
        except Exception:
            # Avoid crashing user bots if startup fails
            import logging
            logging.getLogger('sg_antinuke').exception("Failed to start AntiNuke tasks")

    # Multiple listeners are supported; this won't replace user handlers
    bot.add_listener(_on_ready, name="on_ready")
