# import streamlit as st
# import pandas as pd
# import re
# from textblob import TextBlob
# import matplotlib.pyplot as plt
# from wordcloud import WordCloud
# import emoji
# from collections import Counter
# import nltk

# # Download required NLTK data for TextBlob
# @st.cache_resource
# def download_nltk_data():
#     try:
#         nltk.data.find('tokenizers/punkt')
#     except LookupError:
#         nltk.download('punkt', quiet=True)
#     try:
#         nltk.data.find('corpora/brown')
#     except LookupError:
#         nltk.download('brown', quiet=True)

# download_nltk_data()




# # ------------------ PAGE CONFIG ------------------
# st.set_page_config(
#     page_title="WhatsApp Chat Analyzer AI",
#     page_icon="📈",
#     layout="wide",
#      menu_items={
#          'Get Help': 'https://www.google.com/help',
#         #  'Report a bug': "https://www.extremelycoolapp.com/bug",
#         #  'About': "# This is a header. This is an *extremely* cool app!"
#      }
# )

# st.title("📊 WhatsApp Chat Analyzer AI")
# st.write("Upload your exported WhatsApp chat (.txt) to analyze group or individual members")

# # ------------------ FILE UPLOAD ------------------
# uploaded_file = st.file_uploader("Upload WhatsApp Chat File", type=["txt"])

# # ------------------ CHAT PARSER ------------------
# def parse_chat(file):
#     messages = []

#     pattern = re.compile(
#         r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s*'
#         r'(\d{1,2}:\d{2}[\u202f ]?(?:am|pm|AM|PM)?)\s*-\s*'
#         r'([^:]+):\s*(.*)$'
#     )

#     system_pattern = re.compile(
#         r'(added|removed|changed|joined|left|deleted|media omitted)',
#         re.IGNORECASE
#     )

#     current_message = None

#     for raw_line in file:
#         line = raw_line.decode("utf-8", errors="ignore").strip()

#         # 1️⃣ Check normal user message
#         match = pattern.match(line)
#         if match:
#             date, time, user, message = match.groups()

#             # skip empty or system-like messages
#             if system_pattern.search(message):
#                 current_message = None
#                 continue

#             current_message = [date, time, user, message]
#             messages.append(current_message)
#             continue

#         # 2️⃣ Skip pure system lines
#         if system_pattern.search(line):
#             current_message = None
#             continue

#         # 3️⃣ Append ONLY real multiline text
#         if current_message is not None:
#             current_message[3] += " " + line

#     df = pd.DataFrame(messages, columns=["Date", "Time", "User", "Message"])
#     df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
#     df["Date"] = df["Date"].dt.date
#     df["Message"] = df["Message"].str.lower().str.strip()
#     df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
#     df = df.dropna(subset=["Date"])

#     return df.dropna()


# # ------------------ SENTIMENT ------------------
# def get_sentiment(text):
#     polarity = TextBlob(str(text)).sentiment.polarity
#     if polarity > 0:
#         return "Positive"
#     elif polarity < 0:
#         return "Negative"
#     return "Neutral"

# # ------------------ EMOJI EXTRACT ------------------
# def extract_emojis(text):
#     return [c for c in text if c in emoji.EMOJI_DATA]

# # ------------------ MAIN APP ------------------
# if uploaded_file is not None:
#     df_all = parse_chat(uploaded_file)

#     if df_all.empty:
#         st.error("❌ Could not parse chat file")
#         st.stop()

#     st.success(f"✅ Parsed {len(df_all)} messages")

#     df_all["Sentiment"] = df_all["Message"].apply(get_sentiment)
#     df_all["DayName"] = df_all["Date"].dt.day_name()
#     df_all["MonthName"] = df_all["Date"].dt.month_name()

#     # ------------------ USER SELECTION ------------------
#     users = ["Overall"] + sorted(df_all["User"].unique())
#     selected_user = st.selectbox("Select Member for Analysis", users)

#     df = df_all if selected_user == "Overall" else df_all[df_all["User"] == selected_user]

#     st.header("👥 Overall Group Analysis" if selected_user == "Overall"
#               else f"👤 Analysis for: {selected_user}")

#     # ------------------ METRICS ------------------
#     col1, col2, col3 = st.columns(3)
#     col1.metric("Total Messages", len(df))
#     col2.metric("Active Days", df["Date"].nunique())
#     col3.metric("Avg Messages / Day", round(len(df) / df["Date"].nunique(), 2))

#     # ------------------ MESSAGES PER USER ------------------
#     st.subheader("📌 Messages per User")
#     data = df_all["User"].value_counts() if selected_user == "Overall" else df["User"].value_counts()
#     st.bar_chart(data)

