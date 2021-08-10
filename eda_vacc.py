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

################
file_path = "country_vaccinations.csv\country_vaccinations.csv"
#file_path = "country_vaccinations.csv\country_vaccinations5.csv"
#file_path = "C:\\Users\G3\Documents\Gabriel\Profile\Projects\covid_vaccine\country_vaccinations\country_vaccinations7.csv"
df = pd.read_csv(file_path)

df.shape
df.head()
df.columns

df.isnull().sum()

################
# (1) Daily vaccinations and daily vaccinations raw
dvac = df[['country', 'date', 'total_vaccinations', 
           'daily_vaccinations_raw', 'daily_vaccinations']].copy() #important to use copy, otherwise SettingwithCopyWarning pops up

# Finding same consecutive values in 'total_vaccinations'
dvac['csc_value'] = dvac.total_vaccinations.groupby([dvac['country'],dvac['total_vaccinations']]).diff(1) == 0

# Filling gaps of missing values between same consecutive values in 'csc_value' and 'total_vaccinations'
dvac['csc_value'].fillna(method='bfill', inplace=True)

dvac.loc[dvac['csc_value'] == True, 'total_vaccinations'] = ((dvac['total_vaccinations'].groupby([dvac['country'], dvac['csc_value']]))
                                                        .transform(lambda x:x.bfill()))

# (2) Creates new variable from 'total_vaccinations' grouped by country
dvac['filltv'] = (dvac['total_vaccinations'].groupby(dvac['country'])               
               .transform(lambda x:x.bfill())) #back fill -- fills back 'total_vaccinations' by group 'country'

# (3) identifying nan values in 'total vaccinations'
# Counts the number of consecutive missing values 
dvac['nan_values'] = (dvac.total_vaccinations.isnull().astype(int).groupby(dvac.total_vaccinations.notnull().astype(int).cumsum())
                      .transform('sum')
                      .transform(lambda x:x+1 if x != 0 else 0)
                      .shift(1))

# (4) Calculates difference from consecutive unique different values in 'filltv'
dvac.loc[dvac.nan_values != 0, 'diff_filltv'] = ((dvac['filltv'].groupby([dvac['country']]).diff(-1)*(-1)) #'diff' calculates difference between rows. multiply by minus 1 to get positive result. can try abs())
                                             .replace(-0, np.nan) #'replace' removes 0's with nan
                                             .shift(1) #'shift' changes result to one row foward
                                             .groupby([dvac['country']]).transform(lambda x:x.ffill())) #'transform' fills the nan values with substraction

# (5) Divides the difference by the number of missing values
dvac['avg_filltv'] = (dvac['diff_filltv']/dvac['nan_values'])

# (6) Substitutes values with data from 'daily_vaccinations_raw'
dvac.loc[dvac.nan_values == 0, 'avg_filltv'] = dvac['daily_vaccinations_raw']

# Sets values to zero based on variable 'test'
dvac.loc[dvac.csc_value == True, 'avg_filltv'] = 0

# (7) moving avg
dvac['MA'] = round(dvac.groupby('country')['avg_filltv'] #groups by 'country' and uses 'dvr_new'
                   .rolling(window=7, min_periods=1) #takes 7 values. minimum 1 value for first values
                   .mean(), 0).reset_index(0,drop=True) #it's the avg. needs reset_index, otherwise it won't work

# If 'fup' is a missing value, 'MA' also turns to a missing value
dvac.loc[dvac.filltv.isna(), 'MA'] = np.nan

# Difference
dvac['diff'] = dvac['MA'] - dvac['daily_vaccinations']

df1 = dvac.loc[dvac['diff'].notna() & dvac['diff'] != 0]

################
### Monthly heatmap
dvac = df[['country', 'date', 'total_vaccinations', 'people_vaccinated', 'people_fully_vaccinated',
           'daily_vaccinations_raw', 'daily_vaccinations']].copy()

