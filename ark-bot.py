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
    #opening cache
    with open('ark-bot-rewritten/cache.json', "r") as read_file:
        old_times = json.load(read_file)

    html = requests.get(url)
    soup = BeautifulSoup(html.text, "html.parser")
    #list for the latest times
    new_times = []
    #parse html table, starting from the first element, since [0] is empty space
    for tr in soup.findAll('tr')[1:]:
        #wrapped inside try/except because sometimes it crashes
        try:
            tds = tr.findAll('td')
            location = tds[0].string
            first_available = tds[2].string
            second_available = tds[3].string
            third_available = tds[4].string
            #construct the dict that is going to be sent
            table_row = {
                "Koht": location,
                "1": first_available,
                "2": second_available,
                "3": third_available,
                "Link": 'eteenindus.mnt.ee/main.jsf'
            }
            #send most recent times to the list
            new_times.append(table_row)
        except IndexError:
            pass
    #search for difference between new list times and older times stored in json
    for diff in new_times:
        if diff not in old_times:
            #yield over return because sometimes there are many changes
            yield diff
            #write the updates to the json 
            with open('ark-bot-rewritten/cache.json', 'w') as f:
                json.dump(new_times, f)

def sendTweet():
    #getting the enviroment variables, setting up tweepy
    load_dotenv()
    auth = tweepy.OAuthHandler(
        os.getenv('CONSUMER_KEY'), os.getenv('CONSUMER_SECRET'))
    auth.set_access_token(os.getenv('ACCESS_TOKEN'),
                          os.getenv('ACCESS_TOKEN_SECRET'))
    api = tweepy.API(auth, wait_on_rate_limit=True)
    #giving generator scrape a variable value
    data = scrape()
    
    if data is None:
        pass
    else:
        try:
            #string manipulation spagetthi, remove curly brackets, commas etc
            tweet = "\n".join(map(str, data)).replace("{", "").replace("}", "").replace("'", "").replace(",", "\n")
            #when length of the string is smaller than twitter max character length
            if len(tweet) < 240:
                
                print(tweet)
                print("Sending tweet")
                api.update_status(status=tweet)
            else:
                print("Too many chars")
                ### for future reference, cut up the huge string and send 1 location at a time
        #catch duplicate tweet error
        except tweepy.TweepError as error:
            if error.api_code == 187:
                print('Duplikaat')
            else:
                raise error


while 1:
    #start the cycle every 5s
    scrape()
    sendTweet()
    time.sleep(5)
