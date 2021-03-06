#reused inports form demo --> This is not stealing :)
import streamlit as st
import twint
import pandas as pd
import re
import numpy as np
import datetime
import time
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer, pipeline

def get_hashtags(text):
    """Function to extract hashtags from tweets"""
    hashtags = re.findall(r'\#\w+', text.lower())
    return hashtags


def get_mentions(text):
    """Function to extract mentions from tweets"""
    mentions = re.findall(r'\@\w+', text.lower())
    return mentions


def remove_content(text):
    """Clean up text by removing urls, mentions & hashtags"""
    text = re.sub(r"http\S+", "", text)  # remove urls
    text = re.sub(r'\S+\.com\S+', '', text)  # remove urls
    text = re.sub(r'\@\w+', '', text)  # remove mentions
    text = re.sub(r'\#\w+', '', text)  # remove hashtags
    return text


def process_text(text):
    """Apply remove content & lower text"""
    text = remove_content(text)
    text = re.sub('[^a-zA-ZÀ-ÿ]', ' ', text.lower())  # remove non-alphabets
    return text

####### Streamlit Side panel #########
# side panel for twint configuration
add_text = st.sidebar.title(
    'The Prisoners Of Hack-A-Ton'
)

# Create date selection for streamlit
today = datetime.date.today()
add_yesterday = today - datetime.timedelta(days=7)

start_date = st.sidebar.date_input('Start date', add_yesterday)
end_date = st.sidebar.date_input('End date', today)

# Warning if dates are not correct.
if start_date > end_date:
    st.sidebar.error('End date must fall after start date.')

if end_date > today:
    st.sidebar.error("Sorry but we can't see in the future, please a correct end date.")

# add_text_search = st.sidebar.write('Enter your search keyword:')
add_profile = st.sidebar.text_input('Enter twitter username', '')
######## End sidebar #######

######## Streamit main #######
start_date = start_date.strftime('%Y-%m-%d')
end_date = end_date.strftime('%Y-%m-%d')
# st.write(start_date, end_date)

# Config Twint
c = twint.Config()
c.Limit = 100
c.lang = "en"
c.Since = start_date
c.Until = end_date
c.Username = add_profile
c.Hide_output = True
c.Pandas = True
c.Popular_tweets = True
c.Store_object = True
#

# if keyword(s) for search, start showing graph in dashboard
if add_profile:
    print('Searching now...')
    
    st.title("Report for Twitter user :" + add_profile)
    twint.run.Search(c)
    df = twint.storage.panda.Tweets_df
    #time.sleep(10)
    print("Done")

    if len(df) > 1:
        df['date'] = pd.to_datetime(df['date'])

        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        df['tweets'] = df['tweet'].apply(lambda x: len(x.split()))
        df['hashtags'] = df['tweet'].apply(lambda x: get_hashtags(x))
        df['mentions'] = df['tweet'].apply(lambda x: get_mentions(x))
        df['num_hashtags'] = df['tweet'].apply(lambda x: len(get_hashtags(x)))
        df['num_mentions'] = df['tweet'].apply(lambda x: len(get_mentions(x)))
        df['hour'] = df['date'].dt.hour

        # Example plot: hour vs length
        df_HL = df[["hour", "tweets"]]
        df_HL = df_HL.groupby(['hour']).mean()

        st.title('Average tweets per hour.')
        st.header('from {} to {}'.format(start_date, end_date))
        st.bar_chart(data=df_HL, width=0, height=0, use_container_width=True)

        # Example plot: top 10 hashtags
        hashes = df['hashtags'].tolist()
        tags = []
        for x in hashes:
            if x:
                tags.extend(x)
        df_tags = pd.DataFrame(tags, columns=['hashtag'])

        st.title('Top 10 hashtags.')
        st.header('from {} to {}'.format(start_date, end_date))
        st.bar_chart(data=df_tags['hashtag'].value_counts().head(
            10), width=0, height=0, use_container_width=True)

        df = df[['tweet']]
        df['cleaned_tweets'] = df['tweet'].apply(lambda x: process_text(x))
        df['cleaned_tweets'] = df['cleaned_tweets'].str.rstrip().str.lstrip()
        s = '.'.join(df.loc[:, 'cleaned_tweets'])

        # Example NLP with transformers (transformer + pytorch)
        # initialize the model architecture and weights
        model = T5ForConditionalGeneration.from_pretrained("t5-small")

        # initialize the model tokenizer
        tokenizer = T5Tokenizer.from_pretrained("t5-small")

        inputs = tokenizer.encode(
            "summarize: " + s, return_tensors="pt", max_length=512, truncation=True)

        # generate the summarization output
        outputs = model.generate(
            inputs,
            max_length=510,
            min_length=40,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True)

        st.header("This is a summary from all the tweets form " + start_date + " till " + end_date)

        st.write(tokenizer.decode(outputs[0]))
        classifier = pipeline('sentiment-analysis')

        label = classifier(tokenizer.decode(outputs[0]))[0]["label"]
        score = classifier(tokenizer.decode(outputs[0]))[0]["score"]

        st.write("The sentiment of this summary is: " + label  + " with a score of: " + str(round(score, 5)))

        for tweet in df['cleaned_tweets']:
            st.write("")
            st.write(tweet)

            classifier = pipeline('sentiment-analysis')

            label = classifier(tweet)[0]["label"]
            score = classifier(tweet)[0]["score"]

            st.write("The sentiment of this tweet is : " + label  + " with a score of: " + str(round(score, 5)))

        

#### Extra streamlit for info ####
# Add drop down menu
# add_selectbox = st.sidebar.selectbox(
    # 'How would you like to be contacted?',
    # ('Twitter', 'Mail', 'Mobile phone')
# )

# Add a slider to the sidebar:
# add_slider = st.sidebar.slider(
    # 'Select a range of values',
    # 0.0, 100.0, (25.0, 75.0)
# )
