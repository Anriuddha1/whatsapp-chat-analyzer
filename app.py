import streamlit as st
import pandas as pd
import re
from textblob import TextBlob
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import emoji
from collections import Counter
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')


# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="WhatsApp Chat Analyzer AI",
    page_icon="📈",
    layout="wide",
    #  menu_items={
    #      'Get Help': 'https://www.extremelycoolapp.com/help',
    #      'Report a bug': "https://www.extremelycoolapp.com/bug",
    #      'About': "# This is a header. This is an *extremely* cool app!"
    #  }
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

    # ------------------ MESSAGES PER USER ------------------
    st.subheader("📌 Messages per User")
    data = df_all["User"].value_counts() if selected_user == "Overall" else df["User"].value_counts()
    st.bar_chart(data)

    # ------------------ PIE CHART ------------------
    st.subheader("🥧 Member Activity Distribution")
    fig, ax = plt.subplots()
    ax.pie(data.values, labels=data.index, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    st.pyplot(fig)

    # ------------------ SENTIMENT ------------------
    st.subheader("🧠 Sentiment Distribution")
    st.bar_chart(df["Sentiment"].value_counts())

    # ------------------ TIMELINE ------------------
    st.subheader("📈 Activity Timeline")
    timeline = df["Date"].value_counts().sort_index()
    st.line_chart(timeline)

    # ------------------ WORD CLOUD ------------------
    st.subheader("☁️ Word Cloud")

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

    st.pyplot(fig)


    text = " ".join(df["Message"])
    # ------------------ COMMON WORDS ------------------
    st.subheader("📝 Most Common Words")

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
    st.info("📂 Upload a WhatsApp .txt file to start analysis")