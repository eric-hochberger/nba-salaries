# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
from basketball_reference_web_scraper import client
import pandas as pd
from bs4 import BeautifulSoup
import re
import requests
import lxml.html as lh
import unidecode


# %%
# advanced_stats = client.players_advanced_season_totals(season_end_year=2019)
#
# normal_stats = client.players_season_totals(season_end_year=2018)
#
# testdf = pd.DataFrame(advanced_stats)
#
#
# # %%
# testdf['minutes_played_total'] = testdf.groupby('name').minutes_played.transform('sum')
# testdf['proportion'] = testdf['minutes_played']/testdf['minutes_played_total']
# num_cols = list(testdf.select_dtypes(include=['int', 'float64']))
# unwanted_num_cols = ['age', 'minutes_played', 'games_played']
# for col in unwanted_num_cols:
#     num_cols.remove(col)
# for col in num_cols:
#     testdf[col] = testdf[col]*testdf['proportion']
# testdf = testdf.groupby('name').agg('sum')
#
# player_counts = pd.DataFrame(testdf.groupby('name').size())


# %%
def clean_advanced(year):
    advanced_stats = client.players_advanced_season_totals(season_end_year=year)
    df = pd.DataFrame(advanced_stats)
    # Handle quirk in data where traded players are represented as multiple observations
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
    num_cols = list(df.select_dtypes(include=['int', 'float64']))
    unwanted_num_cols = ['age']
    for col in unwanted_num_cols:
        num_cols.remove(col)
    df_grouped = df.groupby('name')[num_cols].agg('sum')
    unwanted_num_cols1 = ['minutes_played']
    for col in unwanted_num_cols1:
        num_cols.remove(col)
    for col in num_cols:
        df_grouped[col] = (df_grouped[col]/df_grouped['minutes_played'])*48
    df_grouped['age'] = df.groupby('name')['age'].agg('mean')
    df_grouped['minutes_played'] = df.groupby('name')['minutes_played'].agg('mean')
    df_grouped['games_played'] = df.groupby('name')['games_played'].agg('mean')
    df_grouped['games_started'] = df.groupby('name')['games_started'].agg('mean')
    df_grouped['year'] = year
    return df_grouped

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
    for k in range(2,page_total + 1):
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


# %%
#Get Player Statistics
all_stats_2011_2020 = []
for year in range(2011, 2021):
    df = clean_advanced(year)
    df1 = clean_basic(year)
    stats = pd.merge(df, df1, how='inner', left_on=['name'], right_on=['name'])
    all_stats_2011_2020.append(stats)
all_stats_2011_2020 = pd.concat(all_stats_2011_2020)
all_stats_2011_2020.isna().sum()
all_stats_2011_2020 = all_stats_2011_2020.reset_index()
all_stats_2011_2020 = all_stats_2011_2020.drop('year_y', 1)
all_stats_2011_2020.rename(columns={'year_x' : 'year'}, inplace=True)

# %%
#Get Salaries
salarydf = []
for year in range(2011, 2021):
    salarydf.append(GetSalaries(str(year)))


# %%
salarydf = pd.concat(salarydf)


# %%
salarydf = salarydf.reset_index()


# %%
for i in range(len(salarydf)):
    salarydf['name'][i] = unidecode.unidecode(salarydf['name'][i])
    salarydf['name'][i] = re.sub('\*', '', salarydf['name'][i])
    salarydf['name'][i] = re.sub('\.', '', salarydf['name'][i])
    salarydf['name'][i] = salarydf['name'][i].replace("'", '')
    salarydf['name'][i] = salarydf['name'][i].replace(" ", '_').lower()


# %%
all_stats_2011_2020 = all_stats_2011_2020.reset_index()
for i in range(len(all_stats_2011_2020)):
    all_stats_2011_2020['name'][i] = str(all_stats_2011_2020['name'][i])
    all_stats_2011_2020['name'][i] = unidecode.unidecode(all_stats_2011_2020['name'][i])
    all_stats_2011_2020['name'][i] = re.sub('\*', '', all_stats_2011_2020['name'][i])
    all_stats_2011_2020['name'][i] = re.sub('\.', '', all_stats_2011_2020['name'][i])
    all_stats_2011_2020['name'][i] = all_stats_2011_2020['name'][i].replace("'", '')
    all_stats_2011_2020['name'][i] = all_stats_2011_2020['name'][i].replace(" ", '_').lower()


# %%
fulldf = pd.merge(all_stats_2011_2020, salarydf, how='inner', left_on=['name', 'year'], right_on=['name', 'year'])
fulldf['year'].value_counts()


# %%
salary_cap = pd.read_csv('/Users/erichochberger/Desktop/Stat_301_03_Final_Project/salary_cap_history.csv')

for i in range(len(salary_cap)):
    salary_cap.loc[i, 'Cap'] = re.sub('\$', '', salary_cap['Cap'][i])
    salary_cap.loc[i, 'Cap'] = re.sub(',', '', salary_cap['Cap'][i])
    salary_cap.loc[i, 'Cap'] = int(salary_cap['Cap'][i])
    salary_cap.loc[i, 'Year'] = re.sub('[0-9]{2}-', '', salary_cap['Year'][i])

d = {'Year' : ['2019', '2020'], 'Cap' : [101869000, 109140000], 'Cap_2015' : ['', '']}

salary_cap = salary_cap.append(pd.DataFrame(d)).reset_index().drop('Cap_2015', 1)

salary_cap.rename(columns={'Year' : 'year'}, inplace=True)
for i in range(len(salary_cap)):
    salary_cap['year'][i] = int(salary_cap['year'][i])
salary_cap = salary_cap.set_index('year').to_dict()['Cap']

fulldf['cap'] = fulldf['year'].map(salary_cap)
fulldf['cap'].isna().sum()

fulldf['salary_prop'] = fulldf['salary']/fulldf['cap']

unwanted_cols = ['SALARY', 'NAME', 'RK', 'index_x', 'index_y', 'age_x', 'proportion']
for col in unwanted_cols:
    fulldf = fulldf.drop(col, 1)

fulldf = fulldf[(fulldf['minutes_played'] > 500)]

fulldf.to_csv('nba_salaries_and_stats_2011_2020', index=False)
