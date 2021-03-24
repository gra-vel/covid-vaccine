# -*- coding: utf-8 -*-
"""
Editor de Spyder

Este es un archivo temporal.
"""
import pandas as pd
import plotly.express as px
import plotly.io as pio 
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

for i in df.columns:
    df.i.unique()
    df.i.value_counts()

## daily vaccinations and daily vaccinations raw
dvac = df[['country', 'date', 'total_vaccinations', 'people_vaccinated', 'people_fully_vaccinated',
           'daily_vaccinations_raw', 'daily_vaccinations']].copy()
#filling values upwards in total_vaccinations by country
dvac['fup'] = (dvac['total_vaccinations'].groupby(dvac['country']).transform(lambda x:x.bfill()))


#if dvac['nan_values'] > 0:
dvac.loc[dvac['nan_values'] > 0, 'new_avg2'] = dvac['nan_values'] + 1
dvac['new_avg'] = dvac['fup']/(dvac['nan_values']+1)



                      
dvac['substract'] = dvac['fup'] - dvac['fup'].shift(1)





## Find the max number of people vaccinated as of the most recent date
# Columns for country, date and total vaccinates
total_per_country = df[['country', 'date', 'people_fully_vaccinated']]
# Filling empty values by group with foward fill (ffill)
total_per_country['people_fully_vaccinated'] = (total_per_country['people_fully_vaccinated'].groupby(total_per_country['country'])
                                                                                            .transform(lambda x:x.ffill()))
# Filtering na values
total_per_country.dropna(inplace=True)
# line
fig = px.line(total_per_country, x='date', y='people_fully_vaccinated', color='country')
fig.show()

# Filtering latest date
total_per_country = total_per_country[total_per_country.groupby(['country'])['date'].transform(max) == df['date']].dropna()
                                                                                    



# separate total vaccinated and max date. merge them
df1 = df[['country', 'date', 'people_fully_vaccinated']]
total_per_country.fillna(method='ffill', inplace=True)
total_per_country.loc[total_per_country.groupby(['country'])['people_fully_vaccinated'].idxmax()]
total_per_country.groupby(['country'], sort=False)['date'].max()

