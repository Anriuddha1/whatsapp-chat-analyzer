import streamlit as st
import pandas as pd
import re
from textblob import TextBlob
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import emoji
from collections import Counter
import nltk

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

st.markdown("""
<style>
.analysis-card {
    background-color: #0d0d1a;
    padding: 1rem;
    border-radius: 16px;
    min-height: 600px;   /* 🔥 SAME HEIGHT */
}
</style>
""", unsafe_allow_html=True)


# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="WhatsApp Chat Analyzer AI",
    page_icon="📈",
    layout="wide",
     menu_items={
         'Get Help': 'https://www.google.com/help',
        #  'Report a bug': "https://www.extremelycoolapp.com/bug",
        #  'About': "# This is a header. This is an *extremely* cool app!"
     }
)

st.title("📊 WhatsApp Chat Analyzer AI")
st.write("Upload your exported WhatsApp chat (.txt) to analyze group or individual members")

# ------------------ FILE UPLOAD ------------------
uploaded_file = st.file_uploader("Upload WhatsApp Chat File", type=["txt"])

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

        # 1️⃣ Check normal user message
        match = pattern.match(line)
        if match:
            date, time, user, message = match.groups()

            # skip empty or system-like messages
            if system_pattern.search(message):
                current_message = None
                continue

            current_message = [date, time, user, message]
            messages.append(current_message)
            continue

        # 2️⃣ Skip pure system lines
        if system_pattern.search(line):
            current_message = None
            continue

        # 3️⃣ Append ONLY real multiline text
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
        st.error("❌ Could not parse chat file")
        st.stop()

    st.success(f"✅ Parsed {len(df_all)} messages")

    df_all["Sentiment"] = df_all["Message"].apply(get_sentiment)
    df_all["DayName"] = df_all["Date"].dt.day_name()
    df_all["MonthName"] = df_all["Date"].dt.month_name()

    # ------------------ USER SELECTION ------------------
    users = ["Overall"] + sorted(df_all["User"].unique())
    selected_user = st.selectbox("Select Member for Analysis", users)

    df = df_all if selected_user == "Overall" else df_all[df_all["User"] == selected_user]

    st.header("👥 Overall Group Analysis" if selected_user == "Overall"
              else f"👤 Analysis for: {selected_user}")

    # ------------------ METRICS ------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Messages", len(df))
    col2.metric("Active Days", df["Date"].nunique())
    col3.metric("Avg Messages / Day", round(len(df) / df["Date"].nunique(), 2))

    left, right = st.columns(2)

    with left:
        st.subheader("📌 Messages per User")
        data = df_all["User"].value_counts() if selected_user == "Overall" else df["User"].value_counts()
        st.bar_chart(data)

    with right:
        st.subheader("🥧 Member Activity Distribution")
        fig, ax = plt.subplots()
        ax.pie(data.values, labels=data.index, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        st.pyplot(fig)


    left, right = st.columns(2)

    with left:
        st.subheader("🧠 Sentiment Distribution")
        st.bar_chart(df["Sentiment"].value_counts())

    with right:
        st.subheader("📈 Activity Timeline")
        timeline = df["Date"].value_counts().sort_index()
        st.line_chart(timeline)



    # ------------------ WORD CLOUD ------------------
    

    from wordcloud import STOPWORDS, WordCloud
    import matplotlib.pyplot as plt

    stop_words = STOPWORDS.union({
        "media", "omitted", "<media", "omitted>", "this", "message", "was", "deleted",
        "the", "and", "to", "a", "in", "of"
    })

    words = [
        word.lower() for word in " ".join(df["Message"]).split()
        if word.isalpha() and word.lower() not in stop_words
    ]

    clean_text = " ".join(words)

    wc = WordCloud(
        width=850,
        height=400,
        background_color="rgba(13, 13, 26, 0)",  # ✅ transparent background
        stopwords=stop_words,
        margin=0
    ).generate(clean_text)

    fig, ax = plt.subplots(figsize=(10, 4))

    # 🔴 REMOVE WHITE CANVAS (TRANSPARENT)
    fig.patch.set_facecolor((13/255, 13/255, 26/255, 0))
    ax.set_facecolor((13/255, 13/255, 26/255, 0))


    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")




    text = " ".join(df["Message"])
    # ------------------ COMMON WORDS ------------------
   

    stop_words = {
        "media", "omitted", "<media", "omitted>","this","message","was","deleted",
        "the", "and", "to", "a", "in", "of"
    }

    words = [
        word for word in text.split()
        if word.lower() not in stop_words
        and word.isalpha()
    ]

    common_words = Counter(words).most_common(20)
    df_common = pd.DataFrame(common_words, columns=["Word", "Count"])

    # 🔥 START INDEX FROM 1
    df_common.index = range(1, len(df_common) + 1)

    left, right = st.columns(2)

    with left:
        st.subheader("☁️ Word Cloud")
        st.pyplot(fig)   # your existing wordcloud fig

    with right:
        st.subheader("📝 Most Common Words")
        st.table(df_common)


    # ------------------ EMOJI ANALYSIS ------------------
    st.subheader("😄 Emoji Analysis")
    emojis = []
    for msg in df["Message"]:
        emojis.extend(extract_emojis(msg))

    if emojis:
        df_common1=pd.DataFrame(Counter(emojis).most_common(10),
                               columns=["Emoji", "Count"])
        df_common1.index = range(1, len(df_common1) + 1)
        st.table(df_common1)
    else:
        st.info("No emojis found")

    # ------------------ MOST ACTIVE DAY ------------------
    st.subheader("📅 Most Active Day")
    day_counts = df["DayName"].value_counts()
    st.success(f"🔥 {day_counts.idxmax()} ({day_counts.max()} messages)")
    st.bar_chart(day_counts)

    # ------------------ MOST ACTIVE MONTH ------------------
    st.subheader("🗓️ Most Active Month")
    month_counts = df["MonthName"].value_counts()
    st.success(f"🔥 {month_counts.idxmax()} ({month_counts.max()} messages)")
    st.bar_chart(month_counts)

    # ------------------ RAW DATA ------------------
    st.subheader("📄 Chat Preview")
    df["Message"] = df["Message"].str.lower().str.strip()

    df = df[
        (df["Message"] != "") &
        (~df["Message"].isin([
            "this message was deleted",
            "message deleted",
            "<media omitted>",
            "media omitted"
        ]))
    ]
    df = df[::-1]
    df_preview = df.copy()
    df_preview.index = range(1, len(df_preview) + 1)
    st.dataframe(df_preview)


else:
    st.info("📤 Upload a WhatsApp chat export (.txt file) to begin")
    st.markdown("""
    <div style='  background-color: #060032d9; padding: 2rem; border-radius: 16px; margin-top: 2rem;'>
        <h3 style='color: blue !important; margin-top: 0 !important;'>How to export your chat:</h3>
        <ol style='color: green;'>
            <li>Open WhatsApp and select a chat</li>
            <li>Tap ⋮ (menu) → More → Export chat</li>
            <li>Choose "Without Media"</li>
            <li>Upload the .txt file here</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)






# import streamlit as st
# import pandas as pd
# import re
# from textblob import TextBlob
# import matplotlib.pyplot as plt
# from wordcloud import WordCloud
# import emoji
# from collections import Counter
# import nltk
# import plotly.express as px
# import plotly.graph_objects as go

# # Download required NLTK data
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

# # ------------------ ELEGANT CSS ------------------
# st.markdown("""
# <style>
#     @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
#     * {
#         font-family: 'Inter', sans-serif;
#     }
    
#     .stApp {
#         background: linear-gradient(to bottom, #0f0c29, #302b63, #24243e);
#     }
    
#     /* Hide Streamlit branding */
#     #MainMenu {visibility: hidden;}
#     footer {visibility: hidden;}
    
#     /* Custom headers */
#     h1 {
#         color: #ffffff !important;
#         font-size: 2.8rem !important;
#         font-weight: 700 !important;
#         text-align: center;
#         margin-bottom: 0 !important;
#         letter-spacing: -0.5px;
#     }
    
#     h2 {
#         color: #e0e7ff !important;
#         font-size: 1.5rem !important;
#         font-weight: 600 !important;
#         margin-top: 3rem !important;
#         margin-bottom: 1.5rem !important;
#     }
    
#     h3 {
#         color: #c7d2fe !important;
#         font-size: 1.2rem !important;
#         font-weight: 500 !important;
#     }
    
#     /* Subtitle */
#     .subtitle {
#         text-align: center;
#         color: rgba(255, 255, 255, 0.7);
#         font-size: 1.1rem;
#         margin-bottom: 3rem;
#         font-weight: 300;
#     }
    
#     /* Metric cards */
#     [data-testid="stMetricValue"] {
#         font-size: 2rem !important;
#         font-weight: 700 !important;
#         color: #6366f1 !important;
#     }
    
#     [data-testid="stMetricLabel"] {
#         font-size: 0.9rem !important;
#         color: #64748b !important;
#         font-weight: 500 !important;
#     }
    
#     div[data-testid="metric-container"] {
#         background: white;
#         padding: 1.5rem;
#         border-radius: 16px;
#         box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
#         border: 1px solid rgba(226, 232, 240, 0.8);
#     }
    
#     /* File uploader */
#     [data-testid="stFileUploader"] {
#         background: white;
#         border-radius: 16px;
#         padding: 2rem;
#         border: 2px dashed #cbd5e1;
#         transition: all 0.3s ease;
#     }
    
#     [data-testid="stFileUploader"]:hover {
#         border-color: #6366f1;
#         box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.1);
#     }
    
#     /* Select box */
#     .stSelectbox > div > div {
#         background: white;
#         border-radius: 12px;
#         border: 1px solid #e2e8f0;
#     }
    
#     /* Info/Success boxes */
#     .stAlert {
#         background: white !important;
#         border-radius: 12px !important;
#         border-left: 4px solid #6366f1 !important;
#         padding: 1rem 1.5rem !important;
#     }
    
#     /* Dataframe */
#     [data-testid="stDataFrame"] {
#         background: white;
#         border-radius: 16px;
#         padding: 1rem;
#         box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
#     }
    
#     /* Remove padding */
#     .block-container {
#         padding-top: 3rem !important;
#         padding-bottom: 3rem !important;
#     }
    
#     /* Chart containers */
#     .chart-container {
#         background: white;
#         border-radius: 16px;
#         padding: 1.5rem;
#         box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
#         margin: 1rem 0;
#     }
    
#     /* Divider */
#     hr {
#         margin: 2rem 0;
#         border: none;
#         height: 1px;
#         background: linear-gradient(to right, transparent, rgba(255,255,255,0.2), transparent);
#     }
# </style>
# """, unsafe_allow_html=True)

# # ------------------ PAGE CONFIG ------------------
# st.set_page_config(
#     page_title="WhatsApp Analyzer",
#     page_icon="💬",
#     layout="wide"
# )

# # ------------------ HEADER ------------------
# st.markdown("<h1>💬 WhatsApp Chat Analyzer</h1>", unsafe_allow_html=True)
# st.markdown('<p class="subtitle">Unlock insights from your conversations</p>', unsafe_allow_html=True)

# # ------------------ FILE UPLOAD ------------------
# uploaded_file = st.file_uploader("", type=["txt"], label_visibility="collapsed")

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
#         match = pattern.match(line)
#         if match:
#             date, time, user, message = match.groups()
#             if system_pattern.search(message):
#                 current_message = None
#                 continue
#             current_message = [date, time, user, message]
#             messages.append(current_message)
#             continue
#         if system_pattern.search(line):
#             current_message = None
#             continue
#         if current_message is not None:
#             current_message[3] += " " + line

#     df = pd.DataFrame(messages, columns=["Date", "Time", "User", "Message"])
#     df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
#     df["Date"] = df["Date"].dt.date
#     df["Message"] = df["Message"].str.lower().str.strip()
#     df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
#     df = df.dropna(subset=["Date"])
#     return df.dropna()

# def get_sentiment(text):
#     polarity = TextBlob(str(text)).sentiment.polarity
#     if polarity > 0:
#         return "Positive"
#     elif polarity < 0:
#         return "Negative"
#     return "Neutral"

# def extract_emojis(text):
#     return [c for c in text if c in emoji.EMOJI_DATA]

# # ------------------ MAIN APP ------------------
# if uploaded_file is not None:
#     df_all = parse_chat(uploaded_file)

#     if df_all.empty:
#         st.error("Could not parse the chat file. Please check the format.")
#         st.stop()

#     st.success(f"✓ Parsed {len(df_all):,} messages successfully")

#     df_all["Sentiment"] = df_all["Message"].apply(get_sentiment)
#     df_all["DayName"] = df_all["Date"].dt.day_name()
#     df_all["MonthName"] = df_all["Date"].dt.month_name()

#     # User selection
#     st.markdown("<br>", unsafe_allow_html=True)
#     users = ["Overall"] + sorted(df_all["User"].unique())
#     selected_user = st.selectbox("Select member", users)

#     is_overall = selected_user == "Overall"
#     df = df_all if is_overall else df_all[df_all["User"] == selected_user]

#     # Metrics
#     st.markdown("<br>", unsafe_allow_html=True)
#     col1, col2, col3, col4 = st.columns(4)
#     col1.metric("Messages", f"{len(df):,}")
#     col2.metric("Active Days", f"{df['Date'].nunique():,}")
#     col3.metric("Avg/Day", f"{len(df) / df['Date'].nunique():.1f}")
#     col4.metric("Members", df_all["User"].nunique() if is_overall else 1)

#     # Timeline
#     st.markdown("<h2>Activity Timeline</h2>", unsafe_allow_html=True)
#     timeline = df.groupby("Date").size().reset_index(name='count')
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(
#         x=timeline['Date'], 
#         y=timeline['count'],
#         mode='lines',
#         fill='tozeroy',
#         line=dict(color='#6366f1', width=2),
#         fillcolor='rgba(99, 102, 241, 0.1)'
#     ))
#     fig.update_layout(
#         height=350,
#         margin=dict(l=20, r=20, t=20, b=20),
#         paper_bgcolor='white',
#         plot_bgcolor='white',
#         xaxis=dict(showgrid=False, title=""),
#         yaxis=dict(showgrid=True, gridcolor='#f1f5f9', title="Messages")
#     )
#     st.plotly_chart(fig, use_container_width=True)

#     # Two columns
#     col1, col2 = st.columns(2)

#     with col1:
#         st.markdown("<h2>Top Members</h2>", unsafe_allow_html=True)
#         data = df_all["User"].value_counts().head(10) if is_overall else df["User"].value_counts()
#         fig = go.Figure()
#         fig.add_trace(go.Bar(
#             x=data.values,
#             y=data.index,
#             orientation='h',
#             marker=dict(
#                 color=data.values,
#                 colorscale='Blues',
#                 showscale=False
#             )
#         ))
#         fig.update_layout(
#             height=400,
#             margin=dict(l=20, r=20, t=20, b=20),
#             paper_bgcolor='white',
#             plot_bgcolor='white',
#             xaxis=dict(showgrid=False, title=""),
#             yaxis=dict(showgrid=False, title="")
#         )
#         st.plotly_chart(fig, use_container_width=True)

#     with col2:
#         st.markdown("<h2>Sentiment</h2>", unsafe_allow_html=True)
#         sentiment_counts = df["Sentiment"].value_counts()
#         colors = {'Positive': '#10b981', 'Neutral': '#6b7280', 'Negative': '#ef4444'}
#         fig = go.Figure()
#         fig.add_trace(go.Bar(
#             x=sentiment_counts.index,
#             y=sentiment_counts.values,
#             marker=dict(color=[colors.get(x, '#6366f1') for x in sentiment_counts.index])
#         ))
#         fig.update_layout(
#             height=400,
#             margin=dict(l=20, r=20, t=20, b=20),
#             paper_bgcolor='white',
#             plot_bgcolor='white',
#             xaxis=dict(showgrid=False, title=""),
#             yaxis=dict(showgrid=False, title="")
#         )
#         st.plotly_chart(fig, use_container_width=True)

#     # Word Cloud
#     st.markdown("<h2>Most Used Words</h2>", unsafe_allow_html=True)
#     from wordcloud import STOPWORDS
#     stop_words = STOPWORDS.union({
#         "media", "omitted", "<media", "omitted>", "this", "message", "was", "deleted"
#     })
#     words = [word.lower() for word in " ".join(df["Message"]).split()
#              if word.isalpha() and word.lower() not in stop_words]
    
#     if words:
#         clean_text = " ".join(words)
#         wc = WordCloud(
#             width=1400, 
#             height=400, 
#             background_color="white",
#             stopwords=stop_words, 
#             colormap='viridis',
#             margin=5
#         ).generate(clean_text)
        
#         fig, ax = plt.subplots(figsize=(14, 4))
#         fig.patch.set_facecolor('white')
#         ax.set_facecolor('white')
#         ax.imshow(wc, interpolation="bilinear")
#         ax.axis("off")
#         plt.tight_layout(pad=0)
#         st.pyplot(fig)

#     # Activity patterns
#     col1, col2 = st.columns(2)

#     with col1:
#         st.markdown("<h2>By Day</h2>", unsafe_allow_html=True)
#         day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
#         day_counts = df["DayName"].value_counts().reindex(day_order, fill_value=0)
#         fig = go.Figure()
#         fig.add_trace(go.Bar(
#             x=day_counts.index,
#             y=day_counts.values,
#             marker=dict(color='#8b5cf6')
#         ))
#         fig.update_layout(
#             height=300,
#             margin=dict(l=20, r=20, t=20, b=20),
#             paper_bgcolor='white',
#             plot_bgcolor='white',
#             xaxis=dict(showgrid=False, title=""),
#             yaxis=dict(showgrid=False, title="")
#         )
#         st.plotly_chart(fig, use_container_width=True)

#     with col2:
#         st.markdown("<h2>Top Emojis</h2>", unsafe_allow_html=True)
#         emojis = []
#         for msg in df["Message"]:
#             emojis.extend(extract_emojis(msg))
#         if emojis:
#             emoji_counts = Counter(emojis).most_common(10)
#             df_emoji = pd.DataFrame(emoji_counts, columns=["Emoji", "Count"])
#             df_emoji.index = range(1, len(df_emoji) + 1)
#             st.dataframe(df_emoji, use_container_width=True, height=300)
#         else:
#             st.info("No emojis found")

#     # Raw data
#     st.markdown("<h2>Message History</h2>", unsafe_allow_html=True)
#     df_clean = df[
#         (df["Message"] != "") &
#         (~df["Message"].isin(["this message was deleted", "message deleted", 
#                              "<media omitted>", "media omitted"]))
#     ].copy()
#     df_clean = df_clean.sort_values('Date', ascending=False)
#     df_clean.index = range(1, len(df_clean) + 1)
#     st.dataframe(df_clean.head(100), use_container_width=True, height=400)

# else:
#     st.info("📤 Upload a WhatsApp chat export (.txt file) to begin")
#     st.markdown("""
#     <div style='background: white; padding: 2rem; border-radius: 16px; margin-top: 2rem;'>
#         <h3 style='color: #1e293b !important; margin-top: 0 !important;'>How to export your chat:</h3>
#         <ol style='color: #475569;'>
#             <li>Open WhatsApp and select a chat</li>
#             <li>Tap ⋮ (menu) → More → Export chat</li>
#             <li>Choose "Without Media"</li>
#             <li>Upload the .txt file here</li>
#         </ol>
#     </div>
#     """, unsafe_allow_html=True)