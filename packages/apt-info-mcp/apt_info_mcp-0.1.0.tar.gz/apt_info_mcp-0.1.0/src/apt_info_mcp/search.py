# search.py: 검색 로직 담당
import re
from .db import get_supabase
from .utils import normalize_to_standard

# ========================================================
# [핵심] 여기서 딱 한 번 초기화합니다 (전역 변수)
# ========================================================
# 이 파일이 import될 때 최초 1회 실행되어, supabase 변수에 클라이언트가 저장됩니다.
supabase = get_supabase()


# --------------------------------------------------------
# 실제 함수들
# --------------------------------------------------------
def search_apt_final(user_query: str):

    # ---------------------------------------------------------
    # 1. 전처리 (표준화 -> 불용어 제거)
    # ---------------------------------------------------------
    # [변경점] 먼저 표준화 함수를 통과시킵니다.
    # 이제 "Sky View"는 "스카이뷰"(공백없음)가 되어 나옵니다.
    standard_query = normalize_to_standard(user_query)

    search_keywords = []

    # ---------------------------------------------------------
    # [핵심 로직 변경]
    # 토큰을 리스트로 만들고 하나씩 깎아 나갑니다.
    # ---------------------------------------------------------
    token = standard_query

    # [Step 1] "건물 형태"는 위치 불문하고 무조건 삭제 (가장 먼저!)
    # 이유: "아파트"가 중간에 있으면 뒤에 있는 "3단지" 처리를 방해함
    # 예: "느티마을[아파트]3단지" -> "느티마을3단지"
    global_remove_keywords = ["아파트", "오피스텔", "빌라", "주상복합"]
    for word in global_remove_keywords:
        token = token.replace(word, "")

    # [Step 2] "숫자+단지/차" 패턴 처리 (정규식 활용)
    # 이유: "3단지"에서 "단지"만 떼고 "3"은 남겨야 함
    # 예: "인창주공2단지" -> "인창주공2"
    # 예: "성산시영1차" -> "성산시영1"
    token = re.sub(r"(\d+)(단지|차)", r"\1", token)

    # [Step 3] 끝에서부터 꼬리표(Suffix) 반복 제거 (양파 껍질 벗기기)
    # 이제 "아파트"가 사라졌으니, 끝에 남은 "마을", "지구" 등을 처리
    suffixes = [
        "마을",
        "단지",
        "지구",
        "차",
    ]  # '차'는 위에서 숫자가 없을 경우를 대비해 둠

    while True:
        has_changed = False
        for suffix in suffixes:
            if token.endswith(suffix) and len(token) > len(suffix):
                token = token[: -len(suffix)]  # 끝부분 잘라내기
                has_changed = True

        if not has_changed:
            break

    # 최종적으로 정리된 토큰 추가
    search_keywords.append(token)

    if not search_keywords:
        return []

    print(f"검색 키워드(표준화됨): {search_keywords}")

    # ---------------------------------------------------------
    # 2. 1단계: AND 검색 (표준화된 컬럼 searchTextStandard 사용)
    # ---------------------------------------------------------
    # [변경점] 이제 searchTextNoSpace 대신 'searchTextStandard'를 봅니다.
    # DB도 위 규칙대로 변환되어 저장되어 있기 때문입니다.

    query = supabase.table("apt_search_list").select("*")

    for k in search_keywords:
        query = query.ilike("searchTextStandard", f"%{k}%")

    results = query.limit(15).execute().data

    # ---------------------------------------------------------
    # 3. 2단계: 결과 0건일 때 -> "유전자 검색(Scatter Match)" 발동!
    # ---------------------------------------------------------
    if not results:
        # 모든 키워드를 합쳐서 하나의 패턴으로 만듭니다. (이미 합쳐져 있지만 안전장치)
        joined_keyword = "".join(search_keywords)

        # 글자 사이사이에 %를 넣습니다.
        scatter_pattern = "%".join(list(joined_keyword))
        final_pattern = f"%{scatter_pattern}%"

        print(f"[!] 1단계 실패. 패턴 검색 시도: '{final_pattern}'")

        # 여기도 searchTextStandard 컬럼을 사용합니다.
        results = (
            supabase.table("apt_search_list")
            .select("*")
            .ilike("searchTextStandard", final_pattern)
            .limit(10)
            .execute()
            .data
        )

    return results


def get_recent_trades(apt_seq: str, limit: int = 5):
    """
    특정 단지(aptSeq)의 최근 실거래가를 가져옵니다.
    """
    try:
        response = (
            supabase.table("apt_trades")
            .select("dealDate, dealAmount, floor, excluUseAr")
            .eq("aptSeq", apt_seq)
            .order("dealDate", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"에러 발생: {e}")
        return []


def get_apt_detail_info(apt_seq: str):
    """
    특정 단지(aptSeq)에 연결된 기본 정보들을 조회합니다.
    합산 로직 없이, 매핑된 모든 K-apt 정보를 리스트로 반환합니다.

    필드: 세대수(kaptdaCnt), 복도유형(codeHallNm), 사용승인일(kaptUsedate)
    """

    # Supabase의 Nested Select 문법을 사용하여 조인된 데이터를 가져옵니다.
    # apt_mapping 테이블을 조회하면서, 연결된 apt_info_basic 테이블의 컬럼들을 {} 안에 명시합니다.
    response = (
        supabase.table("apt_code_mapping")
        .select(
            """
            kaptCode,
            apt_info_basic (
                kaptName,
                kaptdaCnt,
                codeHallNm,
                kaptUsedate
            )
        """
        )
        .eq("aptSeq", apt_seq)
        .execute()
    )

    data = response.data

    if not data:
        return []

    # 결과를 깔끔한 딕셔너리 리스트로 변환
    details_list = []

    for item in data:
        # 외래키로 연결된 apt_info_basic 데이터가 존재하는지 확인
        basic_info = item.get("apt_info_basic")

        if basic_info:
            details_list.append(
                {
                    "kaptCode": item["kaptCode"],  # 관리 코드
                    "name": basic_info.get("kaptName"),  # 아파트 이름
                    "households": basic_info.get("kaptdaCnt"),  # 세대수
                    "hallType": basic_info.get(
                        "codeHallNm"
                    ),  # 복도유형 (계단식/복도식 등)
                    "useDate": basic_info.get("kaptUsedate"),  # 사용승인일 (YYYYMMDD)
                }
            )

    return details_list
