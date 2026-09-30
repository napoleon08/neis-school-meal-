import datetime
import re

import pandas as pd
import requests
import streamlit as st


# =========================================================
# 페이지 기본 설정
# =========================================================

st.set_page_config(
    page_title="학교 급식 찾아보기",
    page_icon="🍚",
    layout="wide"
)


# =========================================================
# NEIS API 주소
# =========================================================

학교정보_API = (
    "https://open.neis.go.kr/hub/schoolInfo"
)

급식정보_API = (
    "https://open.neis.go.kr/hub/mealServiceDietInfo"
)


# =========================================================
# 평택 지역 고등학교 목록
# =========================================================
#
# 급식 데이터는 각 학교의 NEIS 학교정보를 이용해서
# 실제 교육청 코드와 학교 코드를 찾아온다.
#
# 아래 목록은 "평택 지역 고등학교"를 선택하기 위한
# 검색 목록이다.
# =========================================================

평택_고등학교 = [
    "경기물류고등학교",
    "동일공업고등학교",
    "비전고등학교",
    "송탄고등학교",
    "송탄제일고등학교",
    "신한고등학교",
    "안중고등학교",
    "은혜고등학교",
    "이충고등학교",
    "진위고등학교",
    "청담고등학교",
    "청북고등학교",
    "태광고등학교",
    "평택고등학교",
    "평택마이스터고등학교",
    "평택여자고등학교",
    "한국관광고등학교",
    "한광고등학교",
    "한광여자고등학교",
    "현화고등학교",
    "효명고등학교",
    "용죽고등학교",
]


# =========================================================
# 디자인
# =========================================================

