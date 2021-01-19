# Script to fix encoding and clean data of first dataset (from https://zenodo.org/record/4282522)

import pandas as pd

df = pd.read_csv('../../covid-dataset/COVID Fake News Data.csv')
print(df.iloc[0][0].encode('windows-1252').decode('utf-8'))
df['headlines'] = df['headlines'].apply(lambda x: x.encode('windows-1252', errors='ignore').decode('utf-8', errors='ignore'))
df['headlines'] = df['headlines'].str.replace('%', 'percent')
df.to_csv('../../covid-dataset/cleaned-COVID Fake News Data.csv', index=False)

