import datetime
import re

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# =========================================================
# PAGE CONFIG
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
# GLOBAL DESIGN
# =========================================================

st.markdown(
    """
    <style>

    /* ==============================
       GLOBAL
    ============================== */

    .stApp {
        background:
            linear-gradient(
                180deg,
                #F8FAFC 0%,
                #F1F5F9 100%
            );
        color: #0F172A;
    }

    .main .block-container {
        max-width: 1250px;
        padding-top: 2.5rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3, h4 {
        color: #0F172A !important;
        letter-spacing: -0.03em;
    }

    p, label, span, div {
        color: inherit;
    }


    /* ==============================
       SIDEBAR
    ============================== */

    section[data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 2rem;
    }

    section[data-testid="stSidebar"] h2 {
        color: #0F172A !important;
    }


    /* ==============================
       HERO
    ============================== */

    .hero {
        background:
            linear-gradient(
                135deg,
                #FFFFFF 0%,
                #EFF6FF 100%
            );

        border: 1px solid #DBEAFE;
        border-radius: 24px;

        padding: 34px 38px;

        margin-bottom: 30px;

        box-shadow:
            0 10px 30px rgba(15, 23, 42, 0.06);
    }

    .hero-badge {
        display: inline-block;

        background: #DBEAFE;
        color: #1D4ED8 !important;

        padding: 7px 13px;

        border-radius: 999px;

        font-size: 13px;
        font-weight: 700;

        margin-bottom: 14px;
    }

    .hero-title {
        font-size: 38px;
        line-height: 1.15;

        font-weight: 800;

        color: #0F172A !important;

        margin-bottom: 10px;
    }

    .hero-description {
        font-size: 16px;
        color: #64748B !important;

        line-height: 1.7;

        max-width: 800px;
    }


    /* ==============================
       SECTION TITLE
    ============================== */

    .section-title {
        font-size: 24px;

        font-weight: 800;

        color: #0F172A !important;

        margin-top: 30px;
        margin-bottom: 16px;
    }


    /* ==============================
       STAT CARDS
    ============================== */

    .stat-card {
        background: #FFFFFF;

        border: 1px solid #E2E8F0;

        border-radius: 18px;

        padding: 22px 24px;

        min-height: 125px;

        box-shadow:
            0 6px 20px rgba(15, 23, 42, 0.05);
    }

    .stat-label {
        font-size: 13px;

        font-weight: 700;

        color: #64748B !important;

        margin-bottom: 8px;
    }

    .stat-value {
        font-size: 28px;

        font-weight: 800;

        color: #0F172A !important;
    }

    .stat-sub {
        font-size: 13px;

        color: #94A3B8 !important;

        margin-top: 5px;
    }


    /* ==============================
       MENU CARDS
    ============================== */

    .menu-card {
        display: flex;

        align-items: center;

        background: #FFFFFF;

        border: 1px solid #E2E8F0;

        border-radius: 16px;

        padding: 17px 20px;

        margin-bottom: 10px;

        box-shadow:
            0 4px 12px rgba(15, 23, 42, 0.04);

        transition:
            transform 0.15s ease,
            box-shadow 0.15s ease;
    }

    .menu-card:hover {
        transform: translateY(-2px);

        box-shadow:
            0 8px 20px rgba(15, 23, 42, 0.08);
    }

    .menu-number {
        display: flex;

        align-items: center;
        justify-content: center;

        width: 34px;
        height: 34px;

        border-radius: 10px;

        background: #EFF6FF;

        color: #2563EB !important;

        font-weight: 800;

        margin-right: 14px;

        flex-shrink: 0;
    }

    .menu-name {
        font-size: 17px;

        font-weight: 650;

        color: #1E293B !important;
    }


    /* ==============================
       INFO BOX
    ============================== */

    .info-box {
        background: #FFFFFF;

        border: 1px solid #E2E8F0;

        border-radius: 18px;

        padding: 20px 22px;

        margin-top: 20px;

        color: #475569 !important;

        line-height: 1.7;
    }


    /* ==============================
       FOOTER
    ============================== */

    .footer {
        text-align: center;

        color: #94A3B8 !important;

        font-size: 13px;

        padding-top: 35px;
    }


    /* ==============================
       STREAMLIT INPUTS
    ============================== */

    div[data-baseweb="input"] {
        border-radius: 12px;
    }

    div[data-baseweb="select"] > div {
        border-radius: 12px;
    }


    /* ==============================
       BUTTON
    ============================== */

    .stButton > button {
        border-radius: 12px;

        border: 1px solid #DBEAFE;

        background: #EFF6FF;

        color: #1D4ED8;

        font-weight: 700;
    }

    .stButton > button:hover {
        border-color: #93C5FD;

        background: #DBEAFE;

        color: #1E40AF;
    }


    /* ==============================
       DATAFRAME
    ============================== */

    [data-testid="stDataFrame"] {
        border-radius: 14px;
        overflow: hidden;
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
# MEAL API
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
    """
    <div style="
        padding: 10px 4px 22px 4px;
    ">
        <div style="
            font-size: 25px;
            font-weight: 800;
            color: #0F172A;
        ">
            🍚 급식 데이터
        </div>

        <div style="
            font-size: 13px;
            color: #64748B;
            margin-top: 5px;
        ">
            NEIS School Meal Dashboard
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


st.sidebar.markdown(
    "### 🏫 학교 검색"
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
        "검색된 학교가 없습니다. "
        "학교 이름을 확인해주세요."
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
# HERO
# =========================================================

st.markdown(
    f"""
    <div class="hero">

        <div class="hero-badge">
            NEIS SCHOOL MEAL DATA
        </div>

        <div class="hero-title">
            🍚 우리학교 급식 데이터
        </div>

        <div class="hero-description">
            나이스 교육정보 API를 이용해
            <b>{school_name}</b>의 급식 정보를
            쉽고 깔끔하게 확인할 수 있습니다.
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# MEAL
# =========================================================

st.markdown(
    f"""
    <div class="section-title">
        🍽️ {school_name} 급식
    </div>
    """,
    unsafe_allow_html=True,
)


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
        for item in menu_text.split(
            "\n"
        )
        if item.strip()
    ]


    # =====================================================
    # STATS
    # =====================================================

    c1, c2, c3 = st.columns(3)


    with c1:

        st.markdown(
            f"""
            <div class="stat-card">

                <div class="stat-label">
                    MENU
                </div>

                <div class="stat-value">
                    {len(menu_items)}
                </div>

                <div class="stat-sub">
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
            <div class="stat-card">

                <div class="stat-label">
                    ENERGY
                </div>

                <div class="stat-value">
                    {kcal_text}
                </div>

                <div class="stat-sub">
                    급식 열량 정보
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    with c3:

        st.markdown(
            f"""
            <div class="stat-card">

                <div class="stat-label">
                    DATE
                </div>

                <div class="stat-value"
                     style="font-size:24px;">
                    {selected_date.strftime('%Y.%m.%d')}
                </div>

                <div class="stat-sub">
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
        <div class="section-title">
            🍱 오늘의 메뉴
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
    # RAW DATA
    # =====================================================

    with st.expander(
        "🔎 NEIS 원본 데이터 보기"
    ):

        st.json(
            row.to_dict()
        )


# =========================================================
# SCHOOL COMPARISON
# =========================================================

st.divider()


st.markdown(
    """
    <div class="section-title">
        🏫 여러 학교 급식 비교
    </div>
    """,
    unsafe_allow_html=True,
)


st.caption(
    "같은 검색 결과에 포함된 학교를 선택하여 "
    "해당 날짜의 급식 열량을 비교합니다."
)


comparison_labels = st.multiselect(
    "비교할 학교",
    school_options,
    default=(
        school_options[:3]
        if len(school_options) >= 3
        else school_options
    ),
)


if len(comparison_labels) < 3:

    st.info(
        "학교를 3개 이상 선택하면 비교할 수 있습니다."
    )

else:

    comparison_rows = []


    for label in comparison_labels:

        index = school_options.index(
            label
        )

        school = school_df.iloc[
            index
        ]


        compare_meal = get_meal(
            school["SD_SCHUL_CODE"],
            school["ATPT_OFCDC_SC_CODE"],
            ymd,
        )


        if compare_meal.empty:

            comparison_rows.append(
                {
                    "학교": school[
                        "SCHUL_NM"
                    ],
                    "칼로리": 0,
                    "메뉴수": 0,
                }
            )

            continue


        compare_row = (
            compare_meal.iloc[0]
        )


        compare_menu = clean_menu(
            compare_row.get(
                "DDISH_NM",
                "",
            )
        )


        compare_items = [
            x.strip()
            for x in compare_menu.split(
                "\n"
            )
            if x.strip()
        ]


        compare_kcal = parse_kcal(
            compare_row.get(
                "CAL_INFO",
                "",
            )
        )


        comparison_rows.append(
            {
                "학교": school[
                    "SCHUL_NM"
                ],
                "칼로리": (
                    compare_kcal
                    if compare_kcal
                    is not None
                    else 0
                ),
                "메뉴수": len(
                    compare_items
                ),
            }
        )


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
        title="학교별 급식 열량 비교",
    )


    fig.update_traces(
        marker_color="#2563EB",
        texttemplate="%{text:,.0f}",
        textposition="outside",
    )


    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="#0F172A"
        ),
        xaxis_title="학교",
        yaxis_title="칼로리 (kcal)",
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
    )


    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
        Data source · 교육부 NEIS 교육정보 개방 포털
        <br>
        School Meal Data Dashboard
    </div>
    """,
    unsafe_allow_html=True,
)
