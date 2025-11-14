import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp as youtube_dl

ytdl_format_options = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues = {}  # guild_id -> asyncio.Queue
        self.current = {}  # guild_id -> current player

    def ensure_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = asyncio.Queue()

    async def connect_voice(self, guild, channel):
        vc = guild.voice_client
        if vc and vc.is_connected():
            await vc.move_to(channel)
            return vc
        return await channel.connect()

    async def _play_next(self, vc, guild_id):
        queue = self.queues.get(guild_id)
        if not queue or queue.empty():
            return
        player = await queue.get()
        vc.play(player, after=lambda e: self.bot.loop.create_task(self._after_play(vc, guild_id, e)))

    async def _after_play(self, vc, guild_id, error):
        if error:
            print('Player error', error)
        await self._play_next(vc, guild_id)

    @app_commands.command(name='join', description='Bot joins your voice channel.')
    async def join(self, interaction: discord.Interaction):
        if interaction.user.voice is None or interaction.user.voice.channel is None:
            return await interaction.response.send_message('You are not in a voice channel.', ephemeral=True)
        channel = interaction.user.voice.channel
        await self.connect_voice(interaction.guild, channel)
        await interaction.response.send_message(f'Joined {channel}')

    @app_commands.command(name='leave', description='Bot leaves voice channel.')
    async def leave(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            await interaction.response.send_message('Disconnected.')
        else:
            await interaction.response.send_message('Not connected.', ephemeral=True)

    @app_commands.command(name='yt', description='Plays a song from a youtube link.')
    async def yt(self, interaction: discord.Interaction, url: str):
        if interaction.user.voice is None or interaction.user.voice.channel is None:
            return await interaction.response.send_message('You are not in a voice channel.', ephemeral=True)
        channel = interaction.user.voice.channel
        vc = interaction.guild.voice_client
        if vc is None:
            vc = await self.connect_voice(interaction.guild, channel)

        self.ensure_queue(interaction.guild.id)
        async with interaction.channel.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            queue = self.queues[interaction.guild.id]
            if vc.is_playing():
                await queue.put(player)
                return await interaction.response.send_message(f'Added to queue: {player.title}')
            vc.play(player, after=lambda e: self.bot.loop.create_task(self._after_play(vc, interaction.guild.id, e)))
        await interaction.response.send_message(f'Now playing: {player.title}')

    @app_commands.command(name='pause', description='Pauses the voice client.')
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message('Paused.')
        else:
            await interaction.response.send_message('Nothing is playing.', ephemeral=True)

    @app_commands.command(name='resume', description='Resumes the voice client.')
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message('Resumed.')
        else:
            await interaction.response.send_message('Nothing is paused.', ephemeral=True)

    @app_commands.command(name='volume', description='Sets playback volume (0-200).')
    async def volume(self, interaction: discord.Interaction, volume: int):
        vc = interaction.guild.voice_client
        if not vc or not hasattr(vc, 'source') or vc.source is None:
            return await interaction.response.send_message('No audio source.', ephemeral=True)
        vc.source.volume = max(0.0, min(2.0, volume / 100))
        await interaction.response.send_message(f'Volume set to {volume}%')
async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
