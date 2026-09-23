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


# =========================================================
# CONSTANTS
# =========================================================

NEIS_URL = "https://open.neis.go.kr/hub"
DEFAULT_SCHOOL = "송탄고등학교"


# =========================================================
# DESIGN
# =========================================================

st.markdown(
    """
    <style>

    /* =====================================================
       MAIN PAGE
       Светлый фон → тёмный текст
       ===================================================== */

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
        padding-bottom: 50px;
    }


    /* =====================================================
       MAIN TEXT
       ===================================================== */

    .main p {
        color: #1F2933 !important;
    }

    .main h1,
    .main h2,
    .main h3,
    .main h4 {
        color: #102A43 !important;
    }


    /* =====================================================
       SIDEBAR
       Тёмный фон → светлый текст
       ===================================================== */

    section[data-testid="stSidebar"] {
        background-color: #102A43 !important;
    }

    section[data-testid="stSidebar"] > div {
        background-color: #102A43 !important;
    }

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {
        color: #F8FAFC !important;
    }


    /* =====================================================
       SIDEBAR INPUT
       ===================================================== */

    section[data-testid="stSidebar"] input {
        background-color: #FFFFFF !important;
        color: #1F2933 !important;
        border-radius: 8px !important;
    }

    section[data-testid="stSidebar"] input::placeholder {
        color: #6B7280 !important;
    }


    /* =====================================================
       SIDEBAR SELECT
       ===================================================== */

    section[data-testid="stSidebar"]
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #1F2933 !important;
        border-radius: 8px !important;
    }

    section[data-testid="stSidebar"]
    div[data-baseweb="select"] span {
        color: #1F2933 !important;
    }


    /* =====================================================
       MAIN INPUT
       Светлый фон → тёмный текст
       ===================================================== */

    div[data-baseweb="input"] {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
    }

    div[data-baseweb="input"] input {
        background-color: #FFFFFF !important;
        color: #1F2933 !important;
    }

    input {
        color: #1F2933 !important;
        background-color: #FFFFFF !important;
    }

    textarea {
        color: #1F2933 !important;
        background-color: #FFFFFF !important;
    }


    /* =====================================================
       MAIN SELECT
       ===================================================== */

    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #1F2933 !important;
        border-radius: 8px !important;
    }

    div[data-baseweb="select"] span {
        color: #1F2933 !important;
    }


    /* =====================================================
       METRIC CARDS
       ===================================================== */

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

    [data-testid="stMetricDelta"] {
        color: #164A41 !important;
    }


    /* =====================================================
       EXPANDER
       ===================================================== */

    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D9D4C8 !important;
        border-radius: 10px !important;
    }

    [data-testid="stExpander"] summary {
        color: #102A43 !important;
    }


    /* =====================================================
       BUTTON
       ===================================================== */

    .stButton button {
        background-color: #164A41 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
    }

    .stButton button:hover {
        background-color: #123B34 !important;
        color: #FFFFFF !important;
    }


    /* =====================================================
       ALERTS
       ===================================================== */

    [data-testid="stAlert"] {
        color: #1F2933 !important;
    }


    /* =====================================================
       LINKS
       ===================================================== */

    a {
        color: #164A41 !important;
    }


    /* =====================================================
       DIVIDERS
       ===================================================== */

    hr {
        border-color: #D9D4C8 !important;
    }


    /* =====================================================
       DATAFRAME
       ===================================================== */

    [data-testid="stDataFrame"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D9D4C8 !important;
        border-radius: 10px !important;
        overflow: hidden;
    }


    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# API REQUEST
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


# =========================================================
# SCHOOL SEARCH FALLBACK
# =========================================================

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


# =========================================================
# SCHOOL LABEL
# =========================================================

def school_label(row):

    return (
        f"{row.get('SCHUL_NM', '')}"
        f" | "
        f"{row.get('ATPT_OFCDC_SC_NM', '')}"
        f" | "
        f"{row.get('SCHUL_KND_SC_NM', '')}"
    )


# =========================================================
# GET MEAL DATA
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

    # Remove allergen numbers
    text = re.sub(
        r"\([^)]*\)",
        "",
        text,
    )

    # Convert HTML line breaks
    text = text.replace(
        "<br/>",
        "\n",
    )

    return text.strip()


# =========================================================
# CALORIE
# =========================================================

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
# KOREA DATE
# =========================================================

today_korea = (
    datetime.datetime.utcnow()
    + datetime.timedelta(hours=9)
).date()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown(
    "## 🍚 급식 데이터"
)

st.sidebar.caption(
    "NEIS SCHOOL MEAL"
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


selected_date = st.sidebar.date_input(
    "급식 날짜",
    value=today_korea,
)


ymd = selected_date.strftime(
    "%Y%m%d"
)


# =========================================================
# TITLE
# =========================================================

st.title(
    "🍚 우리학교 급식 데이터"
)

st.write(
    "NEIS 나이스 교육정보 API를 이용하여 "
    "학교 급식 정보를 확인할 수 있습니다."
)


# =========================================================
# SCHOOL TITLE
# =========================================================

st.header(
    f"🍽️ {school_name} 급식"
)


# =========================================================
# GET MEAL
# =========================================================

meal_df = get_meal(
    school_code,
    office_code,
    ymd,
)


if meal_df.empty:

    st.info(
        "📭 선택한 날짜에는 급식 데이터가 없습니다."
    )

else:

    row = meal_df.iloc[0]


    # =====================================================
    # MENU
    # =====================================================

    menu_text = clean_menu(
        row.get(
            "DDISH_NM",
            "",
        )
    )


    menu_items = [
        item.strip()
        for item in menu_text.split("\n")
        if item.strip()
    ]


    # =====================================================
    # CALORIE
    # =====================================================

    kcal = parse_kcal(
        row.get(
            "CAL_INFO",
            "",
        )
    )


    # =====================================================
    # METRICS
    # =====================================================

    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "메뉴 수",
            len(menu_items),
        )


    with col2:

        if kcal is not None:

            st.metric(
                "칼로리",
                f"{kcal:,.0f} kcal",
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
                "%Y-%m-%d"
            ),
        )


    # =====================================================
    # TODAY MENU
    # =====================================================

    st.subheader(
        "🍱 오늘의 메뉴"
    )


    for i, menu in enumerate(
        menu_items,
        start=1,
    ):

        st.markdown(
            f"""
            <div style="
                background-color:#FFFFFF;
                border:1px solid #D9D4C8;
                border-radius:10px;
                padding:14px 18px;
                margin-bottom:8px;
                color:#1F2933;
                font-size:16px;
            ">
                <b style="color:#164A41;">
                    {i}.
                </b>
                <span style="color:#1F2933;">
                    {menu}
                </span>
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
# SCHOOL COMPARISON
# =========================================================

st.divider()

st.header(
    "🏫 학교별 급식 비교"
)


comparison_options = school_options


selected_comparison = st.multiselect(
    "비교할 학교를 선택하세요.",
    comparison_options,
    default=(
        comparison_options[:3]
        if len(comparison_options) >= 3
        else comparison_options
    ),
)


if len(selected_comparison) < 2:

    st.info(
        "두 개 이상의 학교를 선택하면 비교할 수 있습니다."
    )

else:

    comparison_rows = []


    for label in selected_comparison:

        idx = comparison_options.index(
            label
        )

        school = school_df.iloc[idx]


        comparison_meal = get_meal(
            school["SD_SCHUL_CODE"],
            school["ATPT_OFCDC_SC_CODE"],
            ymd,
        )


        if comparison_meal.empty:
            continue


        comparison_row = (
            comparison_meal.iloc[0]
        )


        kcal_value = parse_kcal(
            comparison_row.get(
                "CAL_INFO",
                "",
            )
        )


        if kcal_value is not None:

            comparison_rows.append(
                {
                    "학교": school["SCHUL_NM"],
                    "칼로리": kcal_value,
                }
            )


    if comparison_rows:

        comparison_df = pd.DataFrame(
            comparison_rows
        )


        st.dataframe(
            comparison_df,
            use_container_width=True,
            hide_index=True,
        )


        fig = px.bar(
            comparison_df,
            x="학교",
            y="칼로리",
            text="칼로리",
            title="학교별 급식 칼로리 비교",
        )


        fig.update_traces(
            marker_color="#164A41"
        )


        fig.update_layout(
            paper_bgcolor="#F7F4EC",
            plot_bgcolor="#FFFFFF",
            font_color="#1F2933",
            title_font_color="#102A43",
            xaxis_title="학교",
            yaxis_title="칼로리 (kcal)",
        )


        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    else:

        st.info(
            "비교할 학교의 급식 데이터가 없습니다."
        )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "교육부 NEIS 교육정보 개방 포털 · "
    "우리학교 급식 데이터"
)
