import os
import datetime
import time
import asyncio
import logging
from typing import Dict
from dotenv import load_dotenv
load_dotenv()  # Load the env here so other imports can use it

import discord
from discord.ext import commands, voice_recv
from discord import FFmpegPCMAudio, File, VoiceClient

from gpt import ask_gpt, ask_gpt_session
from gcpsink import GcpSink
from vvapi import BASE_AUDIO_DIR, write_text_to_wav, text_to_hex_audio  # Import vvapi so we can get visiblity into APIs being called
from rvc_api import change_voice
from models.konbini_session import SessionData, KonbiniSession
from audio_utils.audio_converters import hex_to_b64_string, save_b64_string_to_wav, save_hex_to_wav

#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

# We create the sink whenever the user connects to a voice channel, and keep track of the channel.
# TODO: destroy the sink when the user disconnects.
gcp_sinks = {}

# Keep session information here
# Key: channel, value: information about session
# Note that sessions are keyed by channel. This is because within a guild, a bot can only be
# in a single voice channel at a time. Also, each session should start with the bot joining a
# channel, and will end with leaving the channel.
sessions: Dict[str, SessionData] = {}

async def schedule_response_to_audio(transcription_result, voice_client):
    await respond_to_user(transcription_result, voice_client)

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
            selected_item_codes = message.content.upper().split(', ')
            selected_items = ",".join([items_dict.get(item_code) for item_code in selected_item_codes if item_code in items_dict])

            # Build a response based on the selected items
            response = "You've selected:\n"
            for item in selected_item_codes:
                if item in items_dict:
                    response += f"- {items_dict[item]}\n"

            # Send the response to the user
            await channel.send(response)

            channel_name = channel.name
            await channel.send(f"When are you ready to check out, join the {channel_name} channel.")
            await channel.send("Once you join the channel, please wait for konbini-bot to start the conversation!")

            # Create the KonbiniSession to track this session
            konbini_session = KonbiniSession(
                user=user,
                items=[selected_items]
            )
            # TODO: Don't forget to remove the user from sessions when we're done!
            sessions[channel_name] = konbini_session

        except asyncio.TimeoutError:
            await channel.send("Sorry, you took too long to respond!")

        return


@bot.event
async def on_voice_state_update(member, before, after):
    # Don't do anything if the update was triggered by the bot.
    if member == bot.user:
        return

    # Don't do anything if we're not expecting a user.
    try:
        if member.voice.channel.name not in sessions:
            return
    except AttributeError:
        #TODO: logging
        print("User was not in a channel, can't disconnect.")

    # TODO this needs to only trigger if we are expecting the user to join.
    # If the target user joins a channel, then join the channel and start listening
    if not before.channel and after.channel:
        # If voice_client is not properly established... (?)
        #if not user.guild.voice_client or after.channel != user.guild.voice_client.channel:
            #voice_channel = after.channel
            #voice_client = await join_channel(voice_channel)
        voice_channel = after.channel
        for _ in range(3):
            try:
                voice_client = await join_channel(voice_channel)
                break
            except asyncio.TimeoutError:
                print("Timed out waiting for a voice connection. Trying again.")
            except Exception as e:
                print(f"Unknown error: {e}")
                print("Failed to connect to voice channel. Trying again.")
                time.sleep(1)

        # Depending on the session type, do some pre-work
        # TODO: Might be cool to write a .start_session method for each type of sessionData
        session_data = sessions.get(voice_channel.name)
        if session_data.__class__ is KonbiniSession:
            # send the item list and play the result.
            item_list = ",".join(session_data.items)
            item_list_message = f"items: {item_list}"
            logging.log(logging.INFO, f"Sending item list message: {item_list_message}")
            gpt_response = await ask_gpt_session(item_list_message, session_data)
            await play_and_transcribe_response(item_list_message, 
                                         gpt_response,
                                         voice_client)
        
        await start_listening(voice_client)
        await manage_session(member, voice_client)
    
    # Bot will leave the channel once the user disconnects
    if before.channel and not after.channel and member.guild.voice_client:
        voice_client = member.guild.voice_client
        await voice_client.disconnect()

    return


async def join_channel(voice_channel):
    # Joins a channel, returns a voice_client
    voice_client = await voice_channel.connect(cls=voice_recv.VoiceRecvClient)
    return voice_client


