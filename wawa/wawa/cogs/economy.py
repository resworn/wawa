
import sqlite3
import threading
import time
import math
import random
from discord.ext import commands
import discord

DB_PATH = "wawa/data/economy.db"
DB_LOCK = threading.Lock()

# Ensure data folder exists
import os
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def with_db(func):
    """Decorator to provide a safe sqlite connection to functions."""
    def wrapper(*args, **kwargs):
        with DB_LOCK:
            conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level='DEFERRED')
            conn.row_factory = sqlite3.Row
            try:
                result = func(conn, *args, **kwargs)
                conn.commit()
                return result
            except Exception as e:
                conn.rollback()
                raise
            finally:
                conn.close()
    return wrapper

@with_db
def init_db(conn):
    c = conn.cursor()
    # users: id (discord id), wallet (liquid), bank (savings), credit_score (300-850)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        wallet INTEGER NOT NULL DEFAULT 0,
        bank INTEGER NOT NULL DEFAULT 0,
        credit_score INTEGER NOT NULL DEFAULT 600,
        created_at INTEGER NOT NULL
    )''')

    # loans: id, user_id, principal, outstanding, interest_rate (annual %), created_at, due_at, status
    c.execute('''CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        principal INTEGER,
        outstanding INTEGER,
        interest_rate REAL,
        term_days INTEGER,
        created_at INTEGER,
        due_at INTEGER,
        status TEXT DEFAULT 'active'
    )''')

    # credit_cards: id, user_id, limit, balance, apr, min_payment_percent, last_statement
    c.execute('''CREATE TABLE IF NOT EXISTS credit_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        card_limit INTEGER,
        balance INTEGER,
        apr REAL,
        min_payment_percent REAL DEFAULT 0.02,
        created_at INTEGER
    )''')

    # transactions: id, user_id, type, amount, metadata, created_at
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        amount INTEGER,
        metadata TEXT,
        created_at INTEGER
    )''')
    conn.commit()

# simple helpers
def now_ts():
    return int(time.time())

def moneyfmt(amount: int) -> str:
    return f"${amount:,}"

# Business logic
@with_db
def ensure_user(conn, user_id: int):
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row:
        return row
    c.execute("INSERT INTO users (user_id, wallet, bank, credit_score, created_at) VALUES (?, ?, ?, ?, ?)", (user_id, 100, 0, 600, now_ts()))
    conn.commit()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return c.fetchone()

