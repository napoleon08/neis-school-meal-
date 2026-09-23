import datetime
import re

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="우리학교 급식 데이터",
    page_icon="🍚",
    layout="wide",
)

NEIS_URL = "https://open.neis.go.kr/hub"

DEFAULT_SCHOOL = "송탄고등학교"


# =========================================================
# 공통 API 요청 함수
# =========================================================

def api_get(endpoint, params):
    url = f"{NEIS_URL}/{endpoint}"

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10,
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 중 오류가 발생했습니다: {e}")
        return None

    except ValueError:
        st.error("API 응답을 JSON으로 읽을 수 없습니다.")
        return None


# =========================================================
# 학교 검색
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

    data = api_get("schoolInfo", params)

    if not data:
        return pd.DataFrame()

    try:
        rows = data["schoolInfo"][1]["row"]
    except (KeyError, IndexError, TypeError):
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    return df


# =========================================================
# 학교 이름 보정
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

            new_query = query[:-len(short)] + full

            df = search_schools(new_query)

            if not df.empty:
                return df

    return pd.DataFrame()


# =========================================================
# 학교 표시용 이름
# =========================================================

def school_label(row):

    school_name = row.get("SCHUL_NM", "")
    office_name = row.get("ATPT_OFCDC_SC_NM", "")
    school_type = row.get("SCHUL_KND_SC_NM", "")

    return f"{school_name} | {office_name} | {school_type}"


# =========================================================
# 급식 데이터 가져오기
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
        rows = data["mealServiceDietInfo"][1]["row"]
    except (KeyError, IndexError, TypeError):
        return pd.DataFrame()

    return pd.DataFrame(rows)


# =========================================================
# 메뉴 정리
# =========================================================

def clean_menu(menu_text):

    if not isinstance(menu_text, str):
        return ""

    # 알레르기 번호 제거
    menu_text = re.sub(
        r"\([^)]*\)",
        "",
        menu_text,
    )

    # <br/> 제거
    menu_text = menu_text.replace(
        "<br/>",
        "\n",
    )

    return menu_text.strip()


# =========================================================
# 칼로리 숫자 추출
# =========================================================

def parse_kcal(value):

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
# 한국 시간
# =========================================================

today_korea = (
    datetime.datetime.utcnow()
    + datetime.timedelta(hours=9)
).date()


# =========================================================
# 제목
# =========================================================

st.title("🍚 우리학교 급식 데이터")

st.write(
    "NEIS 나이스 교육정보 API를 이용하여 "
    "학교 급식 정보를 확인할 수 있습니다."
)


# =========================================================
# 사이드바
# =========================================================

st.sidebar.header("🏫 학교 검색")

school_query = st.sidebar.text_input(
    "학교 이름",
    value=DEFAULT_SCHOOL,
)

school_df = school_search_with_fallback(
    school_query
)


# =========================================================
# 학교 선택
# =========================================================

if school_df.empty:

    st.warning(
        "검색된 학교가 없습니다. 학교 이름을 확인해주세요."
    )

    st.stop()


school_options = [
    school_label(row)
    for _, row in school_df.iterrows()
]


selected_school_label = st.sidebar.selectbox(
    "학교 선택",
    school_options,
)


selected_index = school_options.index(
    selected_school_label
)

selected_school = school_df.iloc[selected_index]


school_name = selected_school["SCHUL_NM"]
office_code = selected_school["ATPT_OFCDC_SC_CODE"]
school_code = selected_school["SD_SCHUL_CODE"]


# =========================================================
# 날짜 선택
# =========================================================

selected_date = st.sidebar.date_input(
    "급식 날짜",
    value=today_korea,
)


ymd = selected_date.strftime(
    "%Y%m%d"
)


# =========================================================
# 선택 학교 급식
# =========================================================

st.subheader(
    f"🍽️ {school_name} 급식"
)

meal_df = get_meal(
    school_code,
    office_code,
    ymd,
)


if meal_df.empty:

    st.info(
        "급식이 없는 날입니다."
    )

else:

    row = meal_df.iloc[0]

    menu_text = clean_menu(
        row.get("DDISH_NM", "")
    )

    kcal = parse_kcal(
        row.get("CAL_INFO", "")
    )

    menu_items = [
        item.strip()
        for item in menu_text.split("\n")
        if item.strip()
    ]

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

    st.markdown("### 🍱 오늘의 메뉴")

    for i, menu in enumerate(
        menu_items,
        start=1,
    ):

        st.markdown(
            f"""
            <div style="
                padding: 12px;
                margin: 6px 0;
                border-radius: 10px;
                background-color: #f5f5f5;
                font-size: 18px;
            ">
            <b>{i}.</b> {menu}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("🔎 NEIS 원본 데이터"):

        st.write(
            row.to_dict()
        )


# =========================================================
# 여러 학교 비교
# =========================================================

st.divider()

st.subheader(
    "🏫 여러 학교 급식 비교"
)

comparison_labels = st.multiselect(
    "비교할 학교를 선택하세요.",
    school_options,
    default=school_options[:3]
    if len(school_options) >= 3
    else school_options,
)


if len(comparison_labels) < 3:

    st.info(
        "비교하려면 학교를 3개 이상 선택해주세요."
    )

else:

    comparison_date = selected_date.strftime(
        "%Y%m%d"
    )

    comparison_rows = []

    for label in comparison_labels:

        index = school_options.index(label)

        school = school_df.iloc[index]

        compare_meal = get_meal(
            school["SD_SCHUL_CODE"],
            school["ATPT_OFCDC_SC_CODE"],
            comparison_date,
        )

        if compare_meal.empty:

            comparison_rows.append(
                {
                    "학교": school["SCHUL_NM"],
                    "칼로리": 0,
                    "메뉴수": 0,
                }
            )

            continue

        compare_row = compare_meal.iloc[0]

        compare_menu = clean_menu(
            compare_row.get(
                "DDISH_NM",
                "",
            )
        )

        compare_items = [
            x.strip()
            for x in compare_menu.split("\n")
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
                "학교": school["SCHUL_NM"],
                "칼로리": compare_kcal
                if compare_kcal is not None
                else 0,
                "메뉴수": len(compare_items),
            }
        )

    comparison_df = pd.DataFrame(
        comparison_rows
    )

    st.dataframe(
        comparison_df,
        use_container_width=True,
    )

    fig = px.bar(
        comparison_df,
        x="학교",
        y="칼로리",
        text="칼로리",
        title="학교별 급식 칼로리 비교",
    )

    fig.update_layout(
        xaxis_title="학교",
        yaxis_title="칼로리 (kcal)",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# =========================================================
# 출처
# =========================================================

st.divider()

st.caption(
    "데이터 출처: 교육부 NEIS 교육정보 개방 포털"
)
