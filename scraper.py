import time
from news import get_ktm_votes, get_lalitpur_votes, get_bharatpur_votes

def gen_message(full=False):
    city_data_map = dict(
        Kathmandu=get_ktm_votes,
        Bharatpur=get_bharatpur_votes,
        Lalitpur=get_lalitpur_votes,
    ) 
    if not full:
        city_data_map = dict(Kathmandu=get_ktm_votes())

    header = "source: election dot ekantipur dot com\n"
    #footer = """^^contribute:  [Bot code](https://github.com/pykancha/reddit-bots) |  [Api code](https://github.com/pykancha/election-api) | [Api url for your personal automation](https://g7te1m.deta.dev/)"""
    footer = ''
    text = ''
    for city, data in city_data_map.items():
        text += construct_msg(city, data, full=full) if city!='Kathmandu' else construct_msg(city, data, concat_name=True, full=full)
        time.sleep(2)

    submission_body = f"{header}\n{text}\n{footer}"
    return submission_body

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

