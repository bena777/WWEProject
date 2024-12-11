from flask_sqlalchemy import SQLAlchemy
from app import User, Matches, Ratings, db
import requests
from bs4 import BeautifulSoup
import time
import warnings
import re
warnings.simplefilter(action="ignore",category=FutureWarning)
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

def get_recent_matches(date,nrs):
        new_matches = []
        for i in nrs:
            cont = True
            url = f"https://www.cagematch.net//?id=8&nr={i}&page=7"
            headers = {"Accept-Encoding": "deflate"}
            soup = BeautifulSoup(requests.get(url, headers=headers).content, "html.parser")
            links = [
                "https://www.cagematch.net/" + a["href"] for a in soup.select(".TCol a")
            ]
            matches = []
            for u in links:
                if cont:
                    soup = BeautifulSoup(
                        requests.get(u, headers=headers).content, "html.parser"
                    )
                    match = {}
                    for info in soup.select(".InformationBoxRow"):
                        match[info.select_one(".InformationBoxTitle").text.strip()] = info.select_one(".InformationBoxContents").text.strip()
                    matches.append(match)
                    matches[len(matches)-1]["Event:"] = match["Event:"].split("(")[0]
                    matches[len(matches)-1]["Date:"] = match["Date:"][6:10]+"-"+match["Date:"][3:5]+"-"+match["Date:"][0:2]
                    if time.strptime(matches[len(matches)-1]["Date:"],"%Y-%m-%d") <= time.strptime(date,"%Y-%m-%d"):
                        cont = False
            for j in matches:
                match = j["Fixture:"].strip()
                participants = []
                for x in re.split(r'vs. |& |,',match):
                    participants.append(str(x.strip()))
                if len(participants) <= 10:
                    query = [match, j["Date:"].strip(), j["Promotion:"].strip(),j["Match type:"].strip(), j["Event:"].strip()]
                    while len(participants) < 10:
                        participants.append("n/a")
                    for z in participants:
                        query.append(z)
                    new_matches.append(query)
        return new_matches

def get_user_distribution(id):
    similar = {"Prince Devitt":"Finn Balor","Cody":"Cody Rhodes","Io Shirai":"IYO SKY","Dean Ambrose":"Jon Moxley"}
    query_result = db.session.query(Ratings, Matches).\
        join(Matches, Ratings.match_index == Matches.id).\
        filter(Ratings.user_index == id).all()
    matches = [match for _, match in query_result]
    superstars_ratings = {}
    superstars_count = {}
    for i in matches:
        for j in range(1,9):
            par_value = getattr(i,f"par{j}")
            if (par_value not in list(superstars_ratings.keys())) and (par_value != "n/a") and (par_value is not None):
                superstars_ratings[par_value] = Ratings.query.filter_by(user_index=id,match_index=i.id).first().rating
                superstars_count[par_value] = 1
            elif (par_value != "n/a") and (par_value is not None):
                superstars_ratings[par_value] += Ratings.query.filter_by(user_index=id,match_index=i.id).first().rating
                superstars_count[par_value]+=1
    end = []
    for i in superstars_ratings.keys():
        if i in list(similar.keys()):
            alias = i
            superstars_ratings[similar[alias]] += superstars_ratings[i]
            superstars_count[similar[alias]] += superstars_count[i]
            end.append(i)
    for j in end:
        del superstars_ratings[j]
        del superstars_count[j]
    return {x:[superstars_count[x],superstars_ratings[x]] for x in list(superstars_ratings.keys())} #first number in list is count of matches, second is accumlation of all ratings. x[1] / x[0] = average rating


def make_user_distribution_pie(data, id):
    superstars = []
    counts = []
    avg_ratings = []
    for superstar, (count, total_rating) in data.items():
        if count > 3 or len(data) < 10:
            superstars.append(superstar)
            counts.append(count)
            avg_ratings.append(total_rating / count)
    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(counts, labels=superstars, autopct='%1.1f%%', startangle=140)
    for autotext, avg_rating in zip(autotexts, avg_ratings):
        autotext.set_text(f"{autotext.get_text()}\nAVG: {avg_rating:.2f}")
    # Enhance aesthetics
    ax.axis('equal')
    ax.set_title('User Distribution and Average Ratings')
    ax.boxes()
    plt.savefig(f"static/plots/plot_{id}.png", bbox_inches='tight')

# make a distribution that shows histogram of how ALL matches are ranked
def make_user_distribution_hist(id):
    matches = Ratings.query.filter_by(user_index=id).all()
    ratings = [x.rating for x in matches]
    plt.xlabel("Rating")
    plt.ylabel("# of Times")
    plt.title("Rating Distribution")
    plt.xticks([1,2,3,4,5,6,7,8,9,10])
    plt.hist(ratings, bins=10, color='#86bf91',edgecolor="black")
    plt.savefig(f"static/plots/plot_{id}")



import pandas as pd
def get_matches():
     n = 2100
     df = pd.read_csv("aew.csv",index_col="Index")
     while n<=3100:
         url = f"https://www.cagematch.net//?id=8&nr=2287&page=7&s={n}"
         headers = {"Accept-Encoding": "deflate"}
         soup = BeautifulSoup(requests.get(url, headers=headers).content, "html.parser")

         links = [
             "https://www.cagematch.net/" + a["href"] for a in soup.select(".TCol a")
        ]
         matches = []
         for u in links:
             soup = BeautifulSoup(
                 requests.get(u, headers=headers).content, "html.parser"
             )
             match = {}
             for info in soup.select(".InformationBoxRow"):
                 match[info.select_one(".InformationBoxTitle").text.strip()] = info.select_one(".InformationBoxContents").text.strip()
             matches.append(match)
             print(match)
         for i in matches:
             i["Event:"] = i["Event:"].split("(")[0]
             i["Date:"] = i["Date:"][3:5]+"/"+i["Date:"][0:2]+"/"+i["Date:"][6:10]
         df = pd.concat([df,pd.DataFrame(matches)],ignore_index=True)
         n+=100
         df.to_csv("aew.csv")

#
# from sqlalchemy import create_engine
#
# def sql_freindly(csv):
#     conn = create_engine("sqlite:///instance/database.db")
#     df = pd.read_csv(csv,index_col="Index")
#     new = pd.read_csv("updated2.csv")
#     for i in range(0,len(df.values)):
#         match = df.iloc[i]["Fixture"].strip()
#         participants = []
#         for j in re.split(r'vs. |& |,',match):
#             participants.append(str(j.strip()))
#         if len(participants) <= 8:
#              query = [match, df.iloc[i]["Date"].strip(), df.iloc[i]["Promotion"].strip(), df.iloc[i]["Match type"].strip(), df.iloc[i]["Event"].strip()]
#              while len(participants) < 8:
#                  participants.append("n/a")
#              for z in participants:
#                 query.append(z)
#              new.loc[len(new)] = query
#     new.to_sql(name="Matches",con=conn,if_exists='append',index=False)
#     conn.dispose()