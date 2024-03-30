from bot import bot

from discord.ext import voice_recv
from discord import FFmpegPCMAudio

# Voice Channel Related #
# These should be used for debugging generally #
@bot.command(name='join')
# Commands the bot to join the same channel as the user
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
# Commands the bot to leave their voice channel
async def leave(ctx):
    # Check if the bot is connected to a voice channel
    if ctx.voice_client is None:
        await ctx.send("I'm not connected to a voice channel.")
        return

    # Disconnect the bot from the voice channel
    await ctx.voice_client.disconnect()
    await ctx.send("I've left the voice channel.")


@bot.command(name='play_sample')
# Plays the "audio.wav" file 
# TODO: change the way this works so we're not just hard coding everything to audio.wav
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