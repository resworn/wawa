from discord.ext import commands

class Roles(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command()
    async def giverole(self, ctx, role: str):
        r = discord.utils.get(ctx.guild.roles, name=role)
        if not r: return await ctx.send('Role not found')
        await ctx.author.add_roles(r); await ctx.send('Role given')

async def setup(bot): await bot.add_cog(Roles(bot))
