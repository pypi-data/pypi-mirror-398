"""
해외 주식 마스터 파일 파서

해외 거래소(나스닥, 뉴욕, 홍콩 등) 종목 마스터 파일(.cod)을 파싱합니다.
"""
import pandas as pd

# 지원 시장 코드 (11개)
OVERSEAS_MARKETS = {
    "nas": "나스닥",
    "nys": "뉴욕",
    "ams": "아멕스",
    "shs": "상해",
    "shi": "상해지수",
    "szs": "심천",
    "szi": "심천지수",
    "tse": "도쿄",
    "hks": "홍콩",
    "hnx": "하노이",
    "hsx": "호치민",
}

# 컬럼명 정의 (24개)
OVERSEAS_COLUMNS = [
    "국가코드",
    "거래소ID",
    "거래소코드",
    "거래소명",
    "심볼",
    "실시간심볼",
    "한글명",
    "영문명",
    "보안유형",
    "통화",
    "소수점",
    "상장주수",
    "매수호가수량",
    "매도호가수량",
    "시장개장시간",
    "시장폐장시간",
    "업종코드",
    "업종대",
    "업종중",
    "업종소",
    "지수구성여부",
    "거래정지",
    "틱사이즈유형",
    "ETP구분코드",
]


def parse_overseas_stock_master(base_dir: str, market_code: str) -> pd.DataFrame:
    """해외 주식 마스터 파일 파싱

    Args:
        base_dir: 마스터 파일이 있는 디렉토리
        market_code: 시장 코드 (nas, nys, ams, shs, shi, szs, szi, tse, hks, hnx, hsx)

    Returns:
        pd.DataFrame: 종목 정보가 담긴 DataFrame
    """
    from pathlib import Path

    base_path = Path(base_dir)
    file_name = f"{market_code}mst.cod"

    # 대소문자 구분 없이 파일 찾기 (Linux는 대소문자 구분, ZIP 내부는 대문자)
    file_path = None
    for f in base_path.iterdir():
        if f.name.lower() == file_name.lower():
            file_path = f
            break

    if file_path is None:
        raise FileNotFoundError(f"마스터 파일을 찾을 수 없습니다: {file_name}")

    df = pd.read_table(
        file_path,
        sep="\t",
        encoding="cp949",
        header=None,
        names=OVERSEAS_COLUMNS,
        dtype=str,
    )

    return df