#     # ------------------ PIE CHART ------------------
#     st.subheader("🥧 Member Activity Distribution")
#     fig, ax = plt.subplots()
#     ax.pie(data.values, labels=data.index, autopct="%1.1f%%", startangle=90)
#     ax.axis("equal")
#     st.pyplot(fig)

#     # ------------------ SENTIMENT ------------------
#     st.subheader("🧠 Sentiment Distribution")
#     st.bar_chart(df["Sentiment"].value_counts())

#     # ------------------ TIMELINE ------------------
#     st.subheader("📈 Activity Timeline")
#     timeline = df["Date"].value_counts().sort_index()
#     st.line_chart(timeline)

#     # ------------------ WORD CLOUD ------------------
#     st.subheader("☁️ Word Cloud")

#     from wordcloud import STOPWORDS, WordCloud
#     import matplotlib.pyplot as plt

#     stop_words = STOPWORDS.union({
#         "media", "omitted", "<media", "omitted>", "this", "message", "was", "deleted",
#         "the", "and", "to", "a", "in", "of"
#     })

#     words = [
#         word.lower() for word in " ".join(df["Message"]).split()
#         if word.isalpha() and word.lower() not in stop_words
#     ]

#     clean_text = " ".join(words)

#     wc = WordCloud(
#         width=850,
#         height=400,
#         background_color="rgba(13, 13, 26, 0)",  # ✅ transparent background
#         stopwords=stop_words,
#         margin=0
#     ).generate(clean_text)

#     fig, ax = plt.subplots(figsize=(10, 4))

#     # 🔴 REMOVE WHITE CANVAS (TRANSPARENT)
#     fig.patch.set_facecolor((13/255, 13/255, 26/255, 0))
#     ax.set_facecolor((13/255, 13/255, 26/255, 0))


#     ax.imshow(wc, interpolation="bilinear")
#     ax.axis("off")

#     st.pyplot(fig)


#     text = " ".join(df["Message"])
#     # ------------------ COMMON WORDS ------------------
#     st.subheader("📝 Most Common Words")

#     stop_words = {
#         "media", "omitted", "<media", "omitted>","this","message","was","deleted",
#         "the", "and", "to", "a", "in", "of"
#     }

#     words = [
#         word for word in text.split()
#         if word.lower() not in stop_words
#         and word.isalpha()
#     ]

#     common_words = Counter(words).most_common(20)
#     df_common = pd.DataFrame(common_words, columns=["Word", "Count"])

#     # 🔥 START INDEX FROM 1
#     df_common.index = range(1, len(df_common) + 1)

#     st.table(df_common)
#     # ------------------ EMOJI ANALYSIS ------------------
#     st.subheader("😄 Emoji Analysis")
#     emojis = []
#     for msg in df["Message"]:
#         emojis.extend(extract_emojis(msg))

#     if emojis:
#         df_common1=pd.DataFrame(Counter(emojis).most_common(10),
#                                columns=["Emoji", "Count"])
#         df_common1.index = range(1, len(df_common1) + 1)
#         st.table(df_common1)
#     else:
#         st.info("No emojis found")

#     # ------------------ MOST ACTIVE DAY ------------------
#     st.subheader("📅 Most Active Day")
#     day_counts = df["DayName"].value_counts()
#     st.success(f"🔥 {day_counts.idxmax()} ({day_counts.max()} messages)")
#     st.bar_chart(day_counts)

#     # ------------------ MOST ACTIVE MONTH ------------------
#     st.subheader("🗓️ Most Active Month")
#     month_counts = df["MonthName"].value_counts()
#     st.success(f"🔥 {month_counts.idxmax()} ({month_counts.max()} messages)")
#     st.bar_chart(month_counts)

#     # ------------------ RAW DATA ------------------
#     st.subheader("📄 Chat Preview")
#     df["Message"] = df["Message"].str.lower().str.strip()

#     df = df[
#         (df["Message"] != "") &
#         (~df["Message"].isin([
#             "this message was deleted",
#             "message deleted",
#             "<media omitted>",
#             "media omitted"
#         ]))
#     ]
#     df = df[::-1]
#     df_preview = df.copy()
#     df_preview.index = range(1, len(df_preview) + 1)
#     st.dataframe(df_preview)


# else:
#     st.info("📂 Upload a WhatsApp .txt file to start analysis")


import streamlit as st
import pandas as pd
import re
from textblob import TextBlob
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import emoji
from collections import Counter
import nltk
import plotly.express as px
import plotly.graph_objects as go

