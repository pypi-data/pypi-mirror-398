from mcp.server.fastmcp import FastMCP

# [중요] 같은 폴더(.)에 있는 파일들에서 함수를 가져옵니다.
from .search import search_apt_final, get_recent_trades, get_apt_detail_info
from .utils import (
    format_recent_trades,
    format_apt_detail,
    format_apt_search_results,
    normalize_to_standard,
)

# 서버 생성
mcp = FastMCP(name="apt_info_mcp")


@mcp.tool(description="아파트 이름 및 코드 검색 도구")
def search_apartment_tool(query: str) -> str:
    """
    **사용자가 아파트 거래가격이나 정보를 물어볼 때 반드시 가장 먼저 사용하세요.**
    결과로 아파트 이름 목록과 고유 코드(aptSeq)를 반환합니다.
    Args:
        query: 아파트 이름 검색어 (예: "창동 주공 19")
    Returns:
        검색된 아파트와 고유 코드(aptSeq) 목록
    """
    standardized_query = normalize_to_standard(query)
    return format_apt_search_results(search_apt_final(standardized_query))


@mcp.tool(description="아파트 최근 거래가격 조회 도구")
def get_apt_price_tool(apt_seq: str, limit: int = 5) -> str:
    """
    아파트 코드(aptSeq)를 입력받아, 최근 {limit}개의 거래내역 목록을 반환합니다.
    기본값은 최근 5개입니다. search_apartment_tool 함수로 aptSeq를 얻은 후 사용하세요.
    Args:
        apt_seq: 아파트 고유 코드(aptSeq)
        limit: 최근 거래 개수 (기본값: 5)
    Returns:
        최근 {limit}개의 거래내역 목록
    """
    return format_recent_trades(get_recent_trades(apt_seq, limit))


@mcp.tool(description="아파트 상세 정보 조회 도구")
def get_apt_info_tool(apt_seq: str) -> str:
    """
    아파트 코드(aptSeq)를 입력받아, 세대수, 사용승인일(연식), 복도유형(계단식 등) 정보를 반환합니다.
    search_apartment_tool 함수로 aptSeq를 얻은 후 사용하세요.
    Args:
        apt_seq: 아파트 고유 코드(aptSeq)
    Returns:
        세대수, 사용승인일, 복도유형 정보
    """
    return format_apt_detail(get_apt_detail_info(apt_seq))


# 진입점 함수 (pyproject.toml에서 여기를 가리킴)
def main():
    mcp.run()


if __name__ == "__main__":
    main()
