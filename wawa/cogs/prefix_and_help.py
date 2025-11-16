import discord, os
from discord.ext import commands
class PrefixHelp(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command(name='help')
    async def help(self, ctx):
        prefix = os.getenv('COMMAND_PREFIX', ',')
        embed = discord.Embed(title='WAWA Help', description=f'Prefix: `{prefix}`')
        embed.add_field(name='General', value=f'`{prefix}ping` `{prefix}about`', inline=False)
        embed.add_field(name='Economy', value=f'`{prefix}bal` `{prefix}deposit` `{prefix}withdraw` `{prefix}gamble`', inline=False)
        await ctx.send(embed=embed)

async def setup(bot): await bot.add_cog(PrefixHelp(bot))
