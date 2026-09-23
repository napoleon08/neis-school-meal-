import datetime
import re

import pandas as pd
import requests
import streamlit as st


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="달력별 급식",
    page_icon="🍱",
    layout="wide",
)


# =========================================================
# NEIS SETTINGS
# =========================================================

NEIS_URL = "https://open.neis.go.kr/hub"

OFFICE_CODE = "J10"
SCHOOL_CODE = "7530480"
SCHOOL_NAME = "송탄고등학교"


# =========================================================
# DESIGN
# =========================================================

st.markdown(
    """
    <style>

    /* =========================
       전체 배경
       ========================= */

    .stApp {
        background-color: #F7F4EC !important;
        color: #1F2933 !important;
    }

    .main {
        background-color: #F7F4EC !important;
    }

    .main .block-container {
        max-width: 1200px;
        padding-top: 40px;
        padding-bottom: 60px;
    }


    /* =========================
       기본 텍스트
       ========================= */

    .main p {
        color: #1F2933 !important;
    }

    .main h1,
    .main h2,
    .main h3,
    .main h4 {
        color: #102A43 !important;
    }


    /* =========================
       날짜 선택
       ========================= */

    div[data-baseweb="input"] {
        background-color: #FFFFFF !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="input"] input {
        background-color: #FFFFFF !important;
        color: #1F2933 !important;
    }


    /* =========================
       토글
       ========================= */

    [data-testid="stToggle"] label {
        color: #1F2933 !important;
    }


    /* =========================
       메트릭
       ========================= */

    [data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D9D4C8 !important;
        border-radius: 12px !important;
        padding: 18px !important;
    }

    [data-testid="stMetricLabel"] {
        color: #52606D !important;
    }

    [data-testid="stMetricValue"] {
        color: #102A43 !important;
    }


    /* =========================
       구분선
       ========================= */

    hr {
        border-color: #D9D4C8 !important;
    }


    /* =========================
       Expander
       ========================= */

    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D9D4C8 !important;
        border-radius: 10px !important;
    }

    [data-testid="stExpander"] summary {
        color: #102A43 !important;
    }


    /* =========================
       Sidebar
       ========================= */

    section[data-testid="stSidebar"] {
        background-color: #102A43 !important;
    }

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }


    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# API
# =========================================================

@st.cache_data(ttl=600)
def get_meal(ymd):

    params = {
        "Type": "json",
        "pIndex": 1,
        "pSize": 100,
        "ATPT_OFCDC_SC_CODE": OFFICE_CODE,
        "SD_SCHUL_CODE": SCHOOL_CODE,
        "MMEAL_SC_CODE": 2,
        "MLSV_FROM_YMD": ymd,
        "MLSV_TO_YMD": ymd,
    }

    try:

        response = requests.get(
            f"{NEIS_URL}/mealServiceDietInfo",
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

    except requests.exceptions.RequestException:

        st.error(
            "NEIS API에 연결할 수 없습니다."
        )

        return pd.DataFrame()

    except ValueError:

        st.error(
            "NEIS API의 응답을 읽을 수 없습니다."
        )

        return pd.DataFrame()


    try:

        rows = data[
            "mealServiceDietInfo"
        ][1]["row"]

        return pd.DataFrame(rows)

    except (
        KeyError,
        IndexError,
        TypeError,
    ):

        return pd.DataFrame()


# =========================================================
# MENU CLEANING
# =========================================================

def clean_menu(text):

    if not isinstance(text, str):
        return ""

    # 알레르기 번호 제거
    text = re.sub(
        r"\([^)]*\)",
        "",
        text,
    )

    # HTML 줄바꿈을 실제 줄바꿈으로 변경
    text = text.replace(
        "<br/>",
        "\n",
    )

    text = text.replace(
        "<br>",
        "\n",
    )

    return text.strip()


# =========================================================
# CALORIE
# =========================================================

def get_kcal(value):

    if not isinstance(value, str):
        return None

    match = re.search(
        r"[\d.]+",
        value,
    )

    if match:
        return float(match.group())

    return None


# =========================================================
# TODAY IN KOREA
# =========================================================

today_korea = (
    datetime.datetime.utcnow()
    + datetime.timedelta(hours=9)
).date()


# =========================================================
# HEADER
# =========================================================

st.title(
    "🍱 달력별 급식"
)

st.write(
    f"{SCHOOL_NAME}의 날짜별 학교 급식 정보를 확인할 수 있습니다."
)


# =========================================================
# DATE
# =========================================================

selected_date = st.date_input(
    "📅 급식 날짜",
    value=today_korea,
)


# =========================================================
# ALLERGY OPTION
# =========================================================

show_allergy = st.toggle(
    "알레르기 번호 표시",
    value=False,
)


# =========================================================
# API REQUEST
# =========================================================

ymd = selected_date.strftime(
    "%Y%m%d"
)

meal_df = get_meal(
    ymd
)


# =========================================================
# NO DATA
# =========================================================

if meal_df.empty:

    st.info(
        "📭 선택한 날짜에는 급식이 없는 날입니다."
    )

    st.stop()


# =========================================================
# FIRST MEAL ROW
# =========================================================

meal = meal_df.iloc[0]


raw_menu = meal.get(
    "DDISH_NM",
    "",
)


raw_menu = str(
    raw_menu
)


# =========================================================
# MENU SPLIT
# =========================================================

menu_lines = raw_menu.split(
    "<br/>"
)

menu_lines = [
    item.strip()
    for item in menu_lines
    if item.strip()
]


# =========================================================
# CLEAN MENU
# =========================================================

cleaned_menu_lines = []

for item in menu_lines:

    if show_allergy:

        cleaned = item

    else:

        cleaned = re.sub(
            r"\([^)]*\)",
            "",
            item,
        )

    cleaned = cleaned.strip()

    if cleaned:
        cleaned_menu_lines.append(
            cleaned
        )


# =========================================================
# CALORIE
# =========================================================

kcal = get_kcal(
    meal.get(
        "CAL_INFO",
        "",
    )
)


# =========================================================
# INFORMATION CARDS
# =========================================================

col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "메뉴 수",
        len(cleaned_menu_lines),
    )


with col2:

    if kcal is not None:

        st.metric(
            "칼로리",
            f"{kcal:,.1f} kcal",
        )

    else:

        st.metric(
            "칼로리",
            "-",
        )


with col3:

    st.metric(
        "날짜",
        selected_date.strftime(
            "%Y.%m.%d"
        ),
    )


# =========================================================
# MENU
# =========================================================

st.divider()

st.header(
    "🍱 오늘의 메뉴"
)


# =========================================================
# MENU CARDS
# =========================================================

for number, menu in enumerate(
    cleaned_menu_lines,
    start=1,
):

    with st.container(
        border=True
    ):

        col_number, col_menu = st.columns(
            [0.08, 0.92]
        )


        with col_number:

            st.markdown(
                f"### {number}"
            )


        with col_menu:

            st.markdown(
                f"**{menu}**"
            )


# =========================================================
# ORIGINAL NEIS DATA
# =========================================================

st.divider()

with st.expander(
    "🔎 NEIS 원본 데이터 보기"
):

    st.write(
        "NEIS API에서 받은 원본 급식 데이터입니다."
    )

    st.json(
        meal.to_dict()
    )


# =========================================================
# INFORMATION
# =========================================================

st.divider()

st.subheader(
    "📌 급식 정보"
)

info_col1, info_col2 = st.columns(2)


with info_col1:

    st.write(
        f"**학교:** {SCHOOL_NAME}"
    )

    st.write(
        f"**급식 날짜:** "
        f"{selected_date.strftime('%Y-%m-%d')}"
    )


with info_col2:

    st.write(
        f"**메뉴 수:** "
        f"{len(cleaned_menu_lines)}개"
    )

    if kcal is not None:

        st.write(
            f"**총 열량:** "
            f"{kcal:,.1f} kcal"
        )

    else:

        st.write(
            "**총 열량:** 정보 없음"
        )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "교육부 NEIS 교육정보 개방 포털을 이용한 "
    "학교 급식 데이터 서비스"
)