st.markdown(
    """
    <style>

    /* 전체 배경 */

    .stApp {
        background-color: #F7F4EC;
        color: #1F2933;
    }

    .main {
        background-color: #F7F4EC;
    }

    .main .block-container {
        max-width: 1200px;
        padding-top: 35px;
        padding-bottom: 60px;
    }


    /* 제목 */

    .main h1,
    .main h2,
    .main h3,
    .main h4 {
        color: #102A43;
    }


    /* 기본 글자 */

    .main p {
        color: #1F2933;
    }


    /* 입력창 */

    div[data-baseweb="input"] {
        background-color: #FFFFFF;
        border-radius: 10px;
    }

    div[data-baseweb="input"] input {
        background-color: #FFFFFF;
        color: #1F2933;
    }


    /* 선택창 */

    div[data-baseweb="select"] {
        background-color: #FFFFFF;
    }


    /* 메트릭 */

    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #D9D4C8;
        border-radius: 14px;
        padding: 20px;
    }

    [data-testid="stMetricLabel"] {
        color: #52606D;
        font-size: 15px;
    }

    [data-testid="stMetricValue"] {
        color: #102A43;
        font-size: 30px;
        font-weight: 700;
    }


    /* 구분선 */

    hr {
        border-color: #D9D4C8;
    }


    /* 버튼 */

    .stButton button {
        background-color: #164A41;
        color: #FFFFFF;
        border: none;
        border-radius: 9px;
    }

    .stButton button:hover {
        background-color: #102A43;
        color: #FFFFFF;
    }


    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 한국 시간 기준 오늘 날짜
# =========================================================

def 한국_오늘():

    현재_UTC = datetime.datetime.now(
        datetime.timezone.utc
    )

    한국_시간 = 현재_UTC + datetime.timedelta(
        hours=9
    )

    return 한국_시간.date()


# =========================================================
# 학교 이름 줄임말 변환
# =========================================================

def 학교이름_보정(검색어):

    검색어 = 검색어.strip()

    if not 검색어:
        return []


    검색어목록 = [
        검색어
    ]


    # 여고 → 여자고등학교

    if 검색어.endswith("여고"):

        정식이름 = (
            검색어[:-2]
            + "여자고등학교"
        )

        검색어목록.append(
            정식이름
        )


    # 여중 → 여자중학교

    if 검색어.endswith("여중"):

        정식이름 = (
            검색어[:-2]
            + "여자중학교"
        )

        검색어목록.append(
            정식이름
        )


    # 여초 → 여자초등학교

    if 검색어.endswith("여초"):

        정식이름 = (
            검색어[:-2]
            + "여자초등학교"
        )

        검색어목록.append(
            정식이름
        )


    # 고 → 고등학교

    if 검색어.endswith("고"):

        정식이름 = (
            검색어[:-1]
            + "고등학교"
        )

        검색어목록.append(
            정식이름
        )


    # 중 → 중학교

    if 검색어.endswith("중"):

        정식이름 = (
            검색어[:-1]
            + "중학교"
        )

        검색어목록.append(
            정식이름
        )


    # 초 → 초등학교

    if 검색어.endswith("초"):

        정식이름 = (
            검색어[:-1]
            + "초등학교"
        )

        검색어목록.append(
            정식이름
        )


    # 중복 제거

    return list(
        dict.fromkeys(
            검색어목록
        )
    )


# =========================================================
# NEIS 학교정보 API
# =========================================================

@st.cache_data(ttl=3600)
def 학교정보_검색(학교이름):

    검색어목록 = 학교이름_보정(
        학교이름
    )


    if not 검색어목록:
        return pd.DataFrame()


    결과목록 = []


    for 검색어 in 검색어목록:

        매개변수 = {
            "Type": "json",
            "SCHUL_NM": 검색어
        }


        try:

            응답 = requests.get(
                학교정보_API,
                params=매개변수,
                timeout=10
            )

            응답.raise_for_status()

            데이터 = 응답.json()


        except (
            requests.exceptions.RequestException,
            ValueError
        ):

            continue


        try:

            학교행 = 데이터[
                "schoolInfo"
            ][1]["row"]


        except (
            KeyError,
            IndexError,
            TypeError
        ):

            continue


        결과목록.extend(
            학교행
        )


    if not 결과목록:

        return pd.DataFrame()


    결과 = pd.DataFrame(
        결과목록
    )


    # 고등학교만 표시

    if "SCHUL_KND_SC_NM" in 결과.columns:

        결과 = 결과[
            결과["SCHUL_KND_SC_NM"]
            .astype(str)
            .str.contains(
                "고등학교",
                na=False
            )
        ]


    # 검색어가 학교 이름에 포함된 결과만 유지

    if "SCHUL_NM" in 결과.columns:

        결과 = 결과[
            결과["SCHUL_NM"]
            .astype(str)
            .str.contains(
                학교이름.strip(),
                na=False
            )
        ]


    # 중복 제거

    결과 = 결과.drop_duplicates(
        subset=[
            "ATPT_OFCDC_SC_CODE",
            "SD_SCHUL_CODE"
        ]
    )


    return 결과


# =========================================================
# 평택 고등학교 정보 가져오기
# =========================================================

@st.cache_data(ttl=3600)
def 평택학교_정보():

    결과목록 = []


    for 학교이름 in 평택_고등학교:

        매개변수 = {
            "Type": "json",
            "SCHUL_NM": 학교이름
        }


        try:

            응답 = requests.get(
                학교정보_API,
                params=매개변수,
                timeout=10
            )

            응답.raise_for_status()

            데이터 = 응답.json()


        except (
            requests.exceptions.RequestException,
            ValueError
        ):

            continue


        try:

            학교행 = 데이터[
                "schoolInfo"
            ][1]["row"]


        except (
            KeyError,
            IndexError,
            TypeError
        ):

            continue


        for 학교 in 학교행:

            학교명 = str(
                학교.get(
                    "SCHUL_NM",
                    ""
                )
            )

            지역 = str(
                학교.get(
                    "LCTN_SC_NM",
                    ""
                )
            )


            # 평택시 학교만 남김

            if (
                "평택" in 지역
                and 학교명 in 평택_고등학교
            ):

                결과목록.append(
                    {
                        "학교명": 학교명,
                        "지역": 지역,
                        "교육청코드": 학교.get(
                            "ATPT_OFCDC_SC_CODE"
                        ),
                        "학교코드": 학교.get(
                            "SD_SCHUL_CODE"
                        )
                    }
                )


    if not 결과목록:

        return pd.DataFrame()


    결과 = pd.DataFrame(
        결과목록
    )


    결과 = 결과.drop_duplicates(
        subset=[
            "교육청코드",
            "학교코드"
        ]
    )


    결과 = 결과.sort_values(
        by="학교명"
    )


    return 결과


# =========================================================
# NEIS 급식 API
# =========================================================

@st.cache_data(ttl=600)
def 급식정보_검색(
    교육청코드,
    학교코드,
    날짜
):

    매개변수 = {
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": 교육청코드,
        "SD_SCHUL_CODE": 학교코드,
        "MMEAL_SC_CODE": 2,
        "MLSV_FROM_YMD": 날짜,
        "MLSV_TO_YMD": 날짜,
        "pSize": 1000,
        "pIndex": 1
    }


    try:

        응답 = requests.get(
            급식정보_API,
            params=매개변수,
            timeout=10
        )

        응답.raise_for_status()

        데이터 = 응답.json()


    except requests.exceptions.RequestException:

        return pd.DataFrame(), "연결오류"


    except ValueError:

        return pd.DataFrame(), "응답오류"


    # =====================================================
    # 정상적인 급식 데이터
    # =====================================================

    try:

        급식행 = 데이터[
            "mealServiceDietInfo"
        ][1]["row"]


        return (
            pd.DataFrame(급식행),
            "정상"
        )


    except (
        KeyError,
        IndexError,
        TypeError
    ):

        pass


    # =====================================================
    # 급식 데이터 없음
    # =====================================================

    try:

        결과코드 = 데이터[
            "RESULT"
        ]["CODE"]


        if 결과코드 == "INFO-200":

            return (
                pd.DataFrame(),
                "급식없음"
            )


    except (
        KeyError,
        TypeError
    ):

        pass


    return (
        pd.DataFrame(),
        "급식없음"
    )


# =========================================================
# 칼로리 숫자 추출
# =========================================================

def 칼로리_추출(칼로리정보):

    if not isinstance(
        칼로리정보,
        str
    ):

        return None


    결과 = re.search(
        r"[\d.]+",
        칼로리정보
    )


    if 결과:

        return float(
            결과.group()
        )


    return None


# =========================================================
# 메뉴 분리
# =========================================================

def 메뉴_분리(전체메뉴):

    if not isinstance(
        전체메뉴,
        str
    ):

        return []


    메뉴목록 = 전체메뉴.split(
        "<br/>"
    )


    return [
        메뉴.strip()
        for 메뉴 in 메뉴목록
        if 메뉴.strip()
    ]


# =========================================================
# 알레르기 번호 추출
# =========================================================

def 알레르기_번호(메뉴):

    결과 = re.findall(
        r"\(([^)]*)\)",
        메뉴
    )


    if 결과:

        return 결과[-1]


    return ""


# =========================================================
# 앱 제목
# =========================================================

st.title(
    "🍚 학교 급식 찾아보기"
)

st.write(
    "평택 지역 고등학교를 선택하고 "
    "날짜별 중식 메뉴와 칼로리를 확인해 보세요."
)


# =========================================================
# 학교 선택
# =========================================================

st.divider()

st.header(
    "🏫 평택 고등학교 선택"
)


평택학교 = 평택학교_정보()


if 평택학교.empty:

    st.error(
        "평택 지역 고등학교 정보를 불러오지 못했습니다."
    )

    st.stop()


학교표시목록 = []

for _, 학교 in 평택학교.iterrows():

    학교표시목록.append(
        f"{학교['학교명']} · {학교['지역']}"
    )


선택학교 = st.selectbox(
    "학교를 선택하세요.",
    학교표시목록
)


선택정보 = 평택학교[
    (
        평택학교["학교명"]
        + " · "
        + 평택학교["지역"]
    )
    == 선택학교
].iloc[0]


선택학교이름 = 선택정보[
    "학교명"
]

선택지역 = 선택정보[
    "지역"
]

선택교육청코드 = 선택정보[
    "교육청코드"
]

선택학교코드 = 선택정보[
    "학교코드"
]


st.success(
    f"선택한 학교: "
    f"**{선택학교이름}** · {선택지역}"
)


# =========================================================
# 학교 이름 검색
# =========================================================

st.subheader(
    "🔎 학교 이름으로 찾기"
)

검색어 = st.text_input(
    "학교 이름을 입력하세요.",
    placeholder="예: 송탄고, 평택고, 평택여고"
)


if 검색어:

    검색결과 = 학교정보_검색(
        검색어
    )


    if 검색결과.empty:

        st.info(
            "학교를 찾지 못했습니다. "
            "학교 이름을 다시 확인해 주세요."
        )


    else:

        검색학교목록 = []

        for _, 학교 in 검색결과.iterrows():

            학교명 = 학교.get(
                "SCHUL_NM",
                ""
            )

            지역 = 학교.get(
                "LCTN_SC_NM",
                ""
            )


            검색학교목록.append(
                f"{학교명} · {지역}"
            )


        st.write(
            "검색 결과"
        )


        st.selectbox(
            "검색된 학교",
            검색학교목록
        )


# =========================================================
# 날짜 선택
# =========================================================

st.divider()

st.header(
    "📅 급식 날짜"
)


날짜열, 안내열 = st.columns(
    [1, 1]
)


with 날짜열:

    선택날짜 = st.date_input(
        "날짜를 선택하세요.",
        value=한국_오늘()
    )


with 안내열:

    st.write("")

    st.caption(
        "날짜의 기본값은 한국 시간(UTC+9)의 오늘입니다."
    )


# =========================================================
# 급식 데이터 조회
# =========================================================

조회날짜 = 선택날짜.strftime(
    "%Y%m%d"
)


급식표, 상태 = 급식정보_검색(
    선택교육청코드,
    선택학교코드,
    조회날짜
)


# =========================================================
# API 연결 오류
# =========================================================

if 상태 == "연결오류":

    st.error(
        "NEIS 급식 정보에 연결하지 못했습니다."
    )

    st.stop()


# =========================================================
# API 응답 오류
# =========================================================

if 상태 == "응답오류":

    st.error(
        "NEIS 급식 정보의 응답을 읽지 못했습니다."
    )

    st.stop()


# =========================================================
# 급식이 없는 경우
# =========================================================

if 상태 == "급식없음":

    st.info(
        f"📭 {선택날짜.strftime('%Y년 %m월 %d일')}에는 "
        f"**{선택학교이름}**의 중식 급식이 없습니다."
    )

    st.stop()


# =========================================================
# 급식 데이터 표시
# =========================================================

오늘급식 = 급식표.iloc[0]


전체메뉴 = str(
    오늘급식.get(
        "DDISH_NM",
        ""
    )
)


메뉴목록 = 메뉴_분리(
    전체메뉴
)


칼로리 = 칼로리_추출(
    오늘급식.get(
        "CAL_INFO",
        ""
    )
)


# =========================================================
# 급식 기본 정보
# =========================================================

st.divider()

st.header(
    f"🍽️ {선택학교이름} 오늘의 중식"
)

st.caption(
    f"{선택지역} · "
    f"{선택날짜.strftime('%Y년 %m월 %d일')}"
)


# =========================================================
# 숫자 카드
# =========================================================

메뉴카드, 칼로리카드 = st.columns(
    2
)


with 메뉴카드:

    st.metric(
        "🍚 메뉴 가짓수",
        f"{len(메뉴목록)}개"
    )


with 칼로리카드:

    if 칼로리 is not None:

        st.metric(
            "🔥 총 칼로리",
            f"{칼로리:,.1f} kcal"
        )

    else:

        st.metric(
            "🔥 총 칼로리",
            "정보 없음"
        )


# =========================================================
# 메뉴
# =========================================================

st.divider()

st.subheader(
    "🍚 급식 메뉴"
)


if 메뉴목록:

    한줄_메뉴수 = 3


    for 시작 in range(
        0,
        len(메뉴목록),
        한줄_메뉴수
    ):

        현재메뉴 = 메뉴목록[
            시작:
            시작 + 한줄_메뉴수
        ]


        열 = st.columns(
            한줄_메뉴수
        )


        for 번호, 메뉴 in enumerate(
            현재메뉴
        ):

            실제번호 = (
                시작
                + 번호
                + 1
            )


            with 열[번호]:

                with st.container(
                    border=True
                ):

                    st.caption(
                        f"MENU {실제번호}"
                    )

                    st.write(
                        메뉴
                    )


else:

    st.info(
        "메뉴 정보가 없습니다."
    )


# =========================================================
# 칼로리
# =========================================================

st.divider()

st.subheader(
    "🔥 칼로리 정보"
)


if 칼로리 is not None:

    st.write(
        f"선택한 급식의 총 열량은 "
        f"**{칼로리:,.1f} kcal**입니다."
    )

else:

    st.write(
        "해당 날짜에는 칼로리 정보가 없습니다."
    )


# =========================================================
# 알레르기 번호 안내
# =========================================================

st.divider()

st.subheader(
    "⚠️ 알레르기 정보"
)

st.write(
    "메뉴에 표시된 괄호 안 숫자는 "
    "NEIS에서 제공하는 알레르기 유발 식품 번호입니다."
)


# =========================================================
# NEIS 원본 데이터
# =========================================================

with st.expander(
    "🔎 NEIS 원본 데이터 보기"
):

    st.json(
        오늘급식.to_dict()
    )


# =========================================================
# 출처
# =========================================================

st.divider()

st.caption(
    "자료 출처: 나이스 교육정보 개방 포털 "
    "학교기본정보 API · 급식식단정보 API"
)
