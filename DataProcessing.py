from basketball_reference_web_scraper import client
import pandas as pd
from bs4 import BeautifulSoup
import re
import requests
import lxml.html as lh
import numpy as np

def clean_advanced(year):
    advanced_stats = client.players_advanced_season_totals(season_end_year=year)
    df = pd.DataFrame(advanced_stats)
    # Handle quirk in data where traded players are             represented as multiple observations
    df['minutes_played_total'] = df.groupby('name').minutes_played.transform('sum')
    df['proportion'] = df['minutes_played']/df['minutes_played_total']
    num_cols = list(df.select_dtypes(include=['int', 'float64']))
    unwanted_num_cols = ['age', 'minutes_played', 'games_played']
    for col in unwanted_num_cols:
        num_cols.remove(col)
    for col in num_cols:
        df[col] = df[col]*df['proportion']
    df_grouped = df.groupby('name')[num_cols].agg('sum')
    df_grouped['age'] = df.groupby('name')['age'].agg('mean')
    df_grouped['year'] = year
    return df_grouped
def clean_basic(year):
    basic_stats = client.players_season_totals(season_end_year=year)
    df = pd.DataFrame(basic_stats)
    df = df.groupby('name').agg('sum')
    num_cols = list(df.select_dtypes(include=['int', 'float64']))
    unwanted_num_cols = ['age', 'minutes_played', 'games_played', 'games_started']
    for col in unwanted_num_cols:
        num_cols.remove(col)
    for col in num_cols:
        df[col] = (df[col]/df['minutes_played'])*48
    df['year'] = year
    return df

def ScrapePage(url):
    r = requests.get(url)
    # Get number of pages
    soup = BeautifulSoup(r.content, features='html.parser')
    page_total = soup.find(class_="page-numbers").get_text()
    page_total = re.sub('.*of', '', page_total).strip()
    page_total = int(page_total)
    r = requests.get(url)
    doc = lh.fromstring(r.content)
    tr_elements = doc.xpath('//tr')
    # Create empty list
    col = []
    i = 0
    # For each row, store each first element (header) and an empty list
    for t in tr_elements[0]:
        i += 1
        name = t.text_content()
        col.append((name, []))
    for j in range(len(tr_elements)):
        # T is our j'th row
        T = tr_elements[j]
        # i is the index of our column
        i = 0
        # Iterate through each element of the row
        for t in T.iterchildren():
            data = t.text_content()
            # Check if row is empty
            if i > 0:
                # Convert any numerical value to integers
                try:
                    data = int(data)
                except:
                    pass
            # Append the data to the empty list of the i'th column
            col[i][1].append(data)
            # Increment i for the next column
            i += 1
    dict = ({title: column for (title, column) in col})
    return dict, page_total


def GetSalaries(year):
    df = []
    dict = {}
    url = 'http://www.espn.com/nba/salaries/_/year/' + year + '/'
    data, page_total = ScrapePage(url)
    df.append(pd.DataFrame(data))
#Get Salary Data
    for k in range(2,page_total):
        url = 'http://www.espn.com/nba/salaries/_/year/' + year + '/page/' + str(k)
        Dict = ScrapePage(url)[0]
        df.append(pd.DataFrame(Dict))
    df = pd.concat(df)
    df['year'] = int(year)
    df = df[df['RK'] != "RK"]
    df.reset_index(inplace=True, drop=True)
    #Convert salary to numeric
    for i in range(len(df)):
        df.loc[i, 'name'] = re.sub(',.*', '', df['NAME'][i])
        df.loc[i, 'salary'] = re.sub('\$', '', df['SALARY'][i])
        df.loc[i, 'salary'] = re.sub(',', '', df['salary'][i])
 #Get Rid of text rows
        df['salary'] = pd.to_numeric(df['salary'])
    return df




# ##Get Player Statistics
# advanced_stats = client.players_advanced_season_totals(season_end_year=2019)

# normal_stats = client.players_season_totals(season_end_year=2018)

# testdf = pd.DataFrame(advanced_stats)

# #Append group-level sum, want to create columns w/ weighted averages of percentages for players w/ >1 records
# testdf['minutes_played_total'] = testdf.groupby('name').minutes_played.transform('sum')
# testdf['proportion'] = testdf['minutes_played']/testdf['minutes_played_total']

# num_cols = list(testdf.select_dtypes(include=['int', 'float64']))
# num_cols.remove('age')
# for col in num_cols:
#     testdf[col] = testdf[col]*testdf['proportion']
# testdf = testdf.groupby('name').agg('mean')

# player_counts = pd.DataFrame(testdf.groupby('name').size())

# #player_counts[player_counts['0'] > 1]

# # Functional way to collapse basic stats dataframe
# testdf1 = pd.DataFrame(normal_stats)
# testdf1 = testdf1.groupby('name').agg('sum')

#url = 'http://www.espn.com/nba/salaries/_/year/2018/'

#One Year All Salaries



year = '2018'


test = []
test = GetSalaries('2018')

bigdf = []
for i in range(2011, 2020):
    bigdf.append(GetSalaries(str(i)))
bigdf = pd.concat(bigdf)

test.loc[2, 'name'] = re.sub(',.*', '', test['NAME'][2])

#Read in salary cap history
salary_cap = pd.read_csv('/Users/erichochberger/Desktop/Stat_301_03_Final_Project/salary_cap_history.csv')

for i in range(len(salary_cap)):
    salary_cap.loc[i, 'Cap'] = re.sub('\$', '', salary_cap['Cap'][i])
    salary_cap.loc[i, 'Cap'] = re.sub(',', '', salary_cap['Cap'][i])
    salary_cap.loc[i, 'Cap'] = int(salary_cap['Cap'][i])
    salary_cap.loc[i, 'Year'] = re.sub('[0-9]{2}-', '', salary_cap['Year'][i])

d = {'Year' : [2019, 2020], 'Cap' : [101869000, 109140000], 'Cap_2015' : ['', '']}

salary_cap.append(pd.DataFrame(d)).reset_index().drop('Cap_2015', 1)
sys.executable