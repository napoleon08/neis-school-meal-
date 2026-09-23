import re

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# =========================================================
# 기본 설정
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
# 제목
# =========================================================

st.title(
    "🍽️ 메뉴별 급식 분석"
)

st.write(
    "2025년 9월부터 2026년 9월까지 "
    "급식 메뉴가 얼마나 자주 등장했는지 분석합니다."
)


# =========================================================
# API Key 확인
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
        "Streamlit Cloud의 Settings → Secrets에서 "
        "NEIS_API_KEY를 등록해주세요."
    )

    st.stop()


# =========================================================
# 급식 전체 데이터 가져오기
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


        all_rows.extend(rows)


        if len(rows) < page_size:
            break


        page_index += 1


        # 안전장치
        if page_index > 100:
            break


    return pd.DataFrame(
        all_rows
    )


# =========================================================
# 데이터 가져오기
# =========================================================

df = get_all_meals()


if df.empty:

    st.warning(
        "급식 데이터를 찾을 수 없습니다."
    )

    st.stop()


# =========================================================
# 메뉴별 등장 날짜 계산
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


    # <br/> 기준으로 메뉴 분리
    menus = menu_text.split(
        "<br/>"
    )


    for menu in menus:

        # 알레르기 번호 제거
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


        # 같은 날짜에는 한 번만 계산
        menu_days[menu].add(
            date
        )


# =========================================================
# 분석 결과
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
# TOP N 선택
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
# 주요 지표
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


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "급식 일수",
        total_days,
    )


with col2:

    st.metric(
        "가장 많이 나온 메뉴",
        first_menu,
    )


with col3:

    st.metric(
        "등장 비율",
        f"{percentage:.1f}%",
    )


# =========================================================
# 그래프
# =========================================================

st.subheader(
    f"📊 메뉴 TOP {top_n}"
)


fig = px.bar(
    top_df.sort_values(
        "등장일수"
    ),
    x="등장일수",
    y="메뉴",
    orientation="h",
    text="등장일수",
    title=f"{SCHOOL_NAME} 메뉴별 등장 일수",
)


fig.update_layout(
    xaxis_title="등장 일수",
    yaxis_title="메뉴",
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


# =========================================================
# 표
# =========================================================

st.subheader(
    "📋 메뉴별 등장 횟수"
)


st.dataframe(
    top_df,
    use_container_width=True,
)


# =========================================================
# 전체 데이터
# =========================================================

with st.expander(
    "전체 메뉴 데이터 보기"
):

    st.dataframe(
        result,
        use_container_width=True,
    )
