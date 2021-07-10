# -*- coding: utf-8 -*-
"""
Editor de Spyder

Este es un archivo temporal.
"""
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
pio.renderers.default='browser'
import sys

sys.exit("Noooooo!. Con el F9")

################
file_path = "country_vaccinations.csv\country_vaccinations.csv"
#file_path = "country_vaccinations.csv\country_vaccinations5.csv"
df = pd.read_csv(file_path)

df.shape
df.head()
df.columns

df.isnull().sum()

################
# (1) Daily vaccinations and daily vaccinations raw
dvac = df[['country', 'date', 'total_vaccinations', 'people_vaccinated', 'people_fully_vaccinated',
           'daily_vaccinations_raw', 'daily_vaccinations']].copy() #important to use copy, otherwise SettingwithCopyWarning pops up

# Finding same consecutive values in 'total_vaccinations'
dvac['test'] = dvac.total_vaccinations.groupby([dvac['country'],dvac['total_vaccinations']]).diff(1) == 0

# Filling gaps of missing values between same consecutive values in 'test' and 'total_vaccinations'
dvac['test'].fillna(method='bfill', inplace=True)

dvac.loc[dvac['test'] == True, 'total_vaccinations'] = ((dvac['total_vaccinations'].groupby([dvac['country'], dvac['test']]))
                                                        .transform(lambda x:x.bfill()))

# (2) Creates new variable from 'total_vaccinations' grouped by country
dvac['fup'] = (dvac['total_vaccinations'].groupby(dvac['country'])               
               .transform(lambda x:x.bfill())) #back fill -- fills back 'total_vaccinations' by group 'country'

# Counts the number of consecutive missing values 
dvac['nan_values'] = (dvac.total_vaccinations.isnull().astype(int).groupby(dvac.total_vaccinations.notnull().astype(int).cumsum())
                      .transform('sum')
                      .transform(lambda x:x+1 if x != 0 else 0)
                      .shift(1))

# (3) identifying na values in 'total vaccinations'

# (4) Calculates difference from consecutive unique different values in 'fup'
dvac.loc[dvac.nan_values != 0, 'avg_nan'] = ((dvac['fup'].groupby([dvac['country']]).diff(-1)*(-1)) #'diff' calculates difference between rows. multiply by minus 1 to get positive result. can try abs())
                                             .replace(-0, np.nan) #'replace' removes 0's with nan
                                             .shift(1) #'shift' changes result to one row foward
                                             .groupby([dvac['country']]).transform(lambda x:x.ffill())) #'transform' fills the nan values with substraction

# (5) Divides the difference by the number of missing values
dvac['dvr_new'] = (dvac['avg_nan']/dvac['nan_values']) #.fillna(0)

# (6) Substitutes values with data from 'daily_vaccinations_raw'
dvac.loc[dvac.nan_values == 0, 'dvr_new'] = dvac['daily_vaccinations_raw']

# Sets values to zero based on variable 'test'
dvac.loc[dvac.test == True, 'dvr_new'] = 0

# (7) moving avg
dvac['MA'] = round(dvac.groupby('country')['dvr_new'] #groups by 'country' and uses 'dvr_new'
                   .rolling(window=7, min_periods=1) #takes 7 values. minimum 1 value for first values
                   .mean(), 0).reset_index(0,drop=True) #it's the avg. needs reset_index, otherwise it won't work

# If 'fup' is a missing value, 'MA' also turns to a missing value
dvac.loc[dvac.fup.isna(), 'MA'] = np.nan

# Difference
#dvac.loc[dvac.MA == 0, 'MA'] = np.nan

dvac['diff'] = dvac['MA'] - dvac['daily_vaccinations']

df1 = dvac.loc[dvac['diff'] != 0]

df1 = dvac[~dvac.MA.isin(dvac.daily_vaccinations)]

################
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

################
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
################
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
vaccined_people = pd.merge(vaccine_per_country, total_per_country, how='left', on='country')

#number of countries using each type of vaccine
vaccined_people.groupby('vaccines')['country'].count()

#mean for each vaccine
#vaccined_people.groupby('vaccines')['people_fully_vaccinated'].mean()
vaccined_people.groupby('vaccines')['people_fully_vaccinated_per_hundred'].mean()

#getting iso code for countries
vaccined_people2 = pd.merge(vaccined_people, df[['country','iso_code']].copy().drop_duplicates(), 
                            how='left', on='country')
vaccined_people2['valz'] = 1

# separate total vaccinated and max date. merge them
# df1 = df[['country', 'date', 'people_fully_vaccinated']]
# total_per_country.fillna(method='ffill', inplace=True)
# total_per_country.loc[total_per_country.groupby(['country'])['people_fully_vaccinated'].idxmax()]
# total_per_country.groupby(['country'], sort=False)['date'].max()

### Choropleth map
vaccines_list = vaccined_people2['vaccines'].drop_duplicates().to_list()
visible = np.array(vaccines_list)
vaccined_people2['text'] = 'Country: ' + vaccined_people2['country'] + '<br>' + 'Vaccine: ' + vaccined_people2['vaccines']

traces = []
buttons = []
for vac in vaccines_list:
    traces.append(go.Choropleth(
        locations = vaccined_people2.loc[vaccined_people2.vaccines==vac]['iso_code'],
        z = vaccined_people2.loc[vaccined_people2.vaccines==vac]['valz'],
        coloraxis = 'coloraxis',
        colorscale = 'Blues',
        autocolorscale = False,
        marker_line_color = 'white',
        hovertemplate=vaccined_people2.loc[vaccined_people2.vaccines==vac]['text'] + '<extra></extra>',
        visible = True if vac == vaccines_list[0] else False))
    
    buttons.append(dict(label=vac,
                        method='update',
                        args=[{'visible':list(visible==vac)},
                              {'title':f'<b>Countries using {vac}</b>'}]))

updatemenus = [dict(type = 'buttons',
                    active = 0,
                    showactive=True,
                    direction = 'down', 
                    xanchor = 'left', 
                    yanchor = 'top', 
                    x = -0.01, 
                    y = 1, 
                    font = dict(size=9, color='#000000'),
                    buttons = buttons)
               ]

fig = go.Figure(data=traces,
                layout=dict(updatemenus=updatemenus,
                            coloraxis=dict(colorscale='Blues')))

first_title = vaccines_list[0]
fig.update_layout(title=f"<b>Countries using {first_title}</b>",title_x=0.5,
                  coloraxis_showscale=False,                  
                  showlegend = False)

fig.show()


