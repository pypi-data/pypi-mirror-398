"""
한국투자증권 API 상수 정의

API 쿼리 파라미터에서 사용하는 코드 값들을 정의합니다.
변수명은 실제 API 파라미터명을 사용합니다.
"""

# =============================================================================
# 국가 코드 (COUNTRY_CODE)
# =============================================================================

COUNTRY_CODE = {
    "KR": "KR",   # 한국
    "US": "US",   # 미국
    "CN": "CN",   # 중국
    "JP": "JP",   # 일본
}

# =============================================================================
# 조건 시장 분류 코드 (FID_COND_MRKT_DIV_CODE)
# =============================================================================

# 국내주식 시장 분류 코드
FID_COND_MRKT_DIV_CODE_STOCK = {
    "KRX": "J",       # 한국거래소
    "NXT": "NX",      # 넥스트레이드
    "UNIFIED": "UN",  # 통합
    "ELW": "W",       # ELW
}

# 채권 시장 분류 코드
FID_COND_MRKT_DIV_CODE_BOND = {
    "EXCHANGE": "B",  # 장내채권
}

# 선물옵션 시장 분류 코드
FID_COND_MRKT_DIV_CODE_FUTURES = {
    "INDEX_FUTURES": "F",   # 지수선물
    "INDEX_OPTIONS": "O",   # 지수옵션
    "STOCK_FUTURES": "JF",  # 주식선물
    "STOCK_OPTIONS": "JO",  # 주식옵션
    "COMMODITY": "CF",      # 상품선물(금), 금리선물(국채), 통화선물(달러)
    "NIGHT_FUTURES": "CM",  # 야간선물
    "NIGHT_OPTIONS": "EU",  # 야간옵션
}

# 해외지수/환율 시장 분류 코드
FID_COND_MRKT_DIV_CODE_OVERSEAS = {
    "FOREIGN_INDEX": "N",   # 해외지수
    "EXCHANGE_RATE": "X",   # 환율
    "KRW_RATE": "KX",       # 원화환율
    "BOND": "I",            # 국채
    "GOLD_FUTURES": "S",    # 금선물
}

# =============================================================================
# 국내 거래소ID 구분코드 (EXCG_ID_DVSN_CD) - 주문용
# =============================================================================

EXCG_ID_DVSN_CD = {
    "KRX": "KRX",   # 한국거래소 (기본값)
    "NXT": "NXT",   # 넥스트레이드
    "SOR": "SOR",   # Smart Order Routing
}

# =============================================================================
# 해외주식 거래소 코드 - 시세 조회용 (EXCD)
# =============================================================================

EXCD = {
    # 미국 (정규장)
    "NYS": "NYS",   # NYSE
    "NAS": "NAS",   # NASDAQ
    "AMS": "AMS",   # AMEX
    # 미국 (주간거래)
    "BAY": "BAY",   # NYSE 주간거래
    "BAQ": "BAQ",   # NASDAQ 주간거래
    "BAA": "BAA",   # AMEX 주간거래
    # 아시아
    "HKS": "HKS",   # 홍콩
    "TSE": "TSE",   # 도쿄
    "SHS": "SHS",   # 상하이
    "SZS": "SZS",   # 심천
    "SHI": "SHI",   # 상하이 지수
    "SZI": "SZI",   # 심천 지수
    "HSX": "HSX",   # 호치민
    "HNX": "HNX",   # 하노이
}

# 국가별 거래소 코드 매핑 (시세 조회용)
EXCD_BY_COUNTRY = {
    "US": ["NYS", "NAS", "AMS", "BAY", "BAQ", "BAA"],  # 미국 (정규장 + 주간거래)
    "HK": ["HKS"],                                      # 홍콩
    "JP": ["TSE"],                                      # 일본
    "CN": ["SHS", "SZS"],                               # 중국 (상하이, 심천)
    "VN": ["HSX", "HNX"],                               # 베트남 (호치민, 하노이)
}

# =============================================================================
# 해외주식 거래소 코드 - 주문/잔고용 (OVRS_EXCG_CD)
# =============================================================================

