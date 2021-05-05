# -*- coding: utf-8 -*-
"""
Editor de Spyder

Este es un archivo temporal.
"""
import pandas as pd
import numpy as np
import datetime
#from datetime import datetime
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
#file_path = "country_vaccinations.csv\country_vaccinations2.csv"
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

def country_heatmap(country, df=dvac):
    df = df.loc[df['country'] == country].copy()
    #time period
    df['date'] = pd.to_datetime(df['date']).apply(lambda x: x.date())
    start_date = min(df['date'])
    last_date = max(df['date'])
    timeperiod = last_date-start_date
    #weekdays and week number
    country_calendar = [start_date + datetime.timedelta(i) for i in range(timeperiod.days+1)]
    weekdays = [i.weekday() for i in country_calendar]
    weeknumber = [(i.strftime('%V')) for i in country_calendar]
    #z
    vc = df['daily_vaccinations']
    vcr = df['daily_vaccinations_raw']
    #annotation
    text = [str(i) for i in country_calendar]
    #subplots
    fig = make_subplots(1,2, 
                        shared_yaxes=False,
                        subplot_titles=('daily_vaccinations','daily_vaccinations_raw'))
    #daily_vaccinations heatmap
    fig.add_trace(
        go.Heatmap(
            x=weekdays,
            y=weeknumber,
            z=vc,
            text=text,
            xgap=2,
            ygap=2,
            showscale=False,
            colorscale='viridis',
            hovertemplate='Weekday: %{x}<br>Week number: %{y}<br>Vaccinations: %{z}<br>Date: %{text}<extra></extra>'),1,1) 
    #daily_vaccinations_raw heatmap
    fig.add_trace(
        go.Heatmap(
            x=weekdays,
            y=weeknumber,
            z=vcr,
            text=text,
            xgap=2,
            ygap=2,
            showscale=False,
            colorscale='viridis',
            hovertemplate='Weekday: %{x}<br>Week number: %{y}<br>Vaccinations: %{z}<br>Date: %{text}<extra></extra>'),1,2)
    
    fig.update_layout(
        title = country,
        plot_bgcolor = ('rgb(255,255,255)')
        )
    fig.layout.annotations[0].update(y=1.05)
    fig.layout.annotations[1].update(y=1.05)
    fig.update_xaxes(
        tickmode="array",
        ticktext=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
        tickvals=[0,1,2,3,4,5,6],
        title="",
        side="top"
        )
    fig.update_yaxes(
        title="Week Nr.",
        autorange="reversed"
        )
    #print(fig.layout)
    fig.show()

country_heatmap('Ecuador')

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

