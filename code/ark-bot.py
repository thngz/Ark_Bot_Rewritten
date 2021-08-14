from bs4 import BeautifulSoup
import requests
import time
import tweepy
import os
import mysql.connector
from dotenv import load_dotenv


print(f"started at {time.strftime('%X')}")


class Arkbot:
    def __init__(self):
        self.url = "https://eteenindus.mnt.ee/public/vabadSoidueksamiajad.xhtml"
        self.html = requests.get(self.url)
        self.soup = BeautifulSoup(self.html.text, "html.parser")
        self.diff = None
        self.DB_NAME = "examtimes"
        self.host = "mysql"
        self.db = mysql.connector.connect(user="root", password="root", host=self.host)
        self.cursor = self.db.cursor()
        self.old_times = None
        self.diffs = []

    def create_database(self):
        try:
            self.cursor.execute(
                f"CREATE DATABASE {self.DB_NAME} DEFAULT CHARACTER SET 'utf8'"
            )
        except mysql.connector.Error as err:
            pass

    def create_table(self):
        try:
            self.cursor.execute(f"USE {self.DB_NAME}")
        except mysql.connector.Error as err:
            print(f"Database {self.DB_NAME} does not exist.")

        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS exams (location VARCHAR(255) PRIMARY KEY, first VARCHAR(255), second VARCHAR(255), third VARCHAR(255), link VARCHAR(255))"
        )
        self.cursor.execute("SELECT location, first, second, third FROM exams")
        self.old_times = self.cursor.fetchall()

    def scrape(self):

        try:
            for tr in self.soup.findAll("tr")[1:]:
                tds = tr.findAll("td")
                location = tds[0].string
                first_available = tds[2].string
                second_available = tds[3].string
                third_available = tds[4].string

                # Store into sql database
                add_exams_sql = "REPLACE INTO exams (location, first, second, third, link) VALUES (%s, %s, %s, %s, %s)"
                values = (
                    location,
                    first_available,
                    second_available,
                    third_available,
                    "eteenindus.mnt.ee/main.jsf",
                )
                self.cursor.execute(add_exams_sql, values)
                self.db.commit()

        except IndexError:
            print("Index error")

    def compare_data(self):

        self.cursor.execute("SELECT location, first, second, third FROM exams")
        new_times = self.cursor.fetchall()
        for diff in new_times:
            if diff not in self.old_times:
                self.diffs.append(diff)
                if len(self.old_times) > 0:
                    self.old_times.pop(0)

    def tweet(self):
        load_dotenv()
        auth = tweepy.OAuthHandler(
            os.getenv("CONSUMER_KEY"), os.getenv("CONSUMER_SECRET")
        )
        auth.set_access_token(
            os.getenv("ACCESS_TOKEN"), os.getenv("ACCESS_TOKEN_SECRET")
        )
        api = tweepy.API(auth, wait_on_rate_limit=True)
        if len(self.diffs) == 0:
            pass
        else:
            try:
                for diff in self.diffs:
                    tweet = (
                        "\n".join(map(str, diff))
                        .replace("{", "")
                        .replace("}", "")
                        .replace("'", "")
                        .replace(",", "\n")
                    )
                    if tweet:
                        print(tweet)
                        print("Sending tweet")
                        api.update_status(status=tweet)
                        tweet = None
                        self.diffs.pop(0)
                    else:
                        print("no tweet")
                        pass
            except tweepy.TweepError as error:
                if error.api_code == 187:
                    print("Duplikaat")
                else:
                    raise error

    def run(self):
        self.create_database()
        self.create_table()
        self.scrape()
        self.compare_data()
        self.tweet()


while True:
    arkbot = Arkbot()
    arkbot.run()
    time.sleep(5)