OVRS_EXCG_CD = {
    # 미국
    "NASD": "NASD",   # 나스닥
    "NYSE": "NYSE",   # 뉴욕
    "AMEX": "AMEX",   # 아멕스
    # 아시아
    "SEHK": "SEHK",   # 홍콩
    "TKSE": "TKSE",   # 도쿄
    "SHAA": "SHAA",   # 상하이
    "SZAA": "SZAA",   # 심천
    "HASE": "HASE",   # 하노이
    "VNSE": "VNSE",   # 호치민
}

# =============================================================================
# 상품유형 코드 (PRDT_TYPE_CD)
# =============================================================================

PRDT_TYPE_CD = {
    # 국내
    "KR_STOCK": "300",       # 주식
    "KR_FUTURES": "301",     # 선물옵션
    "KR_BOND": "302",        # 채권
    # 미국
    "US_NASDAQ": "512",
    "US_NYSE": "513",
    "US_AMEX": "529",
    # 홍콩
    "HK": "501",
    "HK_CNY": "543",
    "HK_USD": "558",
    # 일본
    "JP": "515",
    # 중국
    "CN_SHANGHAI": "551",
    "CN_SHENZHEN": "552",
    # 베트남
    "VN_HANOI": "507",
    "VN_HOCHIMINH": "508",
}

# =============================================================================
# 국가별 상품유형 코드 매핑 (PRDT_TYPE_CD_BY_COUNTRY)
# =============================================================================

PRDT_TYPE_CD_BY_COUNTRY = {
    "KR": [PRDT_TYPE_CD["KR_STOCK"]],
    "KRX": [PRDT_TYPE_CD["KR_STOCK"]],
    "US": [PRDT_TYPE_CD["US_NASDAQ"], PRDT_TYPE_CD["US_NYSE"], PRDT_TYPE_CD["US_AMEX"]],
    "JP": [PRDT_TYPE_CD["JP"]],
    "HK": [PRDT_TYPE_CD["HK"], PRDT_TYPE_CD["HK_CNY"], PRDT_TYPE_CD["HK_USD"]],
    "CN": [PRDT_TYPE_CD["CN_SHANGHAI"], PRDT_TYPE_CD["CN_SHENZHEN"]],
    "VN": [PRDT_TYPE_CD["VN_HANOI"], PRDT_TYPE_CD["VN_HOCHIMINH"]],
}

# =============================================================================
# API 리턴 코드 (API_RETURN_CODE)
# =============================================================================

API_RETURN_CODE = {
    "SUCCESS": "0",  # 조회되었습니다
    "EXPIRED_TOKEN": "1",  # 기간이 만료된 token 입니다
    "NO_DATA": "7",  # 조회할 자료가 없습니다
    "RATE_LIMIT_EXCEEDED": "EGW00201",  # Rate limit 초과
}

# =============================================================================
# 시장별 투자자동향 - 시장 코드 (MARKET_INVESTOR_TREND_CODE)
# =============================================================================

MARKET_INVESTOR_TREND_CODE = {
    "KOSPI": "KSP",         # 코스피
    "KOSDAQ": "KSQ",        # 코스닥
    "ETF": "ETF",           # ETF
    "ELW": "ELW",           # ELW
    "ETN": "ETN",           # ETN
    "FUTURES": "K2I",       # 선물/콜옵션/풋옵션
    "STOCK_FUTURES": "999", # 주식선물
    "MINI": "MKI",          # 미니
    "WEEKLY_MONTH": "WKM",  # 위클리(월)
    "WEEKLY_THUR": "WKI",   # 위클리(목)
    "KOSDAQ150": "KQI",     # 코스닥150
}

# =============================================================================
# 시장별 투자자동향 - 업종 코드 (SECTOR_CODE)
# =============================================================================

SECTOR_CODE = {
    "KOSPI_TOTAL": "0001",   # 코스피 종합
    "KOSDAQ_TOTAL": "1001",  # 코스닥 종합
    "FUTURES": "F001",       # 선물
    "CALL_OPTION": "OC01",   # 콜옵션
    "PUT_OPTION": "OP01",    # 풋옵션
    "ETF_TOTAL": "T000",     # ETF 전체
    "ELW_TOTAL": "W000",     # ELW 전체
    "ETN_TOTAL": "E199",     # ETN 전체
}
