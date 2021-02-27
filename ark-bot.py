from bs4 import BeautifulSoup
import requests
import json
import time
import tweepy
import os
from dotenv import load_dotenv

print(f"started at {time.strftime('%X')}")


def scrape():
    url = "https://eteenindus.mnt.ee/public/vabadSoidueksamiajad.xhtml"
    cache_times = []
    with open('ark-bot-rewritten/cache.json', "r") as read_file:
        old_times = json.load(read_file)

    html = requests.get(url)
    soup = BeautifulSoup(html.text, "lxml")

    for tr in soup.findAll('tr')[1:]:
        tds = tr.findAll('td')
        location = tds[0].string
        first_available = tds[2].string
        second_available = tds[3].string
        third_available = tds[4].string

        table_row = {
            "Koht": location,
            "1": first_available,
            "2": second_available,
            "3": third_available,
            "Link": 'eteenindus.mnt.ee/main.jsf'
        }

        cache_times.append(table_row)

    for diff in cache_times:
        if diff not in old_times:

            with open('ark-bot-rewritten/cache.json', 'w') as f:
                json.dump(cache_times, f)

            return diff


def sendTweet():
    load_dotenv()
    auth = tweepy.OAuthHandler(
        os.getenv('CONSUMER_KEY'), os.getenv('CONSUMER_SECRET'))
    auth.set_access_token(os.getenv('ACCESS_TOKEN'),
                          os.getenv('ACCESS_TOKEN_SECRET'))
    api = tweepy.API(auth)
    data = scrape()
    # Stringi tootlus
    tweet = str(data).replace("{", "").replace("}",
                                               "").replace("'", "").replace(",", "\n")

    if data is None:
        print("No updates")
    else:
        try:
            print("Sending tweet")
            print(tweet)
            api.update_status(status=tweet)

        except tweepy.TweepError as error:
            if error.api_code == 187:
                print('Duplikaat')
            else:
                raise error


while 1:

    scrape()
    sendTweet()
    time.sleep(10)