def country_heatmap(country, df=dvac):
    df = df.loc[df['country'] == country].copy()
    
    # time period
    df['date'] = pd.to_datetime(df['date']).apply(lambda x: x.date())
    start_date = min(df['date'])
    last_date = max(df['date'])
    timeperiod = last_date-start_date
    
    # weekdays and week number
    country_calendar = [start_date + datetime.timedelta(i) for i in range(timeperiod.days+1)] #list with days in timeperiod
    weekdays = [i.weekday() for i in country_calendar]
    weeknumber = [(i.strftime('%V')) for i in country_calendar]
    
    # daily vaccinations data
    vc = df['daily_vaccinations']
    vcr = df['daily_vaccinations_raw']    
    text = [str(i) for i in country_calendar]
    
    # subplots
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
        title_font_size = 20,
        title_y = 0.98,        
        plot_bgcolor = ('rgb(255,255,255)')
        )
    fig.layout.annotations[0].update(y=1.03)
    fig.layout.annotations[1].update(y=1.03)
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
    fig.show()

country_heatmap('France')

################
### Find the max number of people vaccinated per 100 as of the most recent date
# Columns for country, date and total vaccinates
df['country'].nunique()
total_per_country = df[['country', 'date', 'people_fully_vaccinated_per_hundred']].copy()

# Filling empty values by group with foward fill (ffill)
total_per_country['people_fully_vaccinated_per_hundred'] = (total_per_country['people_fully_vaccinated_per_hundred'].groupby(total_per_country['country'])
                                                            .transform(lambda x:x.ffill()))

# Filtering na values
total_per_country.dropna(inplace=True)

df_southa = total_per_country[total_per_country['country'].isin(['Argentina','Bolivia','Brasil','Chile','Colombia','Ecuador','Paraguay','Peru','Uruguay','Venezuela'])]
df_northa = total_per_country[total_per_country['country'].isin(['Canada','Mexico','United States'])]
#df_westeurope = total_per_country[total_per_country['country'].isin(['Belgium','Denmark','France','Germany','Ireland','Italy','Netherlands','Portugal','Spain','United Kingdom'])]

# line chart
fig = px.line(df_southa, x='date', y='people_fully_vaccinated_per_hundred', color='country', text='country')

fig.update_traces(mode='markers+lines',
                  hovertemplate=
                  '<b>%{text}</b><br>'+
                  'Fully vaccinated per 100: <b>%{y:.2f}</b><br>'+
                  '<extra>%{x}</extra>')

fig.update_layout(
    title = 'Vaccination progress in South America',
    title_font_size=20,
    hoverlabel=dict(font_size=12), 
    hovermode='x'
    )

fig.update_yaxes(
    title="People fully vaccinated per hundred"
    )

fig.show()

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

#getting iso code for countries
vaccine_per_country = pd.merge(vaccine_per_country, df[['country','iso_code']].copy().drop_duplicates(), 
                            how='left', on='country')
vaccine_per_country['valz'] = 1

### Choropleth map
vaccines_list = vaccine_per_country['vaccines'].drop_duplicates().to_list()
visible = np.array(vaccines_list)
vaccine_per_country['text'] = 'Country: ' + vaccine_per_country['country'] + '<br>' + 'Vaccine: ' + vaccine_per_country['vaccines']

traces = []
buttons = []
for vac in vaccines_list:
    traces.append(go.Choropleth(
        locations = vaccine_per_country.loc[vaccine_per_country.vaccines==vac]['iso_code'],
        z = vaccine_per_country.loc[vaccine_per_country.vaccines==vac]['valz'],
        coloraxis = 'coloraxis',
        colorscale = 'Blues',
        autocolorscale = False,
        marker_line_color = 'white',
        hovertemplate=vaccine_per_country.loc[vaccine_per_country.vaccines==vac]['text'] + '<extra></extra>',
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


