from flask_sqlalchemy import SQLAlchemy
from app import User, Matches, Ratings, db
import requests
from bs4 import BeautifulSoup
import time
import warnings
import re
warnings.simplefilter(action="ignore",category=FutureWarning)
import matplotlib.pyplot as plt


def get_recent_matches(date):
        cont = True
        url = f"https://www.cagematch.net//?id=8&nr=1&page=7"
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
        new_matches = []
        for i in matches:
            match = i["Fixture:"].strip()
            participants = []
            for j in re.split(r'vs. |& |,',match):
                participants.append(str(j.strip()))
            if len(participants) <= 8:
                query = [match, i["Date:"].strip(), i["Promotion:"].strip(),i["Match type:"].strip(), i["Event:"].strip()]
                while len(participants) < 8:
                    participants.append("n/a")
                for z in participants:
                    query.append(z)
                new_matches.append(query)
        return new_matches

def get_user_distribution(id):
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
    plt.savefig(f"static/plots/plot_{id}.png", bbox_inches='tight')

# make a distribution that shows histogram of how ALL matches are ranked



# for scrapping the match data
# def get_matches():
#      n = 10100
#      df = pd.DataFrame()
#      while n<=13100:
#          url = f"https://www.cagematch.net//?id=8&nr=1&page=7&s={n}"
#          headers = {"Accept-Encoding": "deflate"}
#          soup = BeautifulSoup(requests.get(url, headers=headers).content, "html.parser")
#
#          links = [
#              "https://www.cagematch.net/" + a["href"] for a in soup.select(".TCol a")
#         ]
#          matches = []
#          for u in links:
#              soup = BeautifulSoup(
#                  requests.get(u, headers=headers).content, "html.parser"
#              )
#              match = {}
#              for info in soup.select(".InformationBoxRow"):
#                  match[info.select_one(".InformationBoxTitle").text.strip()] = info.select_one(".InformationBoxContents").text.strip()
#              matches.append(match)
#              print(match)
#          for i in matches:
#              i["Event:"] = i["Event:"].split("(")[0]
#              i["Date:"] = i["Date:"][3:5]+"/"+i["Date:"][0:2]+"/"+i["Date:"][6:10]
#          df = pd.concat([df,pd.DataFrame(matches)],ignore_index=True)
#          n+=100
#          df.to_csv("matches3.csv")

# # for seperating csv into sql friendly csv
# df = pd.read_csv("matches3.csv",index_col="Index")
# new = pd.read_csv("updated.csv")
# for i in range(0,len(df.values)):
#     print(i)
#     match = df.iloc[i]["Fixture"].strip()
#     participants = []
#     for j in re.split(r'vs. |& |,',match):
#         participants.append(str(j.strip()))
#     if len(participants) <= 8:
#          query = [match, df.iloc[i]["Date"].strip(), df.iloc[i]["Promotion"].strip(), df.iloc[i]["Match type"].strip(), df.iloc[i]["Event"].strip()]
#          while len(participants) < 8:
#              participants.append("n/a")
#          for z in participants:
#             query.append(z)
#          print(query)
#          new.loc[len(new)] = query
# new.to_sql()