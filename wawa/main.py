import os, logging, asyncio
from pathlib import Path
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", ",")
BOT_STATUS = os.getenv("BOT_STATUS", "WAWA on patrol")

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("wawa")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class WaWaBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)

    async def setup_hook(self):
        LOG.info("Loading cogs...")
        base = Path(__file__).parent / "cogs"
        if base.exists():
            for fn in sorted(base.iterdir()):
                if fn.suffix == ".py":
                    name = f"wawa.cogs.{fn.stem}"
                    try:
                        await self.load_extension(name)
                        LOG.info('Loaded %s', name)
                    except Exception as e:
                        LOG.exception('Failed to load %s: %s', name, e)

    async def on_ready(self):
        LOG.info('Logged in as %s', self.user)
        await self.change_presence(activity=discord.Game(BOT_STATUS))

if __name__ == '__main__':
    bot = WaWaBot()
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        LOG.exception('Bot failed: %s', e)
