import os
import datetime
import time
import asyncio
from dotenv import load_dotenv
load_dotenv()  # Load the env here so other imports can use it

import discord
from discord.ext import commands, voice_recv
from discord import FFmpegPCMAudio

from gpt import ask_gpt
from gcpsink import GcpSink
from vvapi import convert_to_audio

# Load environment variables
TOKEN = os.getenv('DISCORD_TOKEN')

# Intents stuff
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.voice_states = True  # Necessary for the bot to join voice channels

# Bot setup
bot = commands.Bot(command_prefix='!', intents=intents)
# We maintain a separate gcp_sink for each guild_id the bot is in.
# We create the sink whenever the user connects to a voice channel.
# Could probably destroy the sink when the user disconnects.
gcp_sinks = {}

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

# Messaging Related #
@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command(name='chat')
async def chat(ctx, *, message: str):  # The '*' indicates that 'message' will consume the rest of the command input
    # Call the ask_gpt function with the message
    gpt_response = await ask_gpt(message)

    # TODO: This is mega messed up LOL
    # Currently, "convert_to_audio" actually saves the converted text
    # as a file, and plays the file. The file is always hard-coded as
    # audio.wav, which is what play_sample is hard-coded to play
    # X D
    convert_to_audio(gpt_response)
    await ctx.invoke(bot.get_command('play_sample'))

    # Send the response back to the user
    await ctx.send(gpt_response)


# Voice Channel Related #
@bot.command(name='join')
async def join(ctx):
    # Check if the command issuer is connected to a voice channel
    if ctx.author.voice is None:
        await ctx.send("You are not connected to a voice channel.")
        return

    # Get the voice channel of the command issuer
    channel = ctx.author.voice.channel

    # Check if the bot is already connected to a voice channel
    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(channel)  # Move the bot to the new channel
    else:
        await channel.connect(cls=voice_recv.VoiceRecvClient)  # Connect the bot to the channel

    await ctx.send(f"Joined {channel.name}")

@bot.command(name='leave')
async def leave(ctx):
    # Check if the bot is connected to a voice channel
    if ctx.voice_client is None:
        await ctx.send("I'm not connected to a voice channel.")
        return

    # Disconnect the bot from the voice channel
    await ctx.voice_client.disconnect()
    await ctx.send("I've left the voice channel.")

@bot.command(name='play_sample')
async def play_sample(ctx):
    # Check if the bot is connected to a voice channel
    if ctx.voice_client is None:
        await ctx.send("I am not connected to a voice channel.")
        return
    
    # Check if the bot is already playing audio
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    
    # Specify the path to your audio file
    audio_source = FFmpegPCMAudio('audio.wav')
    
    # Play the audio
    ctx.voice_client.play(audio_source, after=lambda e: print(f'Playback error: {e}') if e else None)
    await ctx.send("Now playing: audio.wav")

@bot.command(name='listen')
async def listen(ctx):
    if ctx.voice_client is None:
        await ctx.send("I am not connected to a voice channel.")
        return
    
    voice_client = ctx.voice_client
    voice_client.sink = gcp_sinks.get(ctx.guild_id)

async def schedule_response_to_audio(transcription_result, guild_id):
    await respond_to_audio(transcription_result, guild_id)

@bot.event
async def on_voice_state_update(member, before, after):
    print("voice update")
    # Don't do anything if the update was triggered by the bot.
    if member == bot.user:
        print("bot update")
        return

    if before.channel and not after.channel:
        # TODO: Not sure how to make the bot leave a channel on an event
        voice_client = member.guild.voice_client
        await voice_client.disconnect()

    # Join the voice channel and start recording if user joins
    if not before.channel and after.channel:
        if not member.guild.voice_client or after.channel != member.guild.voice_client.channel:
            voice_channel = after.channel
            voice_client = await voice_channel.connect(cls=voice_recv.VoiceRecvClient)

        if member.guild.id not in gcp_sinks:
            gcp_sinks[member.guild.id] = GcpSink(schedule_response_to_audio, member.guild.id)

        # Play a block of silence?
        audio_source = FFmpegPCMAudio('250ms-silence.mp3')
        voice_client.play(audio_source, after=lambda e: print(f'Playback error: {e}') if e else None)

        print(f"[{datetime.datetime.now().isoformat()}]", "Recording...")
        member.guild.voice_client.listen(gcp_sinks.get(member.guild.id))
        # Start watching for end of audio
        asyncio.create_task(gcp_sinks.get(member.guild.id).monitor_buffer())

async def respond_to_audio(transcription_result, guild_id):
    print(f"Responding to message: {transcription_result}")
    bot.get_channel
    gpt_response = await ask_gpt(transcription_result)
    convert_to_audio(gpt_response)

    # Play the audio
    print("Playing response back")
    guild = bot.get_guild(guild_id)
    voice_client = guild.voice_client
    audio_source = FFmpegPCMAudio('audio.wav')  # TODO FIX AUDIO.WAV
    voice_client.play(audio_source, after=lambda e: print(f'Playback error: {e}') if e else None)

    # Send the transcription message as a message
    channel = discord.utils.get(guild.text_channels, name='konbini-test')
    await channel.send(f"you: {transcription_result}")
    await channel.send(f"konbini-bot: {gpt_response}")



# Run the bot
bot.run(TOKEN)
