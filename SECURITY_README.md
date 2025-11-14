SECURITY NOTICE — IMPORTANT
==================================
You pasted your bot token into the chat earlier. That token is now exposed and MUST be rotated immediately.

Steps to rotate (Discord Developer Portal):
1. Go to https://discord.com/developers/applications
2. Select your application -> Bot -> Click 'Regenerate' on the token section.
3. Copy the new token and NEVER paste it publicly or commit it to GitHub.
4. In Railway (or your host), update the environment variable BOT_TOKEN with the new token.

This ZIP intentionally DOES NOT include your real token. It contains a .env.example placeholder.
