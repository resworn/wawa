
import discord
from discord.ext import commands
import json
import os

CONFIG_PATH = "config/config.json"

def load_prefix():
    if not os.path.exists(CONFIG_PATH):
        return ","
    with open(CONFIG_PATH, "r", encoding="utf8") as f:
        data = json.load(f)
    return data.get("prefix", ",")

def save_prefix(prefix):
    with open(CONFIG_PATH, "r", encoding="utf8") as f:
        data = json.load(f)
    data["prefix"] = prefix
    with open(CONFIG_PATH, "w", encoding="utf8") as f:
        json.dump(data, f, indent=4)

class PrefixHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setprefix")
    async def setprefix(self, ctx, prefix: str):
        owner = os.getenv("OWNER_ID")
        if owner and str(ctx.author.id) != str(owner):
            return await ctx.send("You are not authorized.")
        if len(prefix) > 3:
            return await ctx.send("Prefix must be short (1–3 chars).")
        save_prefix(prefix)
        self.bot.command_prefix = prefix
        await ctx.send(f"Prefix updated to **`{prefix}`**")

    @commands.command(name="help")
    async def help(self, ctx):
        prefix = load_prefix()
        embed = discord.Embed(
            title="📘 WAWA Help",
            description=f"Prefix: **`{prefix}`**",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="💰 Economy",
            value=(
                f"`{prefix}register`, `{prefix}bal`, `{prefix}deposit`, `{prefix}withdraw`,
"
                f"`{prefix}transfer @user amount`, `{prefix}gamble amount`,
"
                f"`{prefix}loan amount`, `{prefix}loans`, `{prefix}payloan id amount`,
"
                f"`{prefix}opencard`, `{prefix}cardcharge id amount`, `{prefix}paycard`,
"
                f"`{prefix}credit`, `{prefix}setbio`, `{prefix}viewbio`"
            ),
            inline=False
        )
        embed.add_field(
            name="🎶 Music",
            value=(
                f"`{prefix}join`, `{prefix}leave`, `{prefix}yt <link>`,
"
                f"`{prefix}pause`, `{prefix}resume`, `{prefix}volume <0-200>`"
            ),
            inline=False
        )
        embed.add_field(
            name="🛠 Admin",
            value=(
                f"`{prefix}changestatus`, `{prefix}setavatar`, `{prefix}setbanner`,
"
                f"`{prefix}setbalance`, `{prefix}leaderboard`, `{prefix}shop`,
"
                f"`{prefix}setprefix`"
            ),
            inline=False
        )
        embed.set_footer(text="WAWA Bot — Prefix Command System")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PrefixHelp(bot))
