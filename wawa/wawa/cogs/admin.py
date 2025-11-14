
import discord
from discord.ext import commands
import os
import aiohttp
import sqlite3
from typing import Optional

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def owner_check(self, ctx):
        owner = os.getenv('OWNER_ID')
        if owner and str(ctx.author.id) == str(owner):
            return True
        # also allow server owner as fallback
        try:
            if ctx.guild and ctx.guild.owner_id == ctx.author.id:
                return True
        except Exception:
            pass
        return False

    @commands.command(name='changestatus')
    async def changestatus(self, ctx, *, text: str):
        """Change bot status (owner or server owner only)"""
        if not self.owner_check(ctx):
            return await ctx.send('You are not authorized to change status.')
        await self.bot.change_presence(activity=discord.Game(text))
        await ctx.send(f'Status changed to: {text}')

    @commands.command(name='setavatar')
    async def setavatar(self, ctx, url: Optional[str] = None):
        """Change bot avatar from URL or attachment (owner only)"""
        if not self.owner_check(ctx):
            return await ctx.send('You are not authorized.')
        image_bytes = None
        if url:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    if r.status != 200:
                        return await ctx.send('Failed to download image.')
                    image_bytes = await r.read()
        elif ctx.message.attachments:
            image_bytes = await ctx.message.attachments[0].read()
        else:
            return await ctx.send('Provide an image URL or attach an image.')
        try:
            await self.bot.user.edit(avatar=image_bytes)
            await ctx.send('Avatar updated successfully.')
        except Exception as e:
            await ctx.send(f'Failed to update avatar: {e}')

    @commands.command(name='setbanner')
    async def setbanner(self, ctx, url: Optional[str] = None):
        """Change bot banner (owner only) — may require Nitro privileges"""
        if not self.owner_check(ctx):
            return await ctx.send('You are not authorized.')
        image_bytes = None
        if url:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    if r.status != 200:
                        return await ctx.send('Failed to download image.')
                    image_bytes = await r.read()
        elif ctx.message.attachments:
            image_bytes = await ctx.message.attachments[0].read()
        else:
            return await ctx.send('Provide an image URL or attach an image.')
        try:
            await self.bot.user.edit(banner=image_bytes)
            await ctx.send('Banner updated successfully.')
        except Exception as e:
            await ctx.send(f'Failed to update banner: {e}')

    @commands.command(name='setbalance')
    async def setbalance(self, ctx, member: discord.Member, amount: int):
        if not self.owner_check(ctx):
            return await ctx.send('You are not authorized.')
        db = os.path.join(os.path.dirname(__file__), '..', 'data', 'economy.db')
        db = os.path.normpath(db)
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('UPDATE users SET wallet = ? WHERE user_id = ?', (amount, member.id))
        conn.commit()
        conn.close()
        await ctx.send(f'Set wallet of {member.display_name} to ${amount:,}.')

    @commands.command(name='leaderboard')
    async def leaderboard(self, ctx, top: int = 10):
        db = os.path.join(os.path.dirname(__file__), '..', 'data', 'economy.db')
        db = os.path.normpath(db)
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('SELECT user_id, wallet+bank as total FROM users ORDER BY total DESC LIMIT ?', (top,))
        rows = c.fetchall()
        conn.close()
        out = []
        for idx, row in enumerate(rows):
            out.append(f"{idx+1}. <@{row[0]}> — ${row[1]:,}")
        await ctx.send('\n'.join(out) or 'No users yet.')

    @commands.command(name='shop')
    async def shop(self, ctx):
        # simple static shop
        items = [ ('VIP', 5000), ('Lucky Charm', 1000), ('Framed Title', 2500) ]
        desc = '\n'.join([f"{i+1}. {name} — ${price:,}" for i, (name, price) in enumerate(items)])
        await ctx.send(f"Shop items:\n{desc}")

async def setup(bot):
    await bot.add_cog(Admin(bot))
