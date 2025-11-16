from discord.ext import commands

class Info(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command()
    async def about(self, ctx): await ctx.send('WAWA Bot — rebuilt')

async def setup(bot): await bot.add_cog(Info(bot))
