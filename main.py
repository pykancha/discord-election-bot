# bot.py
import os
import json

import asyncio
import discord
from discord.ext import tasks
from dotenv import load_dotenv

from scraper import gen_message

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MY_GUILD = "Dev Server"

client = discord.Client()
@client.event
async def on_ready():
    channels = []
    print(len(client.guilds))
    for guild in client.guilds:
        for channel in guild.channels:
            if channel.name == 'election-updates':
                channels.append(channel)

        print(
            f'{client.user} is connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})'
        )

    await election_updater(channels)

async def election_updater(channels):

    while True:
        message = gen_message()
        full_message = gen_message(full=True)
        message_outdated = False
        full_message_outdated = False
        with open('message.json', 'r') as wf:
            cached_message = json.load(wf)
        with open('full_message.json', 'r') as wf:
            full_cached_message = json.load(wf)


        if message != cached_message:
            message_outdated = True
            with open('message.json', 'w') as wf:
                json.dump(message, wf)
        if full_message != full_cached_message:
            full_message_outdated = True
            with open('message.json', 'w') as wf:
                json.dump(message, wf)

        outdated = message_outdated
        for channel in channels:
            if channel.guild == MY_GUILD:
                message = full_message
                outdated = full_message_outdated
            if outdated:
                await channel.send(message)
        else:
            print("Yes")
        await asyncio.sleep(60)

if __name__ == "__main__":
    client.run(TOKEN)
