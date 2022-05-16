# bot.py
import os
import json

import asyncio
import discord
from discord.ext import tasks
from dotenv import load_dotenv

from scraper import gen_message
from keep_alive import keep_alive

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MY_GUILD = "Dev Server"

client = discord.Client()
@client.event
async def on_ready():
    print(
            f'{client.user} is connected to the following guild:\n'
        )
    await election_updater()

async def election_updater():
    while True:
        channels = []
        print(len(client.guilds))
        for guild in client.guilds:
            for channel in guild.channels:
                if channel.name == 'election-updates':
                    channels.append(channel)

        try:
            short_message = gen_message()
        except Exception as e:
            print("Scrape error", e)
            await asyncio.sleep(5)
            continue

        await asyncio.sleep(5)

        try:
            full_message = gen_message(full=True)
        except Exception as e:
            print("Scrape error", e)
            await asyncio.sleep(5)
            continue

        message_outdated = False
        full_message_outdated = False
        with open('message.json', 'r') as rf:
            cached_message = json.load(rf)
        with open('full_message.json', 'r') as rf:
            full_cached_message = json.load(rf)
        with open('channelids.json', 'r') as rf:
            channel_ids = json.load(rf)

        if short_message != cached_message:
            print("Cache unmatched")
            message_outdated = True
            with open('message.json', 'w') as wf:
                json.dump(short_message, wf)
        if full_message != full_cached_message:
            full_message_outdated = True
            with open('full_message.json', 'w') as wf:
                print("Full Cache unmatched")
                json.dump(full_message, wf)

        message = ''
        outdated = message_outdated
        if message_outdated:
            user = await client.fetch_user(397648789793669121)
            try:
                await user.send(short_message)
            except Exception as e:
                print("dm fialed", e)

        new_channel = False
        for channel in channels:
            if channel.id not in channel_ids:
                print("New channel", channel.guild.name)
                new_channel = True
            else:
                new_channel = False

            if channel.guild.name == MY_GUILD:
                print("My guild, preparing full message")
                message = full_message
                outdated = full_message_outdated
            else:
                message = short_message
                outdated = message_outdated

            if outdated or new_channel:
                print("Outdated:", outdated, "New channel:", new_channel)
                try:
                    await channel.send(message)
                except Exception as e:
                    print(e, channel.guild.name)
            else:
                print("No new updates")

        with open('channelids.json', 'w') as wf:
            ids = [i.id for i in channels]
            json.dump(ids, wf)
            
        if full_message_outdated or message_outdated:
            os.system('git add . && git commit -m "updates data"')
            
        await asyncio.sleep(120)


if __name__ == "__main__":
    keep_alive()
    client.run(TOKEN)
