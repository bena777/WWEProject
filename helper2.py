import re
from sqlalchemy import create_engine
import pandas as pd

def sql_freindly(csv):
    conn = create_engine("sqlite:///instance/database.db")
    df = pd.read_csv(csv,index_col="Index")
    new = pd.read_csv("updated2.csv")
    for i in range(0,len(df.values)):
        match = df.iloc[i]["Fixture"].strip()
        participants = []
        for j in re.split(r'vs. |& |,',match):
            participants.append(str(j.strip()))
        if len(participants) <= 8:
             query = [match, df.iloc[i]["Date"].strip(), df.iloc[i]["Promotion"].strip(), df.iloc[i]["Match type"].strip(), df.iloc[i]["Event"].strip()]
             while len(participants) < 8:
                 participants.append("n/a")
             for z in participants:
                query.append(z)
             new.loc[len(new)] = query
    new.to_sql(name="Matches",con=conn,if_exists='append',index=False)
    conn.dispose()