# Download required NLTK data for TextBlob
@st.cache_resource
def download_nltk_data():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        nltk.data.find('corpora/brown')
    except LookupError:
        nltk.download('brown', quiet=True)

download_nltk_data()

# ------------------ CUSTOM CSS ------------------
st.markdown("""
<style>
    /* Main background gradient */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Custom header styling */
    h1 {
        color: #ffffff !important;
        font-size: 3rem !important;
        font-weight: 800 !important;
        text-align: center;
        margin-bottom: 0.5rem !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    h2, h3 {
        color: #ffffff !important;
        font-weight: 600 !important;
        margin-top: 2rem !important;
    }
    
    /* Card-like containers */
    .stMetric {
        background: rgba(255, 255, 255, 0.95);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* File uploader styling */
    .stFileUploader {
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 2px dashed #667eea;
    }
    
    /* Select box styling */
    .stSelectbox {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 10px;
        padding: 0.5rem;
    }
    
    /* Data frame styling */
    .stDataFrame {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 1rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    /* Success/Info messages */
    .stSuccess, .stInfo {
        background: rgba(255, 255, 255, 0.95) !important;
        border-radius: 10px !important;
        border-left: 5px solid #10b981 !important;
    }
    
    /* Chart containers */
    .element-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    /* Subtitle text */
    .subtitle {
        color: rgba(255, 255, 255, 0.9);
        text-align: center;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="WhatsApp Chat Analyzer AI",
    page_icon="💬",
    layout="wide",
    menu_items={
        'Get Help': 'https://www.google.com/help',
    }
)

# ------------------ HEADER ------------------
st.title("💬 WhatsApp Chat Analyzer AI")
st.markdown('<p class="subtitle">Discover insights from your conversations with beautiful analytics</p>', unsafe_allow_html=True)

# ------------------ FILE UPLOAD ------------------
uploaded_file = st.file_uploader("📤 Upload Your WhatsApp Chat Export (.txt)", type=["txt"])

# ------------------ CHAT PARSER ------------------
def parse_chat(file):
    messages = []
    pattern = re.compile(
        r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s*'
        r'(\d{1,2}:\d{2}[\u202f ]?(?:am|pm|AM|PM)?)\s*-\s*'
        r'([^:]+):\s*(.*)$'
    )
    system_pattern = re.compile(
        r'(added|removed|changed|joined|left|deleted|media omitted)',
        re.IGNORECASE
    )
    current_message = None

    for raw_line in file:
        line = raw_line.decode("utf-8", errors="ignore").strip()
        match = pattern.match(line)
        if match:
            date, time, user, message = match.groups()
            if system_pattern.search(message):
                current_message = None
                continue
            current_message = [date, time, user, message]
            messages.append(current_message)
            continue
        if system_pattern.search(line):
            current_message = None
            continue
        if current_message is not None:
            current_message[3] += " " + line

    df = pd.DataFrame(messages, columns=["Date", "Time", "User", "Message"])
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df["Date"] = df["Date"].dt.date
    df["Message"] = df["Message"].str.lower().str.strip()
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Date"])
    return df.dropna()

# ------------------ SENTIMENT ------------------
def get_sentiment(text):
    polarity = TextBlob(str(text)).sentiment.polarity
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    return "Neutral"

# ------------------ EMOJI EXTRACT ------------------
def extract_emojis(text):
    return [c for c in text if c in emoji.EMOJI_DATA]

# ------------------ MAIN APP ------------------
if uploaded_file is not None:
    df_all = parse_chat(uploaded_file)

    if df_all.empty:
        st.error("❌ Could not parse chat file. Please check the format.")
        st.stop()

    st.success(f"✅ Successfully parsed {len(df_all):,} messages!")

    df_all["Sentiment"] = df_all["Message"].apply(get_sentiment)
    df_all["DayName"] = df_all["Date"].dt.day_name()
    df_all["MonthName"] = df_all["Date"].dt.month_name()

    # ------------------ USER SELECTION ------------------
    st.markdown("---")
    users = ["📊 Overall Group"] + sorted(df_all["User"].unique())
    selected_user = st.selectbox("🔍 Select Member for Analysis", users)

    is_overall = selected_user == "📊 Overall Group"
    df = df_all if is_overall else df_all[df_all["User"] == selected_user]

    st.header("👥 Overall Group Analytics" if is_overall else f"👤 {selected_user}'s Activity")

    # ------------------ METRICS ------------------
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💬 Total Messages", f"{len(df):,}")
    with col2:
        st.metric("📅 Active Days", df["Date"].nunique())
    with col3:
        st.metric("📊 Avg/Day", f"{len(df) / df['Date'].nunique():.1f}")
    with col4:
        st.metric("👥 Participants", df_all["User"].nunique() if is_overall else "1")

    st.markdown("---")

    # ------------------ INTERACTIVE CHARTS ------------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📌 Message Distribution")
        data = df_all["User"].value_counts() if is_overall else df["User"].value_counts()
        fig = px.bar(x=data.index, y=data.values, 
                     labels={'x': 'User', 'y': 'Messages'},
                     color=data.values,
                     color_continuous_scale='Viridis')
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🥧 Activity Share")
        fig = px.pie(values=data.values, names=data.index, hole=0.4)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    # ------------------ SENTIMENT ------------------
    st.subheader("🧠 Sentiment Analysis")
    sentiment_counts = df["Sentiment"].value_counts()
    fig = go.Figure(data=[
        go.Bar(x=sentiment_counts.index, y=sentiment_counts.values,
               marker_color=['#10b981', '#f59e0b', '#ef4444'])
    ])
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

    # ------------------ TIMELINE ------------------
    st.subheader("📈 Activity Timeline")
    timeline = df.groupby("Date").size().reset_index(name='Messages')
    fig = px.line(timeline, x='Date', y='Messages', 
                  markers=True, line_shape='spline')
    fig.update_traces(line_color='#667eea', line_width=3)
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # ------------------ WORD CLOUD ------------------
    st.subheader("☁️ Word Cloud")
    from wordcloud import STOPWORDS
    stop_words = STOPWORDS.union({
        "media", "omitted", "<media", "omitted>", "this", "message", "was", "deleted",
        "the", "and", "to", "a", "in", "of"
    })
    words = [word.lower() for word in " ".join(df["Message"]).split()
             if word.isalpha() and word.lower() not in stop_words]
    clean_text = " ".join(words)

    if clean_text:
        wc = WordCloud(width=1200, height=400, background_color="white",
                      stopwords=stop_words, colormap='viridis',
                      margin=10).generate(clean_text)
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)

    # ------------------ COMMON WORDS & EMOJIS ------------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📝 Top 15 Words")
        text = " ".join(df["Message"])
        stop_words = {"media", "omitted", "<media", "omitted>", "this", "message", "was", "deleted",
                     "the", "and", "to", "a", "in", "of"}
        words = [word for word in text.split()
                if word.lower() not in stop_words and word.isalpha()]
        common_words = Counter(words).most_common(15)
        df_common = pd.DataFrame(common_words, columns=["Word", "Count"])
        df_common.index = range(1, len(df_common) + 1)
        st.dataframe(df_common, use_container_width=True)

    with col2:
        st.subheader("😄 Top 10 Emojis")
        emojis = []
        for msg in df["Message"]:
            emojis.extend(extract_emojis(msg))
        if emojis:
            df_emoji = pd.DataFrame(Counter(emojis).most_common(10),
                                   columns=["Emoji", "Count"])
            df_emoji.index = range(1, len(df_emoji) + 1)
            st.dataframe(df_emoji, use_container_width=True)
        else:
            st.info("No emojis found in messages")

    # ------------------ ACTIVITY PATTERNS ------------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📅 Most Active Day")
        day_counts = df["DayName"].value_counts()
        st.success(f"🔥 **{day_counts.idxmax()}** with {day_counts.max():,} messages")
        fig = px.bar(x=day_counts.index, y=day_counts.values,
                    labels={'x': 'Day', 'y': 'Messages'},
                    color=day_counts.values, color_continuous_scale='Blues')
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🗓️ Most Active Month")
        month_counts = df["MonthName"].value_counts()
        st.success(f"🔥 **{month_counts.idxmax()}** with {month_counts.max():,} messages")
        fig = px.bar(x=month_counts.index, y=month_counts.values,
                    labels={'x': 'Month', 'y': 'Messages'},
                    color=month_counts.values, color_continuous_scale='Purples')
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)

    # ------------------ RAW DATA ------------------
    st.markdown("---")
    st.subheader("📄 Message History")
    df_clean = df[
        (df["Message"] != "") &
        (~df["Message"].isin([
            "this message was deleted", "message deleted",
            "<media omitted>", "media omitted"
        ]))
    ].copy()
    df_clean = df_clean[::-1]
    df_clean.index = range(1, len(df_clean) + 1)
    st.dataframe(df_clean, use_container_width=True, height=400)

else:
    st.info("👆 Please upload a WhatsApp chat export file (.txt) to begin analysis")
    st.markdown("""
    ### 📖 How to Export WhatsApp Chat:
    1. Open WhatsApp chat
    2. Tap the three dots (⋮) → **More** → **Export chat**
    3. Choose **Without Media**
    4. Upload the .txt file here
    """)