import re

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="메뉴별 급식 분석",
    page_icon="🍽️",
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
                #F0FDF4
            );

        border: 1px solid #DCFCE7;

        border-radius: 24px;

        padding: 32px 36px;

        margin-bottom: 28px;

        box-shadow:
            0 10px 30px
            rgba(15, 23, 42, 0.06);
    }

    .badge {
        display: inline-block;

        background: #DCFCE7;

        color: #15803D !important;

        padding: 7px 12px;

        border-radius: 999px;

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

        font-size: 16px;

        line-height: 1.7;

        margin-top: 8px;
    }

    .stat-card {
        background: #FFFFFF;

        border: 1px solid #E2E8F0;

        border-radius: 18px;

        padding: 22px;

        min-height: 120px;

        box-shadow:
            0 6px 18px
            rgba(15, 23, 42, 0.05);
    }

    .stat-label {
        color: #64748B !important;

        font-size: 13px;

        font-weight: 700;

        margin-bottom: 8px;
    }

    .stat-value {
        color: #0F172A !important;

        font-size: 24px;

        font-weight: 800;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HERO
# =========================================================

st.markdown(
    f"""
    <div class="hero">

        <div class="badge">
            MENU ANALYTICS
        </div>

        <div class="title">
            🍽️ 메뉴별 급식 분석
        </div>

        <div class="subtitle">
            {SCHOOL_NAME}의 급식 데이터를 분석하여
            어떤 메뉴가 자주 등장하는지 확인합니다.
            <br>
            분석 기간 · 2025.09 ~ 2026.09
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# API KEY
# =========================================================

try:

    API_KEY = st.secrets[
        "NEIS_API_KEY"
    ]

except Exception:

    st.error(
        "NEIS_API_KEY가 설정되지 않았습니다."
    )

    st.info(
        """
        Streamlit Cloud에서

        Settings → Secrets

        로 이동한 후 NEIS_API_KEY를 등록해주세요.
        """
    )

    st.stop()


# =========================================================
# GET ALL DATA
# =========================================================

@st.cache_data(ttl=3600)
def get_all_meals():

    all_rows = []

    page_index = 1

    page_size = 1000


    while True:

        params = {
            "KEY": API_KEY,
            "Type": "json",
            "pIndex": page_index,
            "pSize": page_size,
            "ATPT_OFCDC_SC_CODE": OFFICE_CODE,
            "SD_SCHUL_CODE": SCHOOL_CODE,
            "MMEAL_SC_CODE": 2,
            "MLSV_FROM_YMD": "20250901",
            "MLSV_TO_YMD": "20260930",
        }


        try:

            response = requests.get(
                f"{NEIS_URL}/mealServiceDietInfo",
                params=params,
                timeout=20,
            )

            response.raise_for_status()

            data = response.json()

        except Exception as e:

            st.error(
                f"API 요청 오류: {e}"
            )

            break


        try:

            rows = data[
                "mealServiceDietInfo"
            ][1]["row"]

        except (
            KeyError,
            IndexError,
            TypeError,
        ):

            break


        if not rows:
            break


        all_rows.extend(
            rows
        )


        if len(rows) < page_size:
            break


        page_index += 1


        if page_index > 100:
            break


    return pd.DataFrame(
        all_rows
    )


# =========================================================
# DATA
# =========================================================

df = get_all_meals()


if df.empty:

    st.warning(
        "급식 데이터를 찾을 수 없습니다."
    )

    st.stop()


# =========================================================
# COUNT MENU
# =========================================================

menu_days = {}


for _, row in df.iterrows():

    date = row.get(
        "MLSV_YMD",
        "",
    )

    menu_text = row.get(
        "DDISH_NM",
        "",
    )


    if not isinstance(
        menu_text,
        str,
    ):
        continue


    menus = menu_text.split(
        "<br/>"
    )


    for menu in menus:

        menu = re.sub(
            r"\([^)]*\)",
            "",
            menu,
        )


        menu = menu.strip()


        if not menu:
            continue


        if menu not in menu_days:

            menu_days[menu] = set()


        menu_days[menu].add(
            date
        )


# =========================================================
# RESULT
# =========================================================

result = pd.DataFrame(
    [
        {
            "메뉴": menu,
            "등장일수": len(days),
        }

        for menu, days
        in menu_days.items()
    ]
)


result = result.sort_values(
    "등장일수",
    ascending=False,
).reset_index(
    drop=True
)


# =========================================================
# TOP N
# =========================================================

top_n = st.slider(
    "TOP 메뉴 개수",
    min_value=5,
    max_value=20,
    value=10,
)


top_df = result.head(
    top_n
)


# =========================================================
# STATISTICS
# =========================================================

total_days = df[
    "MLSV_YMD"
].nunique()


if len(result) > 0:

    first_menu = result.iloc[0][
        "메뉴"
    ]

    first_count = result.iloc[0][
        "등장일수"
    ]

else:

    first_menu = "-"

    first_count = 0


percentage = 0

if total_days > 0:

    percentage = (
        first_count
        / total_days
        * 100
    )


c1, c2, c3 = st.columns(3)


with c1:

    st.markdown(
        f"""
        <div class="stat-card">

            <div class="stat-label">
                MEAL DAYS
            </div>

            <div class="stat-value">
                {total_days}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with c2:

    st.markdown(
        f"""
        <div class="stat-card">

            <div class="stat-label">
                #1 MENU
            </div>

            <div class="stat-value">
                {first_menu}
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
                APPEARANCE RATE
            </div>

            <div class="stat-value">
                {percentage:.1f}%
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# CHART
# =========================================================

st.markdown(
    "## 📊 메뉴 TOP 순위"
)


chart_df = top_df.sort_values(
    "등장일수"
)


fig = px.bar(
    chart_df,
    x="등장일수",
    y="메뉴",
    orientation="h",
    text="등장일수",
)


fig.update_traces(
    marker_color="#16A34A",
    textposition="outside",
)


fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",

    font=dict(
        color="#0F172A"
    ),

    xaxis=dict(
        title="등장 일수",
        gridcolor="#E2E8F0",
        zeroline=False,
    ),

    yaxis=dict(
        title="",
        automargin=True,
    ),

    margin=dict(
        l=20,
        r=40,
        t=20,
        b=20,
    ),

    height=600,
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


# =========================================================
# TABLE
# =========================================================

st.markdown(
    "## 📋 메뉴별 등장 횟수"
)


st.dataframe(
    top_df,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# ALL DATA
# =========================================================

with st.expander(
    "전체 메뉴 데이터 보기"
):

    st.dataframe(
        result,
        use_container_width=True,
        hide_index=True,
    )
