import os
import datetime
import time
import asyncio
from dotenv import load_dotenv
load_dotenv()  # Load the env here so other imports can use it

import discord
from discord.ext import commands, voice_recv
from discord import FFmpegPCMAudio, File

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

# Keep session information here
# Key: user, value: information about session
sessions = {}

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.command(name='chat')
async def chat(ctx, *, message: str):  # The '*' indicates that 'message' will consume the rest of the command input
    # Call the ask_gpt function with the message
    gpt_response = await ask_gpt(message)

    # TODO: This is mega messed up LOL
    # ask_gpt will write an audio file to audio.wav. The bot plays that audio back here.
    convert_to_audio(gpt_response)
    await ctx.invoke(bot.get_command('play_sample'))

    # Print the response in the chat
    await ctx.send(gpt_response)


@bot.command(name='listen')
async def listen(ctx):
    if ctx.voice_client is None:
        await ctx.send("I am not connected to a voice channel.")
        return
    
    voice_client = ctx.voice_client
    voice_client.sink = gcp_sinks.get(ctx.guild_id)

async def schedule_response_to_audio(transcription_result, guild_id):
    await respond_to_audio(transcription_result, guild_id)

@bot.command(name='scenario')
async def build_scenario(ctx):
    # The bot will ask the user for various input to build the scenario. The user will be able to pick...
    # - The type of scenario (konbini, restaurant order, restaurant reservation...)
    # - Any additional information to set up the scenario.
    # . - Konbini example: what items would you like to purchase?

    scenarios = ['konbini']
    emojis = {}
    konbini_emoji_id = discord.utils.get(ctx.guild.emojis, name='7eleven')
    emojis['konbini'] = konbini_emoji_id

    message = await ctx.send("今日の場面は?\nWhich scenario are we practicing today?")
    await message.add_reaction(emojis.get('konbini'))
    bot.scenario_message_id = message.id

    return

@bot.event
# Reaction handler -- currently this handles the reaction for scenario picking. In the future if we have
# additional reactions, we'll need to break this down into different handlers.
async def on_reaction_add(reaction, user):
    # Ignore the bot's own reactions
    if user == bot.user:
        return

    reaction_handlers = {
        '7eleven': handle_konbini_scenario
    }

    reaction_name = reaction.emoji.name

    handler_function = reaction_handlers.get(reaction_name)
    await handler_function(reaction.message.channel, user)


async def handle_konbini_scenario(channel, user):
    # Ensure you have the correct channel type for sending messages
    if isinstance(channel, discord.TextChannel) or isinstance(channel, discord.DMChannel):
        # Set up images first
        # Path to your image file
        images = {
            'onigiri': 'images/onigiri.jpeg',
            'cup_soup': 'images/cup_soup.jpeg',
            'alcohol': 'images/alcohol.jpeg',
            'chocolate': 'images/chocolate.jpeg',
            'coffee': 'images/coffee.webp',
            'cup_ramen': 'images/cup_ramen.webp',
            'curry_meal': 'images/curry_meal.jpeg',
            'fruit_sando': 'images/fruit_sando.jpeg',
            'potato_chips': 'images/potato_chips.webp',
            'salad': 'images/salad.jpeg',
        }
        image_files = [File(image_path) for image_path in images.values()]

        # Ask the user for what they want
        await channel.send(f"{user.mention}, you've selected the konbini scenario. What items would you like to purchase?",
                           files=image_files)

        items_dict = {
            'A': 'Onigiri',
            'B': 'Seaweed & tofu soup',
            'C': 'Beer',
            'D': 'Chocolate',
            'E': 'Coffee',
            'F': 'Cup ramen',
            'G': 'Katsu curry',
            'H': 'Fruit sandwich',
            'I': 'Potato chips',
            'J': 'Salad'
        }

        items_string = "\n".join([f"{key}: {value}" for key, value in items_dict.items()])
        await channel.send(items_string)

        def check(m):
            # Check that the response is from the same user and channel as the command invocation
            return m.author == user and m.channel == channel

        try:
            # Wait for a response from the user
            message = await bot.wait_for('message', timeout=30.0, check=check)

            # Process the user's response
            selected_items = message.content.upper().split(', ')

            # Build a response based on the selected items
            response = "You've selected:\n"
            for item in selected_items:
                if item in items_dict:
                    response += f"- {items_dict[item]}\n"

            # Send the response to the user
            await channel.send(response)

            channel_name = "#konbini-test"  # Update this eventually
            await channel.send("When are you ready to check out, join the {channel_name} channel.")

        except asyncio.TimeoutError:
            await channel.send("Sorry, you took too long to respond!")

        return


@bot.event
# TODO: Reorganize this event. This was written when we wanted quick testing -- user joins the channel and the
# bot joins immediately to record. In the future, we should make these actions more distinct. This gives us more
# control over the flow of events and timing.
async def on_voice_state_update(member, before, after):
    # Don't do anything if the update was triggered by the bot.
    if member == bot.user:
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
