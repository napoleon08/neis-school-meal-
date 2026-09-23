import datetime
import re

import pandas as pd
import requests
import streamlit as st


# =========================================================
# PAGE
# =========================================================

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
        background:
            linear-gradient(
                180deg,
                #F8FAFC,
                #F1F5F9
            );
        color: #0F172A;
    }

    .main .block-container {
        max-width: 1200px;
        padding-top: 2.5rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        color: #0F172A !important;
    }

    .hero {
        background:
            linear-gradient(
                135deg,
                #FFFFFF,
                #EFF6FF
            );

        border: 1px solid #DBEAFE;

        border-radius: 24px;

        padding: 32px 36px;

        margin-bottom: 28px;

        box-shadow:
            0 10px 30px
            rgba(15, 23, 42, 0.06);
    }

    .badge {
        display: inline-block;

        padding: 7px 12px;

        border-radius: 999px;

        background: #DBEAFE;

        color: #1D4ED8 !important;

        font-size: 13px;

        font-weight: 700;

        margin-bottom: 12px;
    }

    .title {
        font-size: 36px;

        font-weight: 800;

        color: #0F172A !important;
    }

    .subtitle {
        color: #64748B !important;

        margin-top: 8px;

        font-size: 16px;
    }

    .menu-card {
        background: #FFFFFF;

        border: 1px solid #E2E8F0;

        border-radius: 16px;

        padding: 18px 20px;

        margin-bottom: 10px;

        box-shadow:
            0 5px 15px
            rgba(15, 23, 42, 0.04);
    }

    .menu-number {
        display: inline-flex;

        align-items: center;
        justify-content: center;

        width: 32px;
        height: 32px;

        background: #EFF6FF;

        color: #2563EB !important;

        border-radius: 9px;

        font-weight: 800;

        margin-right: 12px;
    }

    .menu-name {
        color: #1E293B !important;

        font-size: 17px;

        font-weight: 650;
    }

    .info {
        background: #FFFFFF;

        border: 1px solid #E2E8F0;

        border-radius: 18px;

        padding: 20px;

        margin-top: 20px;
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

        <div class="badge">
            DAILY MEAL
        </div>

        <div class="title">
            📅 달력별 급식
        </div>

        <div class="subtitle">
            {SCHOOL_NAME}의 날짜별 급식 메뉴를
            한눈에 확인할 수 있습니다.
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


# =========================================================
# GET DATA
# =========================================================

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

        display_text = menu_text.replace(
            "<br/>",
            "\n",
        )

    else:

        display_text = re.sub(
            r"\([^)]*\)",
            "",
            menu_text,
        ).replace(
            "<br/>",
            "\n",
        )


    menu_items = [
        item.strip()
        for item in display_text.split(
            "\n"
        )
        if item.strip()
    ]


    # =====================================================
    # STATS
    # =====================================================

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


    # =====================================================
    # MENU
    # =====================================================

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

                <span class="menu-number">
                    {i}
                </span>

                <span class="menu-name">
                    {menu}
                </span>

            </div>
            """,
            unsafe_allow_html=True,
        )


    # =====================================================
    # EXTRA INFORMATION
    # =====================================================

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
