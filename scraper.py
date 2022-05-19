import time
import discord
from news import get_ktm_votes, get_lalitpur_votes, get_bharatpur_votes

def gen_message(city_data_map, full=False):
    header = "source: election dot ekantipur dot com\n"
    #footer = """^^contribute:  [Bot code](https://github.com/pykancha/reddit-bots) |  [Api code](https://github.com/pykancha/election-api) | [Api url for your personal automation](https://g7te1m.deta.dev/)"""
    footer = ''
    text = ''
    for city, data in city_data_map.items():
        text += construct_msg(city, data, full=full) if city!='Kathmandu' else construct_msg(city, data, concat_name=True, full=full)
        time.sleep(2)

    submission_body = f"{header}\n{text}\n{footer}"
    return submission_body

def gen_embed(city_data_map):
    # funcs
    mayor_names = lambda x: [f"{i['candidate-name']}" for i in city_data_map[x]['mayor']]
    mayor_votes = lambda x: [f"{i['vote-numbers']}" for i in city_data_map[x]['mayor']]
    percentage, vote_count = lambda x: city_data_map[x]['percentage'], lambda x: city_data_map[x]['vote_counted']

    embeds = []
    for city in city_data_map:
        DATASET = []
        for mayor_name, vote in zip(mayor_names(city), mayor_votes(city)):
            DATASET.append( (mayor_name, vote) )
        header = ['   '.join([heading.center(18, ' ') for heading in 'Name Votes'.split()]), ]
        for data in DATASET:
            header.append('   '.join([str(item).center(18, ' ') for item in data]))
        desc = '```'+'\n'.join(header) + '```'
        ktm_leader_vote = int(mayor_votes(city)[0])
        ktm_runnerup_vote = int(mayor_votes(city)[1])
        embed = discord.Embed(title = f'{city} Mayor', description = desc, color=discord.Color.green())
        embed.set_footer(
            text=("\nTotal votes: 191, 186\n"
                  f"Vote counted: {percentage(city)}% ({vote_count(city):,})\n"
                  f"Vote Lead: + {(ktm_leader_vote - ktm_runnerup_vote):,}\n\n"
                  "source: https://election.ekantipur.com?lng=eng"
                 )
        )
        embeds.append(embed)
    return embeds

def get_city_data_map(full=False):
    city_data_map = dict(
        Kathmandu=get_ktm_votes,
        Bharatpur=get_bharatpur_votes,
        Lalitpur=get_lalitpur_votes,
    ) 
    if not full:
        city_data_map = dict(Kathmandu=get_ktm_votes)

    resolved_map = dict()
    for city, data in city_data_map.items():
        try:
            resolved_map[city] = data()
            time.sleep(2)
        except Exception as e:
            print("Resolve Fetch error", e, city)
            time.sleep(5)
            resolved_map[city] = data()
    return resolved_map

def construct_msg(city, data, concat_name=False, full=False):
    data = data()
    mayor = f"**{city}**\n**Mayor**\n"
    get_name = lambda x: x['candidate-name'] if not concat_name else x['candidate-name'].split(' ')[0]
    candidates = [f"- {get_name(i)} = {i['vote-numbers']}" for i in data['mayor']]
    mayor += "\n".join(candidates)
    deputy = "\n**Deputy Mayor**\n"
    candidates = [f"- {i['candidate-name'].split(' ')[0]} = {i['vote-numbers']}" for i in data['deputy']]
    deputy = deputy + "\n".join(candidates) if candidates else ""
    body = f'{mayor}\n{deputy}\n\n' if (deputy and full) else f'{mayor}\n\n'
    return body

