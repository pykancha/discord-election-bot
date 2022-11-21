import time

import discord


def format_data_as_embed(data, parsed_cmd):
    district, area_no = (
        parsed_cmd["district"],
        parsed_cmd["area"],
    )
    print(f":: Formatting data {district} {area_no}")
    body = [
        "   ".join([heading.center(18, " ") for heading in "Name Votes".split(" ")]),
    ]
    sorted_data = sorted(data, key=lambda x: int(x["votes"]), reverse=True)

    print(f":: Taking first 3 items from data of len {len(sorted_data)}")
    for entry in sorted_data[:3]:
        del entry["party"]
        body.append(
            "   ".join([str(value).center(18, " ") for key, value in entry.items()])
        )
        desc = "```" + "\n".join(body) + "```"

    embed = discord.Embed(
        title=f"{district.capitalize()} {area_no}",
        description=desc,
        color=discord.Color.green(),
    )
    leader_vote, runner_up_vote = int(data[0]["votes"]), int(data[1]["votes"])
    embed.set_footer(
        text=(
            f"Vote Lead: + {(leader_vote - runner_up_vote):,}\n\n"
            "source: https://election.ekantipur.com?lng=eng\n\n"
            "Bot Code: https://github.com/pykancha/discord-election-bot"
        )
    )
    return embed


def format_help_as_embed():
    desc = (
        """  An <area> is formatted as "state 3 kathmandu 8" \n\n  """
        "  ?check <area> : Check a election area.\n\n  "
        "  ?sub <area> : Subscribe to new updates in this area.\n\n  "
        "  ?unsub <area> : Unsubscribe this area.\n\n  "
        "  ?listsub : View all your subscriptions.\n\n  "
    )
    embed = discord.Embed(title="Usage:", description=desc, color=discord.Color.blue())
    embed.set_footer(
        text=(
            "source: https://election.ekantipur.com?lng=eng\n\n"
            "Bot Code: https://github.com/pykancha/discord-election-bot"
        )
    )
    return embed


def format_subscription_as_embed(subscriptions):
    body = ""
    for subscription in subscriptions:
        state_no, district_name, area_no = (
            subscription["pradesh"],
            subscription["district"],
            subscription["area"],
        )
        body += f"state: {state_no} {district_name} : {area_no}\n"
    embed = discord.Embed(
        title="Subscriptions", description=body, color=discord.Color.green()
    )
    return embed
