WAWA — Railway deployment instructions (Python 3.12)

1. Sign in to https://railway.app
2. Create a new project -> Empty Project -> Empty Service -> Upload
3. Upload this ZIP (wawa_railway_final.zip)
4. After upload, go to Project -> Settings -> Variables and add:
   - BOT_TOKEN (your bot token)
   - OWNER_ID (your Discord user id)
   - DEV_GUILD_ID (optional)
5. Deploy: Railway will build using the included Dockerfile and start the worker.
6. For persistent storage: migrate SQLite to a managed DB or use Railway's persistent volume options.