async def start_listening(voice_client):
    logging.info(f"Starting to listen in {voice_client.channel.name}")
    if voice_client.channel not in gcp_sinks:
        gcp_sinks[voice_client.channel] = GcpSink(schedule_response_to_audio, voice_client)

    # Play a block of silence -- still not sure what this is for but everyone does it.
    # -- Not playing it for now -- it interrupts the initial conversation..
    # audio_source = FFmpegPCMAudio('250ms-silence.mp3')
    # voice_client.play(audio_source, after=lambda e: print(f'Playback error: {e}') if e else None)

    # TODO turn into a log
    print(f"[{datetime.datetime.now().isoformat()}]", "Recording...")

    # Start listening & watching for user PTT release
    voice_client.listen(gcp_sinks.get(voice_client.channel))
    asyncio.create_task(gcp_sinks.get(voice_client.channel).monitor_buffer())

    return


async def manage_session(user, voice_client):
    # This function will manage the session for the user. It will keep track of the user's progress
    # through the scenario, and will handle the text channel.

    # TODO: This only works for konbini sessions. Need to add additional session types.

    while True:
        channel = discord.utils.get(user.guild.text_channels, name='konbini-test')
        message = await bot.wait_for('message', check=lambda message: message.channel == channel)
        # Process the message here
        response = await respond_to_user(message.content, voice_client)
        if "ありがとう" in response:
            await end_session(user, voice_client.channel, voice_client)
            break

    return

async def play_and_transcribe_response(prompt: str, response: str, voice_client: VoiceClient) -> None:
    """
    Convenience function to play the response and transcribe it to the text channel.
    """ 
    # TODO: What happens when there are multiple users?
    await play_response(response, voice_client)
    await transcribe_response(prompt, response, voice_client)

    return

async def play_response(response, voice_client):
    # Plays the response -- also runs a voice changer
    session = sessions.get(voice_client.channel.name)
    response_count = len(session.chat_history)
    username = session.user.name
    response_filename = os.path.join(BASE_AUDIO_DIR, str(datetime.date.today()), username, f"response{response_count}.wav")
    os.makedirs(os.path.dirname(response_filename), exist_ok=True)
    
    # Get the VoiceVox audio
    hex_audio = text_to_hex_audio(response)
    save_hex_to_wav(hex_audio, response_filename + ".wav")
    
    # Convert hex to b64 for the voice changer
    b64_audio = hex_to_b64_string(hex_audio)
    voice_changed_b64_audio = change_voice(b64_audio)
    if not voice_changed_b64_audio:
        print("Voice changer failed.")
        return
    save_b64_string_to_wav(voice_changed_b64_audio, response_filename)

    # Play the audio
    print("Playing response back")
    audio_source = FFmpegPCMAudio(response_filename)  # TODO FIX AUDIO.WAV
    voice_client.play(audio_source, after=lambda e: print(f'Playback error: {e}') if e else None)

    return


async def transcribe_response(prompt, response, voice_client):
    # Send the transcription message as a message
    # TODO: Don't use a hard-coded channel name. Find a better place to send the conversation transcript.
    channel = discord.utils.get(voice_client.guild.text_channels, name='konbini-test')
    await channel.send(f"you: {prompt}")
    await channel.send(f"konbini-bot: {response}")

    return


async def respond_to_user(user_message, voice_client):
    """
        Takes a message from the user, gets a response from gpt, converts it to spoken audio, and finally
        will play the message in the channel.

        Returns the response from GPT -- we are doing this for now because we manage_session
        needs to know when to end the session. In most cases, we'll probably ignore it.
    """
    print(f"Responding to message: {user_message}")
    gpt_response = await ask_gpt_session(user_message, sessions.get(voice_client.channel.name))

    await play_response(gpt_response, voice_client)
    await transcribe_response(user_message, gpt_response, voice_client)

    return gpt_response

### Infra functions -- these manage the user and bot's presence in the channel. ###
async def end_session(user, voice_channel, voice_client):
    # Remove the user from the session
    sessions.pop(voice_channel.name)

    # Disconnect the user from the voice channel
    await voice_channel.disconnect(user)

    # Disconnect the bot from the voice channel
    voice_client = discord.utils.get(bot.voice_clients, guild=voice_channel.guild)
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()

    return

### Scenario functions -- these handle scenario set-up & the conversation loop ###

### Utility functions -- these are primarily for debugging. They are not used in other commands. ###
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='chat')
async def chat(ctx, *, message: str):  # The '*' indicates that 'message' will consume the rest of the command input
    """
    This allows the user to chat with GPT through the channel text input.
    """
    # Call the ask_gpt function with the message
    gpt_response = await ask_gpt(message)

    # TODO: This is mega messed up LOL
    # ask_gpt will write an audio file to audio.wav. The bot plays that audio back here.
    convert_to_audio(gpt_response)
    await ctx.invoke(bot.get_command('play_sample'))

    # Print the response in the chat
    await ctx.send(gpt_response)


# Run the bot
bot.run(TOKEN)
