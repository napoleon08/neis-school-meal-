import datetime
import re

import pandas as pd
import requests
import streamlit as st


st.set_page_config(
    page_title="달력별 급식",
    page_icon="📅",
    layout="wide",
)


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

    .stApp {
        background: #F1E8D5;
    }

    .main .block-container {
        max-width: 1200px;
        padding-top: 42px;
        padding-bottom: 60px;
    }

    .main h1,
    .main h2,
    .main h3,
    .main p,
    .main label {
        color: #17202A !important;
    }

    .hero {
        background: #102A43;
        border-radius: 26px;
        padding: 40px 44px;
        margin-bottom: 30px;
        box-shadow:
            0 14px 35px rgba(7, 26, 43, 0.18);
    }

    .hero-small {
        color: #C8D8E3 !important;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.12em;
    }

    .hero-title {
        color: #FFFDF7 !important;
        font-size: 40px;
        font-weight: 850;
        margin-top: 12px;
    }

    .hero-text {
        color: #E4ECEF !important;
        font-size: 16px;
        margin-top: 10px;
    }

    .menu-card {
        background: #FFFDF7;
        border: 1px solid #D8CEBA;
        border-radius: 15px;
        padding: 16px 19px;
        margin-bottom: 9px;
        box-shadow:
            0 4px 13px rgba(7, 26, 43, 0.055);
    }

    .number {
        display: inline-flex;
        align-items: center;
        justify-content: center;

        width: 34px;
        height: 34px;

        background: #164A41;
        color: #F8F4EA !important;

        border-radius: 10px;

        font-weight: 800;

        margin-right: 13px;
    }

    .menu-name {
        color: #17202A !important;
        font-size: 17px;
        font-weight: 700;
    }

    .info {
        background: #FFFDF7;
        border: 1px solid #D8CEBA;
        border-left: 5px solid #B58A4A;
        border-radius: 14px;
        padding: 18px;
        color: #17202A !important;
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

    except Exception as e:

        st.error(
            f"API 요청 오류: {e}"
        )

        return pd.DataFrame()

    try:

        rows = data[
            "mealServiceDietInfo"
        ][1]["row"]

    except (
        KeyError,
        IndexError,
        TypeError,
    ):

        return pd.DataFrame()

    return pd.DataFrame(rows)


# =========================================================
# HERO
# =========================================================

st.markdown(
    f"""
    <div class="hero">

        <div class="hero-small">
            DAILY MEAL
        </div>

        <div class="hero-title">
            📅 달력별 급식
        </div>

        <div class="hero-text">
            {SCHOOL_NAME}의 날짜별 급식 메뉴를
            확인할 수 있습니다.
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# DATE
# =========================================================

today = (
    datetime.datetime.utcnow()
    + datetime.timedelta(hours=9)
).date()


selected_date = st.date_input(
    "📅 급식 날짜",
    value=today,
)


show_allergy = st.toggle(
    "알레르기 번호 표시",
    value=True,
)


ymd = selected_date.strftime(
    "%Y%m%d"
)


meal_df = get_meal(
    ymd
)


if meal_df.empty:

    st.markdown(
        """
        <div class="info">
            📭 선택한 날짜에는 급식 데이터가 없습니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

else:

    row = meal_df.iloc[0]

    menu_text = row.get(
        "DDISH_NM",
        "",
    )


    if show_allergy:

        display_text = menu_text

    else:

        display_text = re.sub(
            r"\([^)]*\)",
            "",
            menu_text,
        )


    display_text = display_text.replace(
        "<br/>",
        "\n",
    )


    menu_items = [
        x.strip()
        for x in display_text.split("\n")
        if x.strip()
    ]


    c1, c2, c3 = st.columns(3)


    with c1:
        st.metric(
            "메뉴 수",
            len(menu_items),
        )


    with c2:
        st.metric(
            "칼로리",
            row.get(
                "CAL_INFO",
                "-"
            ),
        )


    with c3:
        st.metric(
            "날짜",
            selected_date.strftime(
                "%Y.%m.%d"
            ),
        )


    st.markdown(
        "## 🍱 오늘의 메뉴"
    )


    for i, menu in enumerate(
        menu_items,
        start=1,
    ):

        st.markdown(
            f"""
            <div class="menu-card">

                <span class="number">
                    {i}
                </span>

                <span class="menu-name">
                    {menu}
                </span>

            </div>
            """,
            unsafe_allow_html=True,
        )


    nutrition = row.get(
        "NTR_INFO",
        "",
    )

    origin = row.get(
        "ORPLC_INFO",
        "",
    )


    with st.expander(
        "🥗 영양 정보"
    ):

        st.write(
            nutrition
            if nutrition
            else "영양 정보가 없습니다."
        )


    with st.expander(
        "🌾 원산지 정보"
    ):

        st.write(
            origin
            if origin
            else "원산지 정보가 없습니다."
        )


    with st.expander(
        "🔎 NEIS 원본 데이터"
    ):

        st.json(
            row.to_dict()
        )
