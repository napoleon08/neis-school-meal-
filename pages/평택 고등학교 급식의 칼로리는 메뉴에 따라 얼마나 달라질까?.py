import datetime
import re

import pandas as pd
import requests
import streamlit as st


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="평택 고등학교 급식의 칼로리는 메뉴에 따라 얼마나 달라질까?",
    page_icon="🍱",
    layout="wide",
)


# =========================================================
# NEIS API SETTINGS
# =========================================================

NEIS_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"

OFFICE_CODE = "J10"
SCHOOL_CODE = "7530480"
SCHOOL_NAME = "송탄고등학교"


# =========================================================
# DESIGN
# =========================================================

st.markdown(
    """
    <style>

    /* =========================================
       전체 배경
       ========================================= */

    .stApp {
        background-color: #F7F4EC !important;
        color: #1F2933 !important;
    }

    .main {
        background-color: #F7F4EC !important;
    }

    .main .block-container {
        max-width: 1200px;
        padding-top: 35px;
        padding-bottom: 60px;
    }


    /* =========================================
       기본 텍스트
       ========================================= */

    .main p {
        color: #1F2933 !important;
    }

    .main h1,
    .main h2,
    .main h3,
    .main h4 {
        color: #102A43 !important;
    }


    /* =========================================
       날짜 입력
       ========================================= */

    div[data-baseweb="input"] {
        background-color: #FFFFFF !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="input"] input {
        background-color: #FFFFFF !important;
        color: #1F2933 !important;
    }


    /* =========================================
       토글
       ========================================= */

    [data-testid="stToggle"] label {
        color: #1F2933 !important;
    }


    /* =========================================
       메트릭 카드
       ========================================= */

    [data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D9D4C8 !important;
        border-radius: 14px !important;
        padding: 20px !important;
    }

    [data-testid="stMetricLabel"] {
        color: #52606D !important;
        font-size: 15px !important;
    }

    [data-testid="stMetricValue"] {
        color: #102A43 !important;
        font-size: 30px !important;
        font-weight: 700 !important;
    }


    /* =========================================
       구분선
       ========================================= */

    hr {
        border-color: #D9D4C8 !important;
    }


    /* =========================================
       Sidebar
       ========================================= */

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
# GET MEAL DATA
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
            NEIS_URL,
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
            "NEIS API 응답을 읽을 수 없습니다."
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

def remove_allergy_numbers(menu):

    """
    메뉴 뒤의 알레르기 번호를 제거한다.

    예:
    치킨마요덮밥(1.5.6.15)
    →
    치킨마요덮밥
    """

    return re.sub(
        r"\s*\([^)]*\)",
        "",
        menu,
    ).strip()


# =========================================================
# CALORIE PARSING
# =========================================================

def parse_kcal(value):

    if not isinstance(value, str):
        return None

    match = re.search(
        r"[\d.]+",
        value,
    )

    if match:

        return float(
            match.group()
        )

    return None


# =========================================================
# KOREA DATE
# =========================================================

today_korea = (
    datetime.datetime.utcnow()
    + datetime.timedelta(hours=9)
).date()


# =========================================================
# PAGE TITLE
# =========================================================

st.title(
    "🍱 평택 고등학교 급식의 칼로리는 메뉴에 따라 얼마나 달라질까?"
)

st.write(
    "송탄고등학교의 중식 데이터를 날짜별로 확인하고 "
    "메뉴 구성과 칼로리를 비교합니다."
)


# =========================================================
# DATE + ALLERGY SWITCH
# =========================================================

date_col, allergy_col = st.columns(
    [1, 1]
)


with date_col:

    selected_date = st.date_input(
        "📅 급식 날짜",
        value=today_korea,
    )


with allergy_col:

    st.write("알레르기 정보")

    show_allergy = st.toggle(
        "알레르기 정보 보기",
        value=True,
    )


# =========================================================
# GET DATA
# =========================================================

ymd = selected_date.strftime(
    "%Y%m%d"
)

meal_df = get_meal(
    ymd
)


# =========================================================
# NO MEAL
# =========================================================

if meal_df.empty:

    st.info(
        "📭 급식이 없는 날입니다."
    )

    st.stop()


# =========================================================
# MEAL DATA
# =========================================================

meal = meal_df.iloc[0]


raw_menu = str(
    meal.get(
        "DDISH_NM",
        "",
    )
)


# =========================================================
# SPLIT MENU
# =========================================================

menu_list = raw_menu.split(
    "<br/>"
)


menu_list = [
    menu.strip()
    for menu in menu_list
    if menu.strip()
]


# =========================================================
# ALLERGY PROCESSING
# =========================================================

display_menu = []


for menu in menu_list:

    if show_allergy:

        display_menu.append(
            menu
        )

    else:

        display_menu.append(
            remove_allergy_numbers(
                menu
            )
        )


# =========================================================
# CALORIE
# =========================================================

kcal = parse_kcal(
    meal.get(
        "CAL_INFO",
        "",
    )
)


# =========================================================
# SCHOOL INFORMATION
# =========================================================

st.caption(
    f"🏫 {SCHOOL_NAME} · 중식 · "
    f"{selected_date.strftime('%Y년 %m월 %d일')}"
)


# =========================================================
# BIG NUMBER CARDS
# =========================================================

st.divider()

metric_col1, metric_col2 = st.columns(
    2
)


with metric_col1:

    st.metric(
        "🍽️ 메뉴 가짓수",
        f"{len(display_menu)}개",
    )


with metric_col2:

    if kcal is not None:

        st.metric(
            "🔥 총 칼로리",
            f"{kcal:,.1f} kcal",
        )

    else:

        st.metric(
            "🔥 총 칼로리",
            "정보 없음",
        )


# =========================================================
# MENU
# =========================================================

st.divider()

st.header(
    "🍚 오늘의 중식 메뉴"
)


if display_menu:

    # 메뉴를 3개씩 한 줄에 배치
    columns_per_row = 3

    for start in range(
        0,
        len(display_menu),
        columns_per_row,
    ):

        row = display_menu[
            start:start + columns_per_row
        ]

        cols = st.columns(
            columns_per_row
        )

        for index, menu in enumerate(
            row
        ):

            menu_number = (
                start + index + 1
            )

            with cols[index]:

                st.markdown(
                    f"""
                    <div style="
                        background-color: #FFFFFF;
                        border: 1px solid #D9D4C8;
                        border-radius: 14px;
                        padding: 20px;
                        margin-bottom: 16px;
                        min-height: 95px;
                        box-shadow: 0 2px 8px rgba(16,42,67,0.04);
                    ">

                        <div style="
                            color: #164A41;
                            font-size: 14px;
                            font-weight: 700;
                            margin-bottom: 8px;
                        ">
                            MENU {menu_number}
                        </div>

                        <div style="
                            color: #1F2933;
                            font-size: 17px;
                            font-weight: 600;
                            line-height: 1.5;
                        ">
                            {menu}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# =========================================================
# CALORIE INFORMATION
# =========================================================

st.divider()

st.subheader(
    "🔥 칼로리 정보"
)


if kcal is not None:

    st.write(
        f"선택한 날짜의 송탄고등학교 중식은 "
        f"**{kcal:,.1f} kcal**입니다."
    )

else:

    st.write(
        "해당 날짜의 칼로리 정보가 없습니다."
    )


# =========================================================
# ORIGINAL DATA
# =========================================================

with st.expander(
    "🔎 NEIS 원본 데이터 보기"
):

    st.json(
        meal.to_dict()
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "교육부 NEIS 교육정보 개방 포털 "
    "mealServiceDietInfo API · 송탄고등학교 중식"
)
