# bot.py
import os
import json

import asyncio
import discord
from discord.ext import tasks
from dotenv import load_dotenv

from scraper import gen_message, get_city_data_map, gen_embed
from keep_alive import keep_alive

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MY_GUILD = "Dev Server"
#TODO
# new channel entry
# lead (+ lead) count
# Graph and metadata

client = discord.Client()
@client.event
async def on_ready():
    print(
            f'{client.user} is connected to the following guild:\n'
        )
    await election_updater()

async def election_updater():
    while True:
        updated_data = await election_info_updated()
        if updated_data:
            await send_message(updated_data)
        else:
            print("No updates")

        full_updated_data = await election_info_updated(full=True)
        if full_updated_data:
            await send_message(updated_data, to_me=True)
        else:
            print("No Full updates")

        if updated_data or full_updated_data:
            os.system('git add . && git commit -m "updates data"')
        
        await asyncio.sleep(60)


async def election_info_updated(full=False):
    data = get_city_data_map(full=full)
    with open('ktm_data.json', 'r') as rf:
        ktm_cache_data = json.load(rf)
    with open('election_data.json', 'r') as rf:
        election_cache_data = json.load(rf)

    ktm_mayor_cache_data = ktm_cache_data['Kathmandu']['mayor']
    ktm_mayor_data = data['Kathmandu']['mayor']

    if full and election_cache_data != data:
        with open('election_data.json', 'w') as wf:
            json.dump(data, wf)
        return data
    elif ktm_mayor_cache_data != ktm_mayor_data:
        with open('ktm_data.json', 'w') as wf:
            json.dump(data, wf)
        return data
    else:
        return False

async def send_message(data, to_me=False):
    embed_messages = gen_embed(data)
    channels = []
    user_ids = [528240871481540611, 397648789793669121]
    if to_me:
        user_ids = user_ids[:1]

    for user_id in user_ids:
        user = await client.fetch_user(user_id)
        try:
            for embed in embed_messages:
                await user.send(embed=embed)
        except Exception as e:
            print("dm fialed", e)
    
    if to_me:
        return

    print(len(client.guilds))
    for guild in client.guilds:
        for channel in guild.channels:
            channel.append(channels)
            if channel.name == 'election-updates':
                try:
                    for embed in embed_messages:
                        await channel.send(embed)
                    await asyncio.sleep(1)
                except Exception as e:
                    print(e, channel.guild.name)

async def join_new_channel():
    #with open('channelids.json', 'r') as rf:
    #    channel_ids = json.load(rf)


    #new_channel = False
    #channels = []
    #for channel in channels:
    #    if channel.id not in channel_ids:
    #        print("New channel", channel.guild.name)
    #        new_channel = True
    #    else:
    #        new_channel = False

    #    if outdated or new_channel:
    #        print("Outdated:", outdated, "New channel:", new_channel)
    #    else:
    #        print("No new updates")

        #with open('channelids.json', 'w') as wf:
        #    ids = [i.id for i in channels]
        #    json.dump(ids, wf)
        #    
    pass


if __name__ == "__main__":
    keep_alive()
    client.run(TOKEN)
