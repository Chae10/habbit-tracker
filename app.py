import streamlit as st
import requests
import random
from datetime import date, timedelta
import pandas as pd
import altair as alt
from openai import OpenAI

# =========================
# 페이지 설정
# =========================
st.set_page_config(
    page_title="AI 습관 트래커",
    page_icon="📊",
    layout="wide"
)

st.title("📊 AI 습관 트래커")

# =========================
# 사이드바 API 키
# =========================
with st.sidebar:
    st.header("🔑 API 설정")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    weather_api_key = st.text_input("OpenWeatherMap API Key", type="password")

# =========================
# Session State 초기화
# =========================
if "records" not in st.session_state:
    demo_dates = [date.today() - timedelta(days=i) for i in range(6, 0, -1)]
    st.session_state.records = [
        {
            "date": d,
            "count": random.randint(2, 5),
            "mood": random.randint(4, 9)
        }
        for d in demo_dates
    ]

# =========================
# 습관 체크인
# =========================
st.subheader("✅ 오늘의 습관 체크인")

col1, col2 = st.columns(2)

with col1:
    wake = st.checkbox("🌅 기상 미션")
    water = st.checkbox("💧 물 마시기")
    study = st.checkbox("📘 공부/독서")

with col2:
    exercise = st.checkbox("🏃 운동하기")
    sleep = st.checkbox("😴 수면")

habits = [wake, water, study, exercise, sleep]
habit_names = ["기상 미션", "물 마시기", "공부/독서", "운동하기", "수면"]

mood = st.slider("😊 오늘의 기분", 1, 10, 6)

city = st.selectbox(
    "🌍 도시 선택",
    ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon",
     "Gwangju", "Suwon", "Ulsan", "Jeju", "Changwon"]
)

coach_style = st.radio(
    "🎮 코치 스타일",
    ["스파르타 코치", "따뜻한 멘토", "게임 마스터"],
    horizontal=True
)

# =========================
# 달성률
# =========================
checked_count = sum(habits)
achievement_rate = int((checked_count / 5) * 100)

c1, c2, c3 = st.columns(3)
c1.metric("📈 달성률", f"{achievement_rate}%")
c2.metric("✅ 달성 습관", f"{checked_count} / 5")
c3.metric("😊 기분", mood)

# =========================
# 오늘 기록 저장
# =========================
if not any(r["date"] == date.today() for r in st.session_state.records):
    st.session_state.records.append({
        "date": date.today(),
        "count": checked_count,
        "mood": mood
    })

# =========================
# 7일 차트
# =========================
st.subheader("📊 최근 7일 습관 달성")

df = pd.DataFrame(st.session_state.records)
df["date"] = pd.to_datetime(df["date"])

chart = alt.Chart(df).mark_bar().encode(
    x="date:T",
    y="count:Q",
    tooltip=["date:T", "count", "mood"]
).properties(height=300)

st.altair_chart(chart, use_container_width=True)

# =========================
# API 함수
# =========================
def get_weather(city, api_key):
    if not api_key:
        return None
    try:
        res = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city,
                "appid": api_key,
                "units": "metric",
                "lang": "kr"
            },
            timeout=10
        )
        if res.status_code != 200:
            return None
        data = res.json()
        return f"{data['weather'][0]['description']} / {data['main']['temp']}°C"
    except:
        return None


def get_dog_image():
    try:
        res = requests.get("https://dog.ceo/api/breeds/image/random", timeout=10)
        if res.status_code != 200:
            return None
        data = res.json()
        url = data["message"]
        breed = url.split("/breeds/")[1].split("/")[0]
        return url, breed
    except:
        return None


def generate_report(habits, mood, weather, breed, style, api_key):
    if not api_key:
        return "❌ OpenAI API Key를 입력해주세요."

    system_prompt = {
        "스파르타 코치": "너는 엄격하고 직설적인 코치다.",
        "따뜻한 멘토": "너는 공감과 응원을 잘하는 따뜻한 멘토다.",
        "게임 마스터": "너는 RPG 게임의 마스터다."
    }[style]

    completed = [n for n, h in zip(habit_names, habits) if h]

    user_prompt = f"""
오늘의 습관: {completed}
기분: {mood}/10
날씨: {weather}
강아지 품종: {breed}

아래 형식으로 작성:
- 컨디션 등급(S~D)
- 습관 분석
- 날씨 코멘트
- 내일 미션
- 오늘의 한마디
"""

    client = OpenAI(api_key=api_key)
    res = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return res.choices[0].message.content

# =========================
# 리포트 생성
# =========================
st.markdown("---")
if st.button("🧠 컨디션 리포트 생성"):
    weather = get_weather(city, weather_api_key) or "날씨 정보 없음"
    dog = get_dog_image()

    col_w, col_d = st.columns(2)

    with col_w:
        st.subheader("🌤 오늘의 날씨")
        st.write(weather)

    with col_d:
        st.subheader("🐶 오늘의 강아지")
        if dog:
            st.image(dog[0], use_container_width=True)
            st.caption(f"품종: {dog[1]}")
        else:
            st.write("불러오기 실패")

    report = generate_report(
        habits,
        mood,
        weather,
        dog[1] if dog else "알 수 없음",
        coach_style,
        openai_api_key
    )

    st.subheader("📋 AI 코치 리포트")
    st.write(report)

    st.subheader("📎 공유용 텍스트")
    st.code(report, language="markdown")

# =========================
# 안내
# =========================
with st.expander("ℹ️ API 안내"):
    st.write(
        "OpenAI: AI 리포트 생성\n"
        "OpenWeatherMap: 날씨 정보\n"
        "Dog CEO API: 강아지 이미지"
    )
