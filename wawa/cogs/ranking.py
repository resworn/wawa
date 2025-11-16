from discord.ext import commands

class Ranking(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command()
    async def rank(self, ctx): await ctx.send('Ranking placeholder')

async def setup(bot): await bot.add_cog(Ranking(bot))
