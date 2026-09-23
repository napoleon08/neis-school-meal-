import datetime
import re

import pandas as pd
import requests
import streamlit as st


# =========================================================
# 기본 설정
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
            f"급식 API 요청 오류: {e}"
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
# 메뉴 정리
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

    # 줄바꿈
    text = text.replace(
        "<br/>",
        "\n",
    )

    return text.strip()


# =========================================================
# 제목
# =========================================================

st.title(
    "📅 달력별 급식"
)

st.write(
    f"{SCHOOL_NAME}의 날짜별 급식을 확인할 수 있습니다."
)


# =========================================================
# 날짜
# =========================================================

today = (
    datetime.datetime.utcnow()
    + datetime.timedelta(hours=9)
).date()


selected_date = st.date_input(
    "급식 날짜를 선택하세요.",
    value=today,
)


ymd = selected_date.strftime(
    "%Y%m%d"
)


# =========================================================
# 알레르기 표시
# =========================================================

show_allergy = st.toggle(
    "알레르기 번호 표시",
    value=True,
)


# =========================================================
# API 호출
# =========================================================

meal_df = get_meal(
    ymd
)


if meal_df.empty:

    st.info(
        "급식이 없는 날입니다."
    )

else:

    row = meal_df.iloc[0]

    menu_text = row.get(
        "DDISH_NM",
        "",
    )

    kcal = row.get(
        "CAL_INFO",
        "-",
    )

    origin = row.get(
        "ORPLC_INFO",
        "",
    )

    nutrition = row.get(
        "NTR_INFO",
        "",
    )


    # -----------------------------------------------------
    # 메뉴 처리
    # -----------------------------------------------------

    if show_allergy:

        display_text = menu_text

        display_text = display_text.replace(
            "<br/>",
            "\n",
        )

    else:

        display_text = clean_menu(
            menu_text
        )


    menu_items = [
        item.strip()
        for item in display_text.split("\n")
        if item.strip()
    ]


    # -----------------------------------------------------
    # 통계
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "메뉴 수",
            len(menu_items),
        )

    with col2:

        st.metric(
            "칼로리",
            kcal,
        )

    with col3:

        st.metric(
            "날짜",
            selected_date.strftime(
                "%Y-%m-%d"
            ),
        )


    # -----------------------------------------------------
    # 메뉴
    # -----------------------------------------------------

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
                padding: 14px;
                margin: 7px 0;
                border-radius: 12px;
                background: #f5f5f5;
                font-size: 18px;
            ">
                <b>{i}.</b> {menu}
            </div>
            """,
            unsafe_allow_html=True,
        )


    # -----------------------------------------------------
    # 영양 정보
    # -----------------------------------------------------

    with st.expander(
        "🥗 영양 정보"
    ):

        if nutrition:
            st.write(nutrition)
        else:
            st.write(
                "영양 정보가 없습니다."
            )


    # -----------------------------------------------------
    # 원산지
    # -----------------------------------------------------

    with st.expander(
        "🌾 원산지 정보"
    ):

        if origin:
            st.write(origin)
        else:
            st.write(
                "원산지 정보가 없습니다."
            )


    # -----------------------------------------------------
    # 원본 데이터
    # -----------------------------------------------------

    with st.expander(
        "🔎 NEIS 원본 데이터"
    ):

        st.write(
            row.to_dict()
        )
