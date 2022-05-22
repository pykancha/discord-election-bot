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
#TODO
# lead (+ lead) count
# Graph and metadata

client = discord.Client()

@client.event
async def on_ready():
    print(
            f'{client.user} is connected to the following guild:\n'
        )
    election_updater.start()

@tasks.loop(minutes=2)
async def election_updater():
    updated_data = await election_info_updated()
    if updated_data:
        await send_message(updated_data)
    else:
        print("No updates")

    full_updated_data = await election_info_updated(full=True)
    #if full_updated_data:
    #    await send_message(full_updated_data, to_me=True)
    #else:
    #    print("No Full updates")

    if updated_data or full_updated_data:
        os.system('git add . && git commit -m "updates data"')


@client.event
async def on_guild_join(guild):
    print("Joining new guild", guild.name)
    with open('ktm_data.json', 'r') as rf:
        ktm_cache_data = json.load(rf)
    with open('channelids.json', 'r') as rf:
        channel_ids = json.load(rf)

    embed_messages = gen_embed(ktm_cache_data)
    for channel in guild.channels:
        if channel.name == 'election-updates':
            channel_ids.append(channel.id)
            try:
                for embed in embed_messages:
                    await channel.send(embed=embed)
                    print("New guild message sent")
                    await asyncio.sleep(1)
            except Exception as e:
                print(e, channel.guild.name)

    with open('channelids.json', 'w') as wf:
        json.dump(channel_ids, wf)

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
    channels = []
    for guild in client.guilds:
        for channel in guild.channels:
            if channel.name == 'election-updates':
                channels.append(channel.id)
                try:
                    for embed in embed_messages:
                        await channel.send(embed=embed)
                    await asyncio.sleep(3)
                except Exception as e:
                    print(e, channel.guild.name)

    # update channel ids
    if channels:
        with open('channelids.json', 'w') as wf:
            json.dump(channels, wf)

if __name__ == "__main__":
    keep_alive()
    client.run(TOKEN)
