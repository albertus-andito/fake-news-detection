# Script to clean second dataset (from https://github.com/parthpatwa/covid19-fake-news-detection)


import re
import pandas as pd

def demoji(text):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               u"\U00010000-\U0010ffff"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)


data = pd.read_csv('../../covid-dataset/Constraint_English_Train.csv', encoding='utf-8')

data['tweet'] = data['tweet'].astype(str)
data['tweet'] = data['tweet'].apply(lambda x: demoji(x))
data['tweet'] = data['tweet'].apply(lambda x: re.sub(r"http\S+", "", x))
data.to_csv('../../covid-dataset/cleaned-Constraint_English_Train.csv', index=False, encoding='utf-8')  # save to csv file
