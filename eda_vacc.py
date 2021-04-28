# -*- coding: utf-8 -*-
"""
Editor de Spyder

Este es un archivo temporal.
"""
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
pio.renderers.default='browser'
import sys

sys.exit("Noooooo!. Con el F9")

"""
- Zdes' mozhno razdelit' strany za ispolsuemuyu vaktsinu. Nuzhno ispol'zovat' razdelenye str.
S etoy informatsiyei, mozhno vyasnit' kto postavit' bol'sche vaktsinii
- Tile graph (geom_tile) in plotly. Dni v mesyatsyakh
"""

file_path = "country_vaccinations.csv\country_vaccinations.csv"
df = pd.read_csv(file_path)

df.shape
df.info
df.columns
df['total_vaccinations'].describe()
df.isnull().sum()

df['country'].head()
df.loc[df.groupby(['country'])['date'].idxmax()]

### Daily vaccinations and daily vaccinations raw
dvac = df[['country', 'date', 'total_vaccinations', 'people_vaccinated', 'people_fully_vaccinated',
           'daily_vaccinations_raw', 'daily_vaccinations']].copy() #important to use copy, otherwise SettingwithCopyWarning pops up

#filling values upwards in total_vaccinations by country
dvac['fup'] = (dvac['total_vaccinations'].groupby(dvac['country'])
               .transform(lambda x:x.bfill())) #back fill -- fills back 'total_vaccinations' by group 'country'

#identifying na values in 'total vaccinations'
dvac['nan_values'] = (dvac['total_vaccinations'].isnull().groupby([dvac['country'],dvac['fup']]) #total_vaccinations instead of people_vaccinated. is_null affects only missing values
                      .transform('sum')) 
dvac.loc[dvac.nan_values > 0, 'nan_values'] += 1

#substracting new values from inmediate previous. 
#dvac.loc[dvac.nan_values != 0, 'avg_nan'] = (dvac['fup'].diff(-1)*(-1)).shift(1) #first try. it works but it's incomplete
dvac.loc[dvac.nan_values != 0, 'avg_nan'] = ((dvac['fup'].groupby([dvac['country']]).diff(-1)*(-1)) #'diff' calculates difference between rows. multiply by minus 1 to get positive result. can try abs())
                                             .replace(-0, np.nan) #'replace' removes 0's with nan
                                             .shift(1) #'shift' changes result to one row foward
                                             .groupby([dvac['country']]).transform(lambda x:x.ffill())) #'transform' fills the nan values with substraction

#dvac['dvr_new'] = round(dvac['avg_nan']/dvac['nan_values'], 4) #round 0 here returns error in MA
dvac['dvr_new'] = (dvac['avg_nan']/dvac['nan_values']).fillna(0)

#completing values with data from daily_vaccinations_raw
dvac.loc[dvac.nan_values == 0, 'dvr_new'] = dvac['daily_vaccinations_raw']

#moving avg
#dvac.dvr_new.fillna(0, inplace = True) #first try
dvac['MA'] = round(dvac.groupby('country')['dvr_new'] #groups by 'country' and uses 'dvr_new'
                   .rolling(window=7, min_periods=1) #takes 7 values. minimum 1 value for first values
                   .mean(), 0).reset_index(0,drop=True) #it's the avg. needs reset_index, otherwise it won't work

dvac.loc[dvac.MA == 0, 'MA'] = np.nan

dvac['diff'] = dvac['MA'] - dvac['daily_vaccinations']

df1 = dvac[~dvac.MA.isin(df.daily_vaccinations)]

### Monthly heatmap
dvac = df[['country', 'date', 'total_vaccinations', 'people_vaccinated', 'people_fully_vaccinated',
           'daily_vaccinations_raw', 'daily_vaccinations']].copy()
dvac.dtypes
dvac['date'] = pd.to_datetime(dvac['date'])
dvac['weekday'] = dvac['date'].dt.dayofweek #could transform to str
dvac['week'] = dvac['date'].dt.isocalendar().week
dvac['week'] = dvac['week'].astype('int64') 
dvac['month'] = dvac['date'].dt.month

#dvac['week'] = dvac['week'].astype(str)
#dvac['weekday'] = dvac['weekday'].astype(str)

#px.version
dvac_alb = dvac.loc[dvac['country'] == 'Albania']
dvac_alb = dvac_alb.drop(columns=['country','date', 'total_vaccinations', 'people_vaccinated', 
                                  'people_fully_vaccinated', 'daily_vaccinations_raw'])
