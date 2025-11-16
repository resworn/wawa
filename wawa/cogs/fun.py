from discord.ext import commands
import random

class Fun(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command()
    async def coin(self, ctx): await ctx.send(random.choice(['Heads','Tails']))

async def setup(bot): await bot.add_cog(Fun(bot))
