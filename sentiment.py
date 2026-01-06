from textblob import TextBlob
import pandas as pd

df = pd.read_csv("parsed_chat.csv")

def get_sentiment(text):
    polarity = TextBlob(str(text)).sentiment.polarity
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"

df["Sentiment"] = df["Message"].apply(get_sentiment)
print(df["Sentiment"].value_counts())
