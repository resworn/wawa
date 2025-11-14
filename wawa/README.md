# WAWA (modernized)

This is a modernized fork of your bot adapted for Python 3.12 and discord.py 2.x.

## Quickstart

1. Install Python 3.12 (recommended).
2. Create and activate a venv:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```
3. Copy `.env.example` to `.env` and fill in your tokens and DB credentials.
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run:
   ```bash
   python main.py
   ```

## Notes
- Music cog uses `yt-dlp` compatible backend.
- Application commands can be synced to a development guild using `DEV_GUILD_ID` in .env.
