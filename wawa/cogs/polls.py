from discord.ext import commands

class Polls(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command()
    async def poll(self, ctx, *, question): m = await ctx.send(f'Poll: {question}'); await m.add_reaction('👍'); await m.add_reaction('👎')

async def setup(bot): await bot.add_cog(Polls(bot))
