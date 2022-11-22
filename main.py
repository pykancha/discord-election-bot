# bot.py
import asyncio
import json
import os

import discord
import requests
from discord.ext import commands, tasks
from dotenv import load_dotenv

from message_formatter import (
    format_data_as_embed,
    format_help_as_embed,
    format_subscription_as_embed,
)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
URL = "http://localhost:8090"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(
    command_prefix=("e?", "?"),
    description="Election Updates for Federal and Provincial",
    intents=intents,
)


@bot.event
async def on_ready():
    print(f"{bot.user} is connected to the following guild:\n")
    election_updater.start()


@tasks.loop(minutes=2)
async def election_updater():
    with open("db.json", "r") as rf:
        subscription_data = json.load(rf)
    subscriptions = []
    for guild_id, subscription_list in subscription_data.items():
        for subscription in subscription_list:
            if subscription not in subscriptions:
                subscriptions.append(subscription)

    bulk_list = ""
    for subscription in subscriptions:
        state_no, district = subscription["pradesh"], subscription["district"]
        bulk_list += f"pradesh-{state_no}/district-{district},"

    # remove last comma
    bulk_list = bulk_list[:-1]
    bulk_list_url = f"{URL}/bulk?list={bulk_list}"

    data = None
    try:
        print("requesting at ", bulk_list_url)
        data = requests.get(bulk_list_url).json()
        data = get_top_3_of_all(data)
    except Exception as e:
        print("Error during fetching bulk lists", e)
        return False

    cache_data = {}
    try:
        with open("cache.json", "r") as rf:
            cache_data = json.load(rf)
    except Exception as e:
        print("Failed loading cache", e)

    if cache_data == data:
        print("Cache Matched: No updates")
        return

    with open("cache.json", "w") as wf:
        json.dump(data, wf)

    try:
        await update_guilds(subscriptions, cache_data, data)
    except Exception as e:
        print("Failed updating guilds", e)


async def update_guilds(subscriptions, cache_data, data):
    with open("db.json", "r") as rf:
        subscription_data = json.load(rf)

    for subscription in subscriptions:
        guild_ids_with_sub = await filter_guild_id_with_sub(
            subscription, subscription_data
        )
        await need_for_sync(guild_ids_with_sub, subscription, cache_data, data)


async def filter_guild_id_with_sub(subscription_to_filter, subscription_data):
    guild_ids = []
    for guild_id, subscription_list in subscription_data.items():
        for subscription in subscription_list:
            if subscription_to_filter == subscription:
                guild_ids.append(guild_id)
    return guild_ids


async def need_for_sync(guild_ids, subscription, cache_data, data):
    district_name, area_no = subscription["district"], subscription["area"]
    try:
        cache_info = cache_data[district_name][f"constituency : {area_no}"]
    except Exception as e:
        print(f"No cache data for {district_name} {area_no} {e}...")
        return
    print(f":: processing {district_name} {area_no}")
    try:
        new_info = data[district_name][f"constituency : {area_no}"]
    except Exception as e:
        print(f"Failed obtaining data for {district_name} {area_no}... {e}")
        return

    if cache_info != new_info:
        print(f":: cached unmatched {district_name} {area_no}")
        embed = format_data_as_embed(new_info, subscription)
        for guild_id in guild_ids:
            guild = bot.get_guild(int(guild_id))
            print("Fechted guild", guild)
            channel = find_channel_to_send_msg(guild)
            await channel.send(embed=embed)

    else:
        print(f":: cached matched {district_name} {area_no}")


@bot.event
async def on_guild_join(guild):
    with open("db.json", "r") as rf:
        subscription_data = json.load(rf)

    subscriptions = [
        {"pradesh": "7", "district": "dadeldhura", "area": "1"},
        {"pradesh": "3", "district": "chitwan", "area": "2"},
    ]

    channel = find_channel_to_send_msg(guild)

    try:
        await channel.send(embed=format_help_as_embed())
        for embed in gen_subscription_embeds(subscriptions):
            await channel.send(embed=embed)
            print("New guild message sent")
            await asyncio.sleep(1)
    except Exception as e:
        print(e, channel.guild.name)

    subscription_data[str(guild.id)] = subscriptions

    with open("db.json", "w") as wf:
        json.dump(subscription_data, wf)


@bot.event
async def on_guild_remove(guild):
    with open("db.json", "r") as rf:
        subscription_data = json.load(rf)

    try:
        del subscription_data[str(guild.id)]
    except Exception as e:
        print("failed deleting guild records", e)

    with open("db.json", "w") as wf:
        json.dump(subscription_data, wf)


@bot.command()
async def sub(ctx, *args):
    """
    Subscribe to a constituency: eg state 3 kathmandu 1
    """
    parsed_cmd = parse_command(" ".join(args))
    print("parsed as ", parsed_cmd)
    data = validate_sub(parsed_cmd)
    if not parsed_cmd or not data:
        await ctx.send(
            f"Invalid subscription: {' '.join(args)}\n"
            "Try again or review syntax\n"
            "Syntax eg: ?sub state 3 kathmandu 10"
        )
        return

    if is_subscribed(ctx.channel.guild.id, parsed_cmd):
        await ctx.send("❗ You are already subscribed.")
        return

    if add_subscription(ctx.channel.guild.id, parsed_cmd):
        await ctx.send("✅ Successfully subscribed.")
        embed = format_data_as_embed(data, parsed_cmd)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Something went wrong our side. Please try again.")