@with_db
def get_balance(conn, user_id: int):
    c = conn.cursor()
    c.execute("SELECT wallet, bank FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        row = ensure_user(user_id)
        return row["wallet"], row["bank"]
    return row["wallet"], row["bank"]

@with_db
def change_wallet(conn, user_id: int, delta: int):
    c = conn.cursor()
    ensure_user(user_id)
    c.execute("UPDATE users SET wallet = wallet + ? WHERE user_id = ?", (delta, user_id))
    c.execute("SELECT wallet FROM users WHERE user_id = ?", (user_id,))
    val = c.fetchone()["wallet"]
    c.execute("INSERT INTO transactions (user_id, type, amount, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
              (user_id, "wallet_change", delta, "", now_ts()))
    return val

@with_db
def change_bank(conn, user_id: int, delta: int):
    c = conn.cursor()
    ensure_user(user_id)
    c.execute("UPDATE users SET bank = bank + ? WHERE user_id = ?", (delta, user_id))
    c.execute("SELECT bank FROM users WHERE user_id = ?", (user_id,))
    val = c.fetchone()["bank"]
    c.execute("INSERT INTO transactions (user_id, type, amount, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
              (user_id, "bank_change", delta, "", now_ts()))
    return val

@with_db
def create_loan(conn, user_id: int, amount: int, interest_rate: float, term_days: int):
    c = conn.cursor()
    now = now_ts()
    due = now + term_days * 24 * 3600
    c.execute("INSERT INTO loans (user_id, principal, outstanding, interest_rate, term_days, created_at, due_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (user_id, amount, amount, interest_rate, term_days, now, due, "active"))
    loan_id = c.lastrowid
    c.execute("INSERT INTO transactions (user_id, type, amount, metadata, created_at) VALUES (?, ?, ?, ?, ?)", (user_id, "loan_disburse", amount, f"loan_id={loan_id}", now))
    return loan_id

@with_db
def get_loans(conn, user_id: int):
    c = conn.cursor()
    c.execute("SELECT * FROM loans WHERE user_id = ? AND status = 'active'", (user_id,))
    return c.fetchall()

@with_db
def pay_loan(conn, user_id: int, loan_id: int, amount: int):
    c = conn.cursor()
    c.execute("SELECT * FROM loans WHERE id = ? AND user_id = ? AND status = 'active'", (loan_id, user_id))
    loan = c.fetchone()
    if not loan:
        raise Exception("No active loan found")
    pay = min(amount, loan["outstanding"])
    c.execute("UPDATE loans SET outstanding = outstanding - ? WHERE id = ?", (pay, loan_id))
    c.execute("INSERT INTO transactions (user_id, type, amount, metadata, created_at) VALUES (?, ?, ?, ?, ?)", (user_id, "loan_payment", -pay, f"loan_id={loan_id}", now_ts()))
    # if outstanding <= 0 set status closed
    c.execute("SELECT outstanding FROM loans WHERE id = ?", (loan_id,))
    out = c.fetchone()["outstanding"]
    if out <= 0:
        c.execute("UPDATE loans SET status = 'closed' WHERE id = ?", (loan_id,))
    return out

@with_db
def open_credit_card(conn, user_id: int, limit: int, apr: float):
    c = conn.cursor()
    now = now_ts()
    c.execute("INSERT INTO credit_cards (user_id, card_limit, balance, apr, created_at) VALUES (?, ?, ?, ?, ?)", (user_id, limit, 0, apr, now))
    cid = c.lastrowid
    c.execute("INSERT INTO transactions (user_id, type, amount, metadata, created_at) VALUES (?, ?, ?, ?, ?)", (user_id, "open_card", 0, f"card_id={cid}", now))
    return cid

@with_db
def charge_card(conn, user_id: int, card_id: int, amount: int):
    c = conn.cursor()
    c.execute("SELECT * FROM credit_cards WHERE id = ? AND user_id = ?", (card_id, user_id))
    card = c.fetchone()
    if not card:
        raise Exception("Card not found")
    if card["balance"] + amount > card["card_limit"]:
        raise Exception("Charge would exceed limit")
    c.execute("UPDATE credit_cards SET balance = balance + ? WHERE id = ?", (amount, card_id))
    c.execute("INSERT INTO transactions (user_id, type, amount, metadata, created_at) VALUES (?, ?, ?, ?, ?)", (user_id, "card_charge", -amount, f"card_id={card_id}", now_ts()))
    return True

@with_db
def pay_card(conn, user_id: int, card_id: int, amount: int):
    c = conn.cursor()
    c.execute("SELECT * FROM credit_cards WHERE id = ? AND user_id = ?", (card_id, user_id))
    card = c.fetchone()
    if not card:
        raise Exception("Card not found")
    pay = min(amount, card["balance"])
    c.execute("UPDATE credit_cards SET balance = balance - ? WHERE id = ?", (pay, card_id))
    c.execute("INSERT INTO transactions (user_id, type, amount, metadata, created_at) VALUES (?, ?, ?, ?, ?)", (user_id, "card_payment", pay, f"card_id={card_id}", now_ts()))
    return card["balance"] - pay

@with_db
def get_credit_score(conn, user_id: int):
    c = conn.cursor()
    c.execute("SELECT credit_score FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        row = ensure_user(user_id)
        return row["credit_score"]
    return row["credit_score"]

@with_db
def adjust_credit_score(conn, user_id: int, delta: int):
    c = conn.cursor()
    ensure_user(user_id)
    c.execute("UPDATE users SET credit_score = credit_score + ? WHERE user_id = ?", (delta, user_id))
    c.execute("SELECT credit_score FROM users WHERE user_id = ?", (user_id,))
    return c.fetchone()["credit_score"]

# Initialize DB on import
init_db()

class Economy(commands.Cog):
    """Prefix-only economy cog: wallet, bank, gamble, loans, credit card"""
    def __init__(self, bot):
        self.bot = bot

    # Register / ensure user exists
    @commands.command(name='register')
    async def register(self, ctx):
        ensure_user(ctx.author.id)
        await ctx.send(f"{ctx.author.mention}, your account has been registered. You start with {moneyfmt(100)} in your wallet.")

    @commands.command(name='bal', aliases=['balance'])
    async def bal(self, ctx, member: discord.Member = None):
        user = member or ctx.author
        wallet, bank = get_balance(user.id)
        await ctx.send(f"**{user.display_name}** — Wallet: {moneyfmt(wallet)} | Bank: {moneyfmt(bank)}")

    @commands.command(name='deposit')
    async def deposit(self, ctx, amount: int):
        if amount <= 0:
            return await ctx.send('Amount must be positive.')
        ensure_user(ctx.author.id)
        wallet, bank = get_balance(ctx.author.id)
        if wallet < amount:
            return await ctx.send('Not enough funds in wallet.')
        change_wallet(ctx.author.id, -amount)
        change_bank(ctx.author.id, amount)
        await ctx.send(f'Deposited {moneyfmt(amount)} to bank.')

    @commands.command(name='withdraw')
    async def withdraw(self, ctx, amount: int):
        if amount <= 0:
            return await ctx.send('Amount must be positive.')
        ensure_user(ctx.author.id)
        wallet, bank = get_balance(ctx.author.id)
        if bank < amount:
            return await ctx.send('Not enough funds in bank.')
        change_bank(ctx.author.id, -amount)
        change_wallet(ctx.author.id, amount)
        await ctx.send(f'Withdrew {moneyfmt(amount)} from bank.')

    @commands.command(name='transfer')
    async def transfer(self, ctx, member: discord.Member, amount: int):
        if amount <= 0:
            return await ctx.send('Amount must be positive.')
        if member.bot:
            return await ctx.send('You cannot transfer to bots.')
        ensure_user(ctx.author.id)
        ensure_user(member.id)
        wallet, _ = get_balance(ctx.author.id)
        if wallet < amount:
            return await ctx.send('Not enough funds.')
        change_wallet(ctx.author.id, -amount)
        change_wallet(member.id, amount)
        await ctx.send(f'Transferred {moneyfmt(amount)} to {member.display_name}.')

    @commands.command(name='gamble')
    async def gamble(self, ctx, amount: int):
        """Gamble with house edge and credit score impact. Returns wins/losses."""
        if amount <= 0:
            return await ctx.send('Amount must be positive.')

        ensure_user(ctx.author.id)
        wallet, _ = get_balance(ctx.author.id)
        if wallet < amount:
            return await ctx.send('Not enough funds.')
        # House edge based on credit score: better credit slightly reduces house edge
        credit = get_credit_score(ctx.author.id)
        house_edge = 0.05  # base 5%
        # reduce edge by up to 2% if credit high
        house_edge -= min(0.02, (credit - 600) / 2500.0)
        # simple roulette-like outcome: 48% win double, 1% jackpot 10x, else lose
        r = random.random()
        win_amount = 0
        if r < 0.01:
            win_amount = int(amount * 9)  # net +9x
        elif r < 0.49 - house_edge:
            win_amount = int(amount * 1.0)  # net +1x (double)
        else:
            win_amount = -amount
        # apply result
        change_wallet(ctx.author.id, win_amount)
        # small credit adjustment: wins slightly up, losses slightly down
        credit_delta = 1 if win_amount > 0 else -2
        adjust_credit_score(ctx.author.id, credit_delta)
        if win_amount > 0:
            await ctx.send(f"You won {moneyfmt(win_amount)}!")
        else:
            await ctx.send(f"You lost {moneyfmt(abs(win_amount))}.")

    @commands.command(name='loan')
    async def loan(self, ctx, amount: int):
        if amount <= 0:
            return await ctx.send('Amount must be positive.')
        ensure_user(ctx.author.id)
        credit = get_credit_score(ctx.author.id)
        # max loan determined by credit score: base multiplier
        max_loan = max(100, int(credit * 2))
        if amount > max_loan:
            return await ctx.send(f'Loan denied. Maximum allowed based on credit is {moneyfmt(max_loan)}.')
        # interest rate depends on credit
        base_apr = 0.25  # 25% annual for low-credit
        apr = max(0.05, base_apr - (credit - 300) / 2000.0)  # better credit -> lower apr
        term_days = 30  # 30-day loan
        loan_id = create_loan(ctx.author.id, amount, apr, term_days)
        change_wallet(ctx.author.id, amount)
        await ctx.send(f'Loan approved (id {loan_id}). Disbursed {moneyfmt(amount)} at APR {apr*100:.1f}% for {term_days} days.')

    @commands.command(name='loans')
    async def loans(self, ctx):
        ensure_user(ctx.author.id)
        loans = get_loans(ctx.author.id)
        if not loans:
            return await ctx.send('You have no active loans.')
        msgs = []
        for l in loans:
            msgs.append(f"ID:{l['id']} Outstanding:{moneyfmt(l['outstanding'])} Due:{time.ctime(l['due_at'])}")
        await ctx.send("\n".join(msgs))

    @commands.command(name='payloan')
    async def payloan(self, ctx, loan_id: int, amount: int):
        if amount <= 0:
            return await ctx.send('Amount must be positive.')
        ensure_user(ctx.author.id)
        wallet, _ = get_balance(ctx.author.id)
        if wallet < amount:
            return await ctx.send('Not enough funds in wallet.')
        remaining = pay_loan(ctx.author.id, loan_id, amount)
        change_wallet(ctx.author.id, -amount)
        await ctx.send(f'Paid {moneyfmt(amount)} towards loan {loan_id}. Remaining outstanding: {moneyfmt(remaining)}')

    @commands.command(name='opencard')
    async def opencard(self, ctx):
        ensure_user(ctx.author.id)
        credit = get_credit_score(ctx.author.id)
        # determine limit and apr based on credit
        limit = max(200, int(credit * 1.5))
        apr = max(0.08, 0.30 - (credit - 300) / 1000.0)
        cid = open_credit_card(ctx.author.id, limit, apr)
        await ctx.send(f"Opened a credit card (id {cid}) with limit {moneyfmt(limit)} and APR {apr*100:.1f}%")

    @commands.command(name='cardcharge')
    async def cardcharge(self, ctx, card_id: int, amount: int):
        if amount <= 0:
            return await ctx.send('Amount must be positive.')
        ensure_user(ctx.author.id)
        try:
            charge_card(ctx.author.id, card_id, amount)
        except Exception as e:
            return await ctx.send(f"Charge failed: {e}")
        await ctx.send(f"Charged {moneyfmt(amount)} to card {card_id}.")

    @commands.command(name='paycard')
    async def paycard(self, ctx, card_id: int, amount: int):
        if amount <= 0:
            return await ctx.send('Amount must be positive.')
        ensure_user(ctx.author.id)
        wallet, _ = get_balance(ctx.author.id)
        if wallet < amount:
            return await ctx.send('Not enough funds in wallet.')
        remaining = pay_card(ctx.author.id, card_id, amount)
        change_wallet(ctx.author.id, -amount)
        await ctx.send(f"Paid {moneyfmt(amount)} to card {card_id}. Remaining balance: {moneyfmt(remaining)}")

    @commands.command(name='credit')
    async def credit(self, ctx):
        ensure_user(ctx.author.id)
        score = get_credit_score(ctx.author.id)
        await ctx.send(f"Your credit score: {score} (300-850)")


@commands.command(name='setbio')
async def setbio(self, ctx, *, text: str):
    """Set your profile bio (stored in DB)"""
    ensure_user(ctx.author.id)
    # update bio
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'data', 'economy.db'))
    c = conn.cursor()
    c.execute('UPDATE users SET bio = ? WHERE user_id = ?', (text, ctx.author.id))
    conn.commit()
    conn.close()
    await ctx.send('Your bio has been updated.')

@commands.command(name='viewbio')
async def viewbio(self, ctx, member: discord.Member = None):
    user = member or ctx.author
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'data', 'economy.db'))
    c = conn.cursor()
    c.execute('SELECT bio FROM users WHERE user_id = ?', (user.id,))
    row = c.fetchone()
    conn.close()
    bio = row[0] if row else ''
    await ctx.send(f"**{user.display_name}**'s bio:\n{bio}")

async def setup(bot):
    await bot.add_cog(Economy(bot))
