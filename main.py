import datetime
import re

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="우리학교 급식 데이터",
    page_icon="🍚",
    layout="wide",
    initial_sidebar_state="expanded",
)


NEIS_URL = "https://open.neis.go.kr/hub"
DEFAULT_SCHOOL = "송탄고등학교"


# =========================================================
# DESIGN
# =========================================================

st.markdown(
    """
    <style>

    /* =====================================================
       BASIC
    ===================================================== */

    html,
    body,
    [class*="css"] {
        font-family:
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;
    }

    .stApp {
        background: #F1E8D5;
    }

    .main {
        background: #F1E8D5;
    }

    .main .block-container {
        max-width: 1250px;
        padding-top: 42px;
        padding-bottom: 60px;
    }


    /* =====================================================
       MAIN TEXT
       Светлый фон → ТОЛЬКО тёмный текст
    ===================================================== */

    .main h1,
    .main h2,
    .main h3,
    .main h4,
    .main p,
    .main label {
        color: #17202A !important;
    }


    /* =====================================================
       SIDEBAR
       Тёмный фон → ТОЛЬКО светлый текст
    ===================================================== */

    section[data-testid="stSidebar"] {
        background: #071A2B !important;
        border-right: 1px solid #163B55;
    }

    section[data-testid="stSidebar"] > div {
        background: #071A2B !important;
    }

    section[data-testid="stSidebar"] * {
        color: #F8F4EA !important;
    }

    section[data-testid="stSidebar"] input {
        background: #102A43 !important;
        color: #FFFDF7 !important;
        border: 1px solid #35566F !important;
    }

    section[data-testid="stSidebar"] input::placeholder {
        color: #C9D5DE !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background: #102A43 !important;
        color: #FFFDF7 !important;
        border: 1px solid #35566F !important;
    }


    /* =====================================================
       SIDEBAR HEADER
    ===================================================== */

    .sidebar-brand {
        padding: 8px 4px 28px 4px;
    }

    .sidebar-brand-title {
        color: #FFFDF7 !important;
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.04em;
    }

    .sidebar-brand-subtitle {
        color: #C9D5DE !important;
        font-size: 12px;
        margin-top: 5px;
    }

    .sidebar-section {
        color: #D7E5DF !important;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-top: 24px;
        margin-bottom: 9px;
    }


    /* =====================================================
       HERO
    ===================================================== */

    .hero {
        background: #102A43;

        border: 1px solid #183B57;

        border-radius: 26px;

        padding: 40px 44px;

        box-shadow:
            0 14px 35px rgba(7, 26, 43, 0.18);

        margin-bottom: 30px;
    }

    .hero-small {
        color: #C8D8E3 !important;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.12em;
        margin-bottom: 13px;
    }

    .hero-title {
        color: #FFFDF7 !important;
        font-size: 40px;
        font-weight: 850;
        line-height: 1.15;
        letter-spacing: -0.045em;
    }

    .hero-description {
        color: #E4ECEF !important;
        font-size: 16px;
        line-height: 1.75;
        margin-top: 13px;
        max-width: 780px;
    }

    .hero-school {
        color: #E7C98B !important;
        font-weight: 800;
    }


    /* =====================================================
       SECTION TITLE
    ===================================================== */

    .section {
        display: flex;
        align-items: center;
        gap: 12px;

        margin-top: 32px;
        margin-bottom: 16px;
    }

    .section-line {
        width: 5px;
        height: 30px;

        background: #164A41;

        border-radius: 10px;
    }

    .section-title {
        color: #102A43 !important;
        font-size: 25px;
        font-weight: 850;
        letter-spacing: -0.035em;
    }


    /* =====================================================
       STAT CARDS
       Светлые карточки → тёмный текст
    ===================================================== */

    .stat-card {
        background: #FFFDF7;

        border: 1px solid #D8CEBA;

        border-radius: 19px;

        padding: 23px 25px;

        min-height: 132px;

        box-shadow:
            0 7px 20px rgba(7, 26, 43, 0.07);
    }

    .stat-card-green {
        border-top: 5px solid #164A41;
    }

    .stat-card-blue {
        border-top: 5px solid #102A43;
    }

    .stat-card-beige {
        border-top: 5px solid #B58A4A;
    }

    .stat-label {
        color: #65727D !important;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.09em;
        text-transform: uppercase;
    }

    .stat-value {
        color: #102A43 !important;
        font-size: 28px;
        font-weight: 850;
        margin-top: 8px;
    }

    .stat-description {
        color: #71808A !important;
        font-size: 12px;
        margin-top: 6px;
    }


    /* =====================================================
       MENU CARDS
    ===================================================== */

    .menu-card {
        display: flex;
        align-items: center;

        background: #FFFDF7;

        border: 1px solid #D8CEBA;

        border-radius: 15px;

        padding: 15px 18px;

        margin-bottom: 9px;

        box-shadow:
            0 4px 13px rgba(7, 26, 43, 0.055);
    }

    .menu-number {
        display: flex;
        align-items: center;
        justify-content: center;

        width: 35px;
        height: 35px;

        background: #164A41;

        color: #F8F4EA !important;

        border-radius: 10px;

        font-size: 14px;
        font-weight: 800;

        margin-right: 14px;

        flex-shrink: 0;
    }

    .menu-name {
        color: #17202A !important;
        font-size: 17px;
        font-weight: 700;
    }


    /* =====================================================
       DARK INFORMATION CARD
       Тёмный фон → светлый текст
    ===================================================== */

    .dark-card {
        background: #164A41;

        border: 1px solid #245D52;

        border-radius: 20px;

        padding: 25px;

        margin-top: 22px;
    }

    .dark-card-title {
        color: #FFFDF7 !important;
        font-size: 18px;
        font-weight: 800;
    }

    .dark-card-text {
        color: #E7F0EC !important;
        font-size: 14px;
        line-height: 1.7;
        margin-top: 7px;
    }


    /* =====================================================
       INFO BOX
    ===================================================== */

    .info-box {
        background: #FFFDF7;

        border-left: 5px solid #B58A4A;

        border-top: 1px solid #D8CEBA;
        border-right: 1px solid #D8CEBA;
        border-bottom: 1px solid #D8CEBA;

        border-radius: 14px;

        padding: 18px 20px;

        color: #17202A !important;

        line-height: 1.7;
    }


    /* =====================================================
       INPUTS IN MAIN
    ===================================================== */

    div[data-baseweb="input"] {
        background: #FFFDF7 !important;
        border-radius: 12px !important;
    }

    div[data-baseweb="input"] input {
        color: #17202A !important;
        background: #FFFDF7 !important;
    }

    div[data-baseweb="select"] > div {
        background: #FFFDF7 !important;
        color: #17202A !important;
        border: 1px solid #CFC3AC !important;
        border-radius: 12px !important;
    }


    /* =====================================================
       DIVIDER
    ===================================================== */

    hr {
        border-color: #D4C8B1 !important;
        margin-top: 35px;
        margin-bottom: 35px;
    }


    /* =====================================================
       EXPANDER
    ===================================================== */

    details {
        background: #FFFDF7 !important;
        border: 1px solid #D8CEBA !important;
        border-radius: 14px !important;
    }

    details summary {
        color: #102A43 !important;
        font-weight: 750 !important;
    }


    /* =====================================================
       TABLE
    ===================================================== */

    [data-testid="stDataFrame"] {
        border: 1px solid #D8CEBA;
        border-radius: 14px;
        overflow: hidden;
    }


    /* =====================================================
       FOOTER
    ===================================================== */

    .footer {
        text-align: center;

        margin-top: 50px;

        padding-top: 25px;

        border-top: 1px solid #D4C8B1;

        color: #697780 !important;

        font-size: 12px;

        line-height: 1.7;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# API
# =========================================================

def api_get(endpoint, params):

    try:

        response = requests.get(
            f"{NEIS_URL}/{endpoint}",
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:

        st.error(
            f"API 요청 중 오류가 발생했습니다: {e}"
        )

        return None

    except ValueError:

        st.error(
            "API 응답을 읽을 수 없습니다."
        )

        return None


# =========================================================
# SCHOOL SEARCH
# =========================================================

@st.cache_data(ttl=3600)
def search_schools(query):

    if not query:
        return pd.DataFrame()

    params = {
        "Type": "json",
        "pIndex": 1,
        "pSize": 100,
        "SCHUL_NM": query,
    }

    data = api_get(
        "schoolInfo",
        params,
    )

    if not data:
        return pd.DataFrame()

    try:

        rows = data[
            "schoolInfo"
        ][1]["row"]

    except (
        KeyError,
        IndexError,
        TypeError,
    ):

        return pd.DataFrame()

    return pd.DataFrame(rows)


def school_search_with_fallback(query):

    df = search_schools(query)

    if not df.empty:
        return df

    replacements = [
        ("여고", "여자고등학교"),
        ("여중", "여자중학교"),
        ("여초", "여자초등학교"),
        ("고", "고등학교"),
        ("중", "중학교"),
        ("초", "초등학교"),
    ]

    for short, full in replacements:

        if query.endswith(short):

            new_query = (
                query[:-len(short)]
                + full
            )

            df = search_schools(
                new_query
            )

            if not df.empty:
                return df

    return pd.DataFrame()


def school_label(row):

    return (
        f"{row.get('SCHUL_NM', '')}"
        f" | "
        f"{row.get('ATPT_OFCDC_SC_NM', '')}"
        f" | "
        f"{row.get('SCHUL_KND_SC_NM', '')}"
    )


# =========================================================
# MEAL
# =========================================================

@st.cache_data(ttl=600)
def get_meal(
    school_code,
    office_code,
    ymd,
):

    params = {
        "Type": "json",
        "pIndex": 1,
        "pSize": 100,
        "ATPT_OFCDC_SC_CODE": office_code,
        "SD_SCHUL_CODE": school_code,
        "MMEAL_SC_CODE": 2,
        "MLSV_FROM_YMD": ymd,
        "MLSV_TO_YMD": ymd,
    }

    data = api_get(
        "mealServiceDietInfo",
        params,
    )

    if not data:
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
# CLEAN MENU
# =========================================================

def clean_menu(text):

    if not isinstance(
        text,
        str,
    ):
        return ""

    text = re.sub(
        r"\([^)]*\)",
        "",
        text,
    )

    text = text.replace(
        "<br/>",
        "\n",
    )

    return text.strip()


def parse_kcal(value):

    if not isinstance(
        value,
        str,
    ):
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
# DATE
# =========================================================

today_korea = (
    datetime.datetime.utcnow()
    + datetime.timedelta(hours=9)
).date()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown(
    """
    <div class="sidebar-brand">

        <div class="sidebar-brand-title">
            🍚 급식 데이터
        </div>

        <div class="sidebar-brand-subtitle">
            NEIS SCHOOL MEAL
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


st.sidebar.markdown(
    '<div class="sidebar-section">학교 선택</div>',
    unsafe_allow_html=True,
)


school_query = st.sidebar.text_input(
    "학교 이름",
    value=DEFAULT_SCHOOL,
)


school_df = school_search_with_fallback(
    school_query
)


if school_df.empty:

    st.warning(
        "검색된 학교가 없습니다."
    )

    st.stop()


school_options = [
    school_label(row)
    for _, row
    in school_df.iterrows()
]


selected_school_label = (
    st.sidebar.selectbox(
        "학교 선택",
        school_options,
    )
)


selected_index = (
    school_options.index(
        selected_school_label
    )
)


selected_school = school_df.iloc[
    selected_index
]


school_name = selected_school[
    "SCHUL_NM"
]

office_code = selected_school[
    "ATPT_OFCDC_SC_CODE"
]

school_code = selected_school[
    "SD_SCHUL_CODE"
]


st.sidebar.markdown(
    '<div class="sidebar-section">날짜</div>',
    unsafe_allow_html=True,
)


selected_date = st.sidebar.date_input(
    "급식 날짜",
    value=today_korea,
)


ymd = selected_date.strftime(
    "%Y%m%d"
)


# =========================================================
# HERO
# =========================================================

st.markdown(
    f"""
    <div class="hero">

        <div class="hero-small">
            NEIS · SCHOOL MEAL DATA
        </div>

        <div class="hero-title">
            🍚 우리학교 급식 데이터
        </div>

        <div class="hero-description">
            나이스 교육정보 API를 이용하여
            <span class="hero-school">
                {school_name}
            </span>
            의 급식 정보를 확인하고
            데이터를 분석할 수 있습니다.
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SECTION
# =========================================================

st.markdown(
    """
    <div class="section">

        <div class="section-line"></div>

        <div class="section-title">
            오늘의 급식
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# MEAL
# =========================================================

meal_df = get_meal(
    school_code,
    office_code,
    ymd,
)


if meal_df.empty:

    st.markdown(
        """
        <div class="info-box">
            📭 선택한 날짜에는 급식 데이터가 없습니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

else:

    row = meal_df.iloc[0]

    menu_text = clean_menu(
        row.get(
            "DDISH_NM",
            "",
        )
    )

    kcal = parse_kcal(
        row.get(
            "CAL_INFO",
            "",
        )
    )

    menu_items = [
        item.strip()
        for item in menu_text.split("\n")
        if item.strip()
    ]


    # =====================================================
    # STATS
    # =====================================================

    c1, c2, c3 = st.columns(3)


    with c1:

        st.markdown(
            f"""
            <div class="stat-card stat-card-green">

                <div class="stat-label">
                    MENU
                </div>

                <div class="stat-value">
                    {len(menu_items)}
                </div>

                <div class="stat-description">
                    오늘 제공되는 메뉴
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    with c2:

        kcal_text = (
            f"{kcal:,.0f} kcal"
            if kcal is not None
            else "-"
        )

        st.markdown(
            f"""
            <div class="stat-card stat-card-blue">

                <div class="stat-label">
                    ENERGY
                </div>

                <div class="stat-value">
                    {kcal_text}
                </div>

                <div class="stat-description">
                    급식 열량
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    with c3:

        st.markdown(
            f"""
            <div class="stat-card stat-card-beige">

                <div class="stat-label">
                    DATE
                </div>

                <div class="stat-value">
                    {selected_date.strftime('%Y.%m.%d')}
                </div>

                <div class="stat-description">
                    선택한 급식 날짜
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    # =====================================================
    # MENU
    # =====================================================

    st.markdown(
        """
        <div class="section">

            <div class="section-line"></div>

            <div class="section-title">
                🍱 오늘의 메뉴
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    for i, menu in enumerate(
        menu_items,
        start=1,
    ):

        st.markdown(
            f"""
            <div class="menu-card">

                <div class="menu-number">
                    {i}
                </div>

                <div class="menu-name">
                    {menu}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    # =====================================================
    # GREEN INFORMATION CARD
    # =====================================================

    st.markdown(
        f"""
        <div class="dark-card">

            <div class="dark-card-title">
                🌿 오늘의 급식 한눈에 보기
            </div>

            <div class="dark-card-text">
                {school_name}
                · {selected_date.strftime('%Y년 %m월 %d일')}
                · 메뉴 {len(menu_items)}개
                · {kcal:,.0f} kcal
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    # =====================================================
    # RAW DATA
    # =====================================================

    with st.expander(
        "🔎 NEIS 원본 데이터"
    ):

        st.json(
            row.to_dict()
        )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">

        교육부 NEIS 교육정보 개방 포털<br>

        <b>우리학교 급식 데이터</b>
        · School Meal Data Dashboard

    </div>
    """,
    unsafe_allow_html=True,
)