@bot.command()
async def unsub(ctx, *args):
    """
    Unsubscribe to a constituency: eg state 3 kathmandu 1
    """
    parsed_cmd = parse_command(" ".join(args))
    print("parsed as ", parsed_cmd)
    if not parsed_cmd:
        await ctx.send(
            f"Invalid subscription: {' '.join(args)}\n"
            "Try again or review syntax\n"
            "Syntax eg: ?unsub state 3 kathmandu 10"
        )
        return

    if not is_subscribed(ctx.channel.guild.id, parsed_cmd):
        await ctx.send("❗ You never subscribed to this region.")
        return

    if remove_subscription(ctx.channel.guild.id, parsed_cmd):
        await ctx.send("✅ Successfully unsubscribed.")
    else:
        await ctx.send("❌ Something went wrong our side. Please try again.")


@bot.command()
async def check(ctx, *args):
    """
    Check a given constituency: eg state 3 kathmandu 10
    """
    parsed_cmd = parse_command(" ".join(args))
    print("parsed as ", parsed_cmd)
    data = validate_sub(parsed_cmd)
    if not parsed_cmd or not data:
        await ctx.send(
            f"Invalid area code: {' '.join(args)}\n"
            "Try again or review syntax\n"
            "Syntax eg: ?check state 3 kathmandu 10"
        )
        return
    try:
        embed = format_data_as_embed(data, parsed_cmd)
        await ctx.send(embed=embed)
    except Exception as e:
        print("Cannot output check: ", e)
        await ctx.send("❌ Something went wrong our side. Please try again.")


@bot.command()
async def listsub(ctx):
    """
    List all subscriptions
    """
    subscriptions = get_subscriptions(ctx.channel.guild.id)
    if not subscriptions:
        return
    await ctx.send(embed=format_subscription_as_embed(subscriptions))


def get_subscriptions(guild_id):
    guild_id = str(guild_id)
    with open("db.json", "r") as rf:
        subscription_data = json.load(rf)
    try:
        subs = subscription_data[guild_id]
        return subs
    except Exception as e:
        print("❌ Something wrong happened, remove and reinvite the bot", e)


def add_subscription(guild_id, parsed_cmd):
    guild_id = str(guild_id)
    with open("db.json", "r") as rf:
        subscription_data = json.load(rf)
    print(":: Adding sub, sub data", subscription_data)
    try:
        prev_subs = subscription_data[guild_id]
        prev_subs.append(parsed_cmd)
        subscription_data[guild_id] = prev_subs
    except Exception as e:
        print("Failed adding subscription", e)
        return False

    with open("db.json", "w") as wf:
        json.dump(subscription_data, wf)
    return True


def remove_subscription(guild_id, parsed_cmd):
    guild_id = str(guild_id)
    with open("db.json", "r") as rf:
        subscription_data = json.load(rf)
    try:
        prev_subs = subscription_data[guild_id]
        prev_subs.remove(parsed_cmd)
        subscription_data[guild_id] = prev_subs
    except Exception as e:
        print("Failed removing subscription", e)
        return False

    with open("db.json", "w") as wf:
        json.dump(subscription_data, wf)
    return True


def is_subscribed(guild_id, parsed_cmd):
    guild_id = str(guild_id)
    with open("db.json", "r") as rf:
        subscription_data = json.load(rf)
    try:
        prev_subs = subscription_data[guild_id]
        return parsed_cmd in prev_subs
    except Exception as e:
        print("Failed checking subscription", e)
        return False

    return True


def parse_command(command):
    cmd_parts = command.split(" ")
    cmd_parts = [i.strip().lower() for i in cmd_parts if i.strip()]
    print(cmd_parts)
    try:
        state_no, district_name, area_no = cmd_parts[1], cmd_parts[2], cmd_parts[3]
        return {"pradesh": state_no, "district": district_name, "area": area_no}
    except Exception as e:
        print("Error during parsing command", e)
        return False


def validate_sub(parsed_command):
    print("validating", parsed_command)
    try:
        state_no, district, area_no = (
            parsed_command["pradesh"],
            parsed_command["district"],
            parsed_command["area"],
        )
        url = make_url(state_no, district)
        print("requesting at ", url)
        data = requests.get(url).json()
        print("Got data", len(data))
        data = data[f"constituency : {area_no}"]
        return data
    except Exception as e:
        print("Error during validating sub", e)
        return False


def make_url(state_no, district):
    url_f = f"{URL}/area?name=pradesh-{state_no}/district-{district}"
    return url_f


def gen_subscription_embeds(subscriptions):
    embeds = []
    for parsed_cmd in subscriptions:
        data = validate_sub(parsed_cmd)
        if not data:
            continue
        embed = format_data_as_embed(data, parsed_cmd)
        embeds.append(embed)
    return embeds


def find_channel_to_send_msg(guild):
    channel_to_send = None
    channels = []
    for channel in guild.channels:
        print(":: scanning channel ", channel.name)
        channels.append(channel)
        if channel.name == "election-updates":
            return channel
        elif channel.name == "general":
            channel_to_send = channel

    print(f":: Scanned {len(channels)} channels")
    return channel_to_send or channels[0]


def get_top_3_of_all(data):
    new_data = dict()
    for district, constituency_dict in data.items():
        new_constituency_dict = dict()
        for constituency, data_list in constituency_dict.items():
            new_constituency_dict[constituency] = data_list[:3]
        new_data[district] = new_constituency_dict
    return new_data


if __name__ == "__main__":
    bot.run(TOKEN)