#dvac_alb2 = dvac_alb[['daily_vaccinations', 'weekday', 'week']].to_dict()
dvac_alb2 = dvac_alb.pivot(index="week",columns="weekday", values="daily_vaccinations")
dvac_alb2 = pd.merge(dvac_alb2, dvac_alb[['week','month']].drop_duplicates(), how='left', left_on='week', right_on='week')

#imshow
fig = px.imshow(dvac_alb2) #without merge
fig.show()

def country_heatmap(df, country):
    df = df.loc[df['country'] == country]
    df = df.drop(columns=['country','date', 'total_vaccinations', 'people_vaccinated', 
                                  'people_fully_vaccinated', 'daily_vaccinations_raw'])
    df = df.pivot(index='week', columns='weekday', values='daily_vaccinations')
    fig = go.Figure(data=go.Heatmap(
        z = df,
        x = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']))
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        height=85 * len(df[0]), #len(df[0])
        width=600)
    fig.show()
    
country_heatmap(dvac, 'Anguilla')
len(dvac_alb2[0])*85
# =============================================================================
# #subplots
# fig = go.Figure(data=go.Heatmap(
#     z = dvac_alb2,
#     x = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']))
# fig.show()
# 
# fig = make_subplots(2,2)
# fig.add_trace(
#     go.Heatmap(z = dvac_alb2), 1,1)
# fig.add_trace(
#     go.Heatmap(z = dvac_alb2), 1,2)
# fig.add_trace(
#     go.Heatmap(z = dvac_alb2), 2,1)
# fig.add_trace(
#     go.Heatmap(z = dvac_alb2), 2,2)
# fig.show()
# 
# #first version
# fig = make_subplots(1,3) #three columns for each quarter
# fig.add_trace(
#     go.Heatmap(z = dvac_alb2.loc[dvac_alb2['month']==1, 0:6], coloraxis='coloraxis'), 1,1)
# fig.add_trace(
#     go.Heatmap(z = dvac_alb2.loc[dvac_alb2['month']==2, 0:6], coloraxis='coloraxis'), 1,2)
# fig.add_trace(
#     go.Heatmap(z = dvac_alb2.loc[dvac_alb2['month']==3, 0:6], coloraxis='coloraxis'), 1,3)
# #fig.update_layout(coloraxis = {'colorscale':'viridis'})
# fig.show()
# 
# #second version
# fig = make_subplots(1,3) 
# fig.add_trace(
#     go.Heatmap(z = dvac_alb2.loc[dvac_alb2['month']==1, 0:6], y=dvac_alb2.loc[dvac_alb2['month']==1, ['week']], 
#                zmin=0, zmax=1000), 1,1)
# fig.add_trace(
#     go.Heatmap(z = dvac_alb2.loc[dvac_alb2['month']==2, 0:6], y=dvac_alb2.loc[dvac_alb2['month']==2, ['week']],
#                zmin=0, zmax=1000), 1,2)
# fig.add_trace(
#     go.Heatmap(z = dvac_alb2.loc[dvac_alb2['month']==3, 0:6], y=dvac_alb2.loc[dvac_alb2['month']==3, ['week']],
#                zmin=0, zmax=1000), 1,3)
# fig.show()
# 
# #third version
# fig = make_subplots(rows=1, cols=3, print_grid=True, shared_yaxes=True) 
# fig.add_trace(
#     go.Heatmap(z = dvac_alb2.loc[dvac_alb2['month']==1, 0:6], y=['a','b','c','d'],
#                 zmin=0, zmax=1000), 1,1)
# fig.add_trace(
#     go.Heatmap(z = dvac_alb2.loc[dvac_alb2['month']==2, 0:6], #, y=['1','2','3','4']
#                 zmin=0, zmax=1000), 1,2)
# fig.add_trace(
#     go.Heatmap(z = dvac_alb2.loc[dvac_alb2['month']==3, 0:6], #, y=['1','2','3']
#                 zmin=0, zmax=1000, connectgaps=False), 1,3)
# fig.update_yaxes(autorange="reversed")
# =============================================================================







alb_dict = {}
for i in dvac_alb['week']:
    for j in dvac_alb['weekday']:
        if i in alb_dict:
            alb_dict[i].append(j)
        else:
            alb_dict[i] = [j]

dict_test = {1:0,
             2:4}
1 in dict_test
dict_test[1].append(2)

fig = px.imshow(dvac_alb2['daily_vaccinations'],
                x = dvac_alb2['weekday'],
                y = dvac_alb2['week'])
fig.show()
####
data = {1:{6:0},
        2:{0:64,
           1:64,
           2:63,
           3:66,
           4:62,
           5:62,
           6:58}}
data_rows = list(data.values())
data2 = []

for i in range(0,len(data_rows)):
    data2.append(list(data_rows[i].values()))

#works
fig = go.Figure(data=go.Heatmap(
    z  = data2,
    x = ["0","1","2","3","4","5","6"], 
    y = ["1","2"]))
fig.show()

#doesn't works
fig = px.imshow(data2,
                labels = dict(x='weekday', y='week', color='total'),
                x = ["0","1","2","3","4","5","6"],
                y = ["1","2"])
fig.show()
####
fig = px.imshow(dvac_alb.daily_vaccinations.tolist(),
                labels = dict(x="weekday", color='daily_vaccinations'),
                x = dvac_alb.weekday.tolist().nunique(), 
                y = dvac_alb.week.tolist())
fig.show()

#go.version
fig = go.Figure(data=go.Heatmap(dvac_alb.daily_vaccinations.tolist()),
                x = dvac_alb.weekday.tolist(), 
                y = dvac_alb.week.tolist())
fig.show()

######
### Find the max number of people vaccinated as of the most recent date
# Columns for country, date and total vaccinates
df['country'].nunique()
total_per_country = df[['country', 'date', 'people_fully_vaccinated']].copy()

# Filling empty values by group with foward fill (ffill)
total_per_country['people_fully_vaccinated'] = (total_per_country['people_fully_vaccinated'].groupby(total_per_country['country'])
                                                .transform(lambda x:x.ffill()))

# Filtering na values
total_per_country.dropna(inplace=True)

# line chart
# fig = px.line(total_per_country, x='date', y='people_fully_vaccinated', color='country')
# fig.show()

# Filtering latest date
total_per_country = (total_per_country[total_per_country.groupby(['country'])['date']
                                      .transform(max) == total_per_country['date']]
                     .dropna()
                     .reset_index(drop=True))

### Find the max number of people vaccinated per 100 as of the most recent date
# Columns for country, date and total vaccinates
df['country'].nunique()
total_per_country = df[['country', 'date', 'people_fully_vaccinated_per_hundred']].copy()

# Filling empty values by group with foward fill (ffill)
total_per_country['people_fully_vaccinated_per_hundred'] = (total_per_country['people_fully_vaccinated_per_hundred'].groupby(total_per_country['country'])
                                                            .transform(lambda x:x.ffill()))

# Filtering na values
total_per_country.dropna(inplace=True)

# line chart
# fig = px.line(total_per_country, x='date', y='people_fully_vaccinated_per_hundred', color='country')
# fig.show()

# Filtering latest date
total_per_country = (total_per_country[total_per_country.groupby(['country'])['date']
                                      .transform(max) == total_per_country['date']]
                     .dropna()
                     .reset_index(drop=True))

### Vaccines per country
vaccine_per_country = df[['country', 'vaccines']].copy()
vaccine_per_country.drop_duplicates(keep='first', inplace=True)

#breaking 'vaccines' into different rows
vaccine_series = vaccine_per_country['vaccines'].str.split(', ').apply(pd.Series,1).stack()
vaccine_series.index = vaccine_series.index.droplevel(-1)
vaccine_series.name = 'vaccines'

vaccine_per_country.drop(columns=['vaccines'], inplace=True)
vaccine_per_country = vaccine_per_country.join(vaccine_series)

### Merging two datasets
vaccined_people = pd.merge(total_per_country, vaccine_per_country, how='left', on='country')
vaccined_people.groupby('vaccines')['country'].count()
#vaccined_people.groupby('vaccines')['people_fully_vaccinated'].mean()
vaccined_people.groupby('vaccines')['people_fully_vaccinated_per_hundred'].mean()





# separate total vaccinated and max date. merge them
df1 = df[['country', 'date', 'people_fully_vaccinated']]
total_per_country.fillna(method='ffill', inplace=True)
total_per_country.loc[total_per_country.groupby(['country'])['people_fully_vaccinated'].idxmax()]
total_per_country.groupby(['country'], sort=False)['date'].max()

