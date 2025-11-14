# main.py — WaWa (modernized)
import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
import discord
from discord.ext import commands
from pydantic import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    BOT_TOKEN: str
    COMMAND_PREFIX: str = ","
    BOT_STATUS: str = "WAWA on patrol"
    DEV_GUILD_ID: int | None = None

    class Config:
        env_file = ".env"

settings = Settings()

LOG = logging.getLogger("wawa")
LOG.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s:%(name)s: %(message)s"))
LOG.addHandler(handler)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class WaWaBot(commands.Bot):
    def __init__(self, *, settings: Settings):
        super().__init__(
            command_prefix=settings.COMMAND_PREFIX,
            intents=intents,
            help_command=None,
        )
        self.settings = settings
        self.start_time = None

    async def setup_hook(self):
        LOG.info("Loading cogs...")
        base = Path("./wawa/cogs")
        if base.exists():
            for fn in sorted(base.iterdir()):
                if fn.suffix == ".py":
                    name = f"wawa.cogs.{fn.stem}"
                    try:
                        await self.load_extension(name)
                        LOG.info("Loaded %s", name)
                    except Exception as e:
                        LOG.exception("Failed to load %s: %s", name, e)

        dev_guild_id = os.getenv("DEV_GUILD_ID") or os.getenv("DEV_GUILD")
        if dev_guild_id:
            try:
                await self.tree.sync(guild=discord.Object(id=int(dev_guild_id)))
                LOG.info("Synced application commands to guild %s", dev_guild_id)
            except Exception:
                LOG.exception("Failed to sync guild commands")

    async def on_ready(self):
        self.start_time = asyncio.get_event_loop().time()
        LOG.info("Logged in as %s (id: %s)", self.user, self.user.id)

        avatar_path = Path("./wawa/assets/avatar.jpg")
        if avatar_path.exists():
            try:
                with avatar_path.open("rb") as f:
                    await self.user.edit(avatar=f.read())
            except Exception:
                LOG.exception("Failed to update avatar")

        await self.change_presence(activity=discord.Game(settings.BOT_STATUS))


# ---------- Background tasks: interest accrual & loan checker ----------
import asyncio

async def apply_daily_interest(bot):
    """Apply interest to outstanding loans once per day (runs in background)."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            # trigger by importing managers database code
            from wawa.managers import database as md
            # connect to sqlite economy DB and apply simple interest accrual
            import sqlite3, time, math, os
            db = os.path.join(os.path.dirname(__file__), 'wawa', 'data', 'economy.db')
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            now = int(time.time())
            # for each active loan, apply daily interest: outstanding += outstanding * (apr/365)
            cur.execute("SELECT id, outstanding, interest_rate FROM loans WHERE status='active'")
            loans = cur.fetchall()
            for lid, out, apr in loans:
                if apr is None:
                    continue
                daily = out * (apr / 365.0)
                add = int(round(daily))
                if add > 0:
                    cur.execute("UPDATE loans SET outstanding = outstanding + ? WHERE id = ?", (add, lid))
                    cur.execute("INSERT INTO transactions (user_id, type, amount, metadata, created_at) VALUES (?, ?, ?, ?, ?)", (None, 'loan_interest', add, f'loan_id={lid}', now))
            conn.commit()
            conn.close()
        except Exception:
            pass
        await asyncio.sleep(60 * 60 * 24)  # sleep one day

async def check_overdue_loans(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            import sqlite3, time, os
            db = os.path.join(os.path.dirname(__file__), 'wawa', 'data', 'economy.db')
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            now = int(time.time())
            # mark overdue loans and optionally adjust credit scores
            cur.execute("SELECT id, user_id, outstanding, due_at FROM loans WHERE status='active' AND due_at < ?", (now,))
            rows = cur.fetchall()
            for lid, uid, out, due in rows:
                # mark as overdue/closed and penalize credit score
                cur.execute("UPDATE loans SET status='overdue' WHERE id = ?", (lid,))
                # penalize credit by -20
                cur.execute("UPDATE users SET credit_score = credit_score - ? WHERE user_id = ?", (20, uid))
                cur.execute("INSERT INTO transactions (user_id, type, amount, metadata, created_at) VALUES (?, ?, ?, ?, ?)", (uid, 'loan_overdue_penalty', -20, f'loan_id={lid}', now))
            conn.commit()
            conn.close()
        except Exception:
            pass
        await asyncio.sleep(60 * 60)  # check hourly

# helper: owner-only check by env OWNER_ID or DEV_GUILD_ID
def is_owner(ctx):
    import os
    try:
        owner = os.getenv('OWNER_ID')
        if owner and str(ctx.author.id) == str(owner):
            return True
    except Exception:
        pass
    return False


if __name__ == "__main__":
    bot = WaWaBot(settings=settings)
    try:
        bot.run(settings.BOT_TOKEN)
    except KeyboardInterrupt:
        LOG.info("Shutting down...")
