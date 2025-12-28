# utils.py: 포맷팅 등


def normalize_to_standard(text: str) -> str:
    """
    사용자 검색어를 DB의 searchTextStandard 포맷으로 변환합니다.
    """
    # 1. 기본 전처리: 대문자 변환 + 모든 공백 제거
    # 예: "Sky View" -> "SKYVIEW"
    standardized = text.upper().replace(" ", "")

    # 2. 치환 규칙 정의 (제공해주신 리스트 그대로)
    replacements = [
        ("에스케이", "SK"),
        ("엘지", "LG"),
        ("지에스", "GS"),
        ("SKVIEW", "SK뷰"),
        ("에스-클래스", "S클래스"),
        ("에스클래스", "S클래스"),
        ("S-클래스", "S클래스"),
        ("S-CLASS", "S클래스"),
        ("이편한", "e편한"),
        ("이-편한", "e편한"),
        ("e-편한", "e편한"),
        ("FIRSTVIEW", "퍼스트뷰"),
        ("THEFIRST", "더퍼스트"),
        ("THE#", "더샵"),
        ("THESHARP", "더샵"),
        ("SummitPlace", "써밋플레이스"),
        ("U.BORA", "유보라"),
        ("디엠씨", "DMC"),
        ("I-PARK", "아이파크"),
        ("IPARK", "아이파크"),
        ("SKY VIEW", "스카이뷰"),
        ("SkyView", "스카이뷰"),
        ("I-Class", "아이클래스"),
        ("We’vePark", "위브파크"),
        ("케이씨씨", "KCC"),
    ]

    for old, new in replacements:
        # 중요: 리스트에 있는 키값('old')도
        # 현재 텍스트 상태(대문자+공백제거)에 맞춰서 변환 후 비교해야 함
        old_key = old.upper().replace(" ", "")

        standardized = standardized.replace(old_key, new)

    return standardized


def format_apt_search_results(results: list):
    if results:
        lines = []
        lines.append(f"--- 검색 결과 (총 {len(results)}건) ---")
        for info in results:
            lines.append(
                f"- 코드(aptSeq): {info['aptSeq']} | 아파트: {info['searchText']}"
            )
        lines.append("-" * 20)
        return "\n".join(lines)
    else:
        return "검색 결과가 없습니다. 검색어를 확인하시거나, 더 단순화된 이름을 사용해보세요. 동이나 도시 이름을 결합해도 좋습니다.\n예시: '주공아파트 19단지' -> '창동 주공19'"


def format_apt_detail(results: list):
    if results:
        print(f"--- 조회 결과 (총 {len(results)}건) ---")
        for info in results:
            # 1. 날짜 데이터 가져오기 (None일 경우 대비)
            raw_date = info.get("useDate")

            # 2. 포맷 변경 로직 (데이터가 있고, 8자리 'YYYYMMDD' 형식일 때만)
            if raw_date and len(raw_date) == 8:
                # 예: "20020125" -> "2002" + "-" + "01" + "-" + "25"
                formatted_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
            else:
                # 데이터가 없거나 형식이 이상하면 원본 그대로 출력
                formatted_date = raw_date

            lines = []
            lines.append(f"[{info['name']}]")
            # lines.append(f" - 코드: {info['kaptCode']}")
            lines.append(f" - 세대수: {info['households']}세대")
            lines.append(f" - 복도유형: {info['hallType']}")
            lines.append(f" - 사용승인일: {formatted_date}")  # 수정된 변수 사용
            lines.append("-" * 20)

            return "\n".join(lines)
    else:
        return "연결된 상세 정보가 없습니다."


def format_recent_trades(trade_list: list) -> str:
    """
    DB의 Raw JSON 리스트를 LLM이 읽기 편한 Markdown 리스트 문자열로 변환합니다.
    """
    if not trade_list:
        return "최근 거래 내역이 없습니다."

    formatted_lines = []
    formatted_lines.append(f"총 {len(trade_list)}건의 최근 거래 내역입니다 (최신순):")

    for t in trade_list:
        # 1. 날짜 포맷팅 (2025-12-13)
        date = t.get("dealDate", "날짜미상")

        # 2. 가격 변환 ('72,500' -> 7억 2,500만원)
        try:
            raw_amount = int(t["dealAmount"].replace(",", ""))  # 콤마 제거
            uk = raw_amount // 10000  # 억 단위
            man = raw_amount % 10000  # 만 단위

            price_str = ""
            if uk > 0:
                price_str += f"{uk}억 "
            if man > 0:
                price_str += f"{format(man, ',')}만원"
        except:
            price_str = t["dealAmount"]  # 에러나면 원본 사용

        # 3. 면적. 나중에 평수 변환 추가?
        try:
            area_m2 = float(t["excluUseAr"])
            rounded_area = round(area_m2, 1)
            area_str = f"전용 {rounded_area}㎡"
        except:
            area_str = f"전용 {t['excluUseAr']}㎡"

        # 4. 층수
        floor = f"{t['floor']}층"

        # "- 2025-12-13 | 전용 59.0㎡ | 7억 2,500만원 (4층)"
        line = f"- {date} | {area_str} | **{price_str}** ({floor})"
        formatted_lines.append(line)

    return "\n".join(formatted_lines)
