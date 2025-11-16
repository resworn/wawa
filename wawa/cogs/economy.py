from discord.ext import commands
import sqlite3, os, time

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'economy.db')

def init_db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    conn = sqlite3.connect(DB); cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, bank INTEGER DEFAULT 0, credit_score INTEGER DEFAULT 600)')
    cur.execute('CREATE TABLE IF NOT EXISTS loans(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, outstanding INTEGER, interest_rate REAL, due_at INTEGER, status TEXT DEFAULT "active")')
    cur.execute('CREATE TABLE IF NOT EXISTS transactions(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, type TEXT, amount INTEGER, metadata TEXT, created_at INTEGER)')
    conn.commit(); conn.close()

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot; init_db()

    @commands.command()
    async def register(self, ctx):
        conn = sqlite3.connect(DB); cur = conn.cursor()
        cur.execute('INSERT OR IGNORE INTO users(user_id) VALUES (?)',(ctx.author.id,))
        conn.commit(); conn.close()
        await ctx.send('Registered.')

    @commands.command()
    async def bal(self, ctx):
        conn = sqlite3.connect(DB); cur = conn.cursor()
        cur.execute('SELECT balance, bank FROM users WHERE user_id=?',(ctx.author.id,))
        row = cur.fetchone(); conn.close()
        if not row: return await ctx.send('No account. Use register.')
        await ctx.send(f'Wallet: {row[0]} | Bank: {row[1]}')

    @commands.command()
    async def deposit(self, ctx, amount: int):
        conn = sqlite3.connect(DB); cur = conn.cursor()
        cur.execute('UPDATE users SET balance=balance-?, bank=bank+? WHERE user_id=?',(amount, amount, ctx.author.id))
        conn.commit(); conn.close(); await ctx.send('Deposited.')

    @commands.command()
    async def withdraw(self, ctx, amount: int):
        conn = sqlite3.connect(DB); cur = conn.cursor()
        cur.execute('UPDATE users SET bank=bank-?, balance=balance+? WHERE user_id=?',(amount, amount, ctx.author.id))
        conn.commit(); conn.close(); await ctx.send('Withdrawn.')

    @commands.command()
    async def gamble(self, ctx, amount: int):
        import random, sqlite3
        conn = sqlite3.connect(DB); cur = conn.cursor()
        cur.execute('SELECT balance FROM users WHERE user_id=?',(ctx.author.id,)); row = cur.fetchone()
        if not row: return await ctx.send('No account.')
        wallet = row[0]
        if amount>wallet: return await ctx.send('Not enough money.')
        win = random.random() < 0.45
        if win:
            cur.execute('UPDATE users SET balance=balance+? WHERE user_id=?',(amount, ctx.author.id))
            conn.commit(); conn.close(); await ctx.send(f'You won {amount}!')
        else:
            cur.execute('UPDATE users SET balance=balance-? WHERE user_id=?',(amount, ctx.author.id))
            conn.commit(); conn.close(); await ctx.send(f'You lost {amount}.')

async def setup(bot): await bot.add_cog(Economy(bot))
