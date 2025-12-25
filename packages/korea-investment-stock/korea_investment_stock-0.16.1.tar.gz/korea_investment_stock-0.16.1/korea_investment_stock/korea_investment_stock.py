'''
한국투자증권 python wrapper
'''
import os
import zipfile
import logging
import re
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

import pandas as pd
import requests

from .token import TokenStorage, TokenManager, create_token_storage
from .constants import (
    PRDT_TYPE_CD_BY_COUNTRY,
    API_RETURN_CODE,
    FID_COND_MRKT_DIV_CODE_STOCK,
    EXCD_BY_COUNTRY,
)
from .config_resolver import ConfigResolver
from .parsers import (
    parse_kospi_master,
    parse_kosdaq_master,
    parse_overseas_stock_master,
    OVERSEAS_MARKETS,
)
from .ipo import validate_date_format, validate_date_range

# 로거 설정
logger = logging.getLogger(__name__)


class KoreaInvestment:
    '''
    한국투자증권 REST API
    '''

    # 기본 캐시 TTL (시간) - 1주일
    DEFAULT_MASTER_TTL_HOURS = 168

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        acc_no: str | None = None,
        config: "Config | None" = None,
        config_file: "str | Path | None" = None,
        token_storage: Optional[TokenStorage] = None
    ):
        """한국투자증권 API 클라이언트 초기화

        설정 우선순위 (5단계):
            1. 생성자 파라미터 (최고 우선순위)
            2. config 객체
            3. config_file 파라미터
            4. 환경 변수 (KOREA_INVESTMENT_*)
            5. 기본 config 파일 (~/.config/kis/config.yaml)

        Args:
            api_key (str | None): 발급받은 API key
            api_secret (str | None): 발급받은 API secret
            acc_no (str | None): 계좌번호 체계의 앞 8자리-뒤 2자리 (예: "12345678-01")
            config (Config | None): Config 객체 (Phase 2에서 추가됨)
            config_file (str | Path | None): 설정 파일 경로
            token_storage (Optional[TokenStorage]): 토큰 저장소 인스턴스

        Raises:
            ValueError: api_key, api_secret, 또는 acc_no가 설정되지 않았을 때
            ValueError: acc_no 형식이 올바르지 않을 때

        Examples:
            # 방법 1: 생성자 파라미터 (기존 방식)
            >>> broker = KoreaInvestment(
            ...     api_key="your-api-key",
            ...     api_secret="your-api-secret",
            ...     acc_no="12345678-01"
            ... )

            # 방법 2: 환경 변수 자동 감지
            >>> broker = KoreaInvestment()

            # 방법 3: Config 객체 사용
            >>> config = Config.from_yaml("~/.config/kis/config.yaml")
            >>> broker = KoreaInvestment(config=config)

            # 방법 4: config_file 파라미터
            >>> broker = KoreaInvestment(config_file="./my_config.yaml")

            # 방법 5: 혼합 사용 (일부만 override)
            >>> broker = KoreaInvestment(config=config, api_key="override-key")
        """
        # 5단계 우선순위로 설정 해결 (ConfigResolver 사용)
        resolver = ConfigResolver()
        resolved = resolver.resolve(
            api_key=api_key,
            api_secret=api_secret,
            acc_no=acc_no,
            config=config,
            config_file=config_file,
        )

        self.api_key = resolved["api_key"]
        self.api_secret = resolved["api_secret"]
        acc_no = resolved["acc_no"]

        # 필수값 검증
        missing_fields = []
        if not self.api_key:
            missing_fields.append("api_key (KOREA_INVESTMENT_API_KEY)")
        if not self.api_secret:
            missing_fields.append("api_secret (KOREA_INVESTMENT_API_SECRET)")
        if not acc_no:
            missing_fields.append("acc_no (KOREA_INVESTMENT_ACCOUNT_NO)")

        if missing_fields:
            raise ValueError(
                "API credentials required. Missing: " + ", ".join(missing_fields) + ". "
                "Pass as parameters, use config/config_file, or set KOREA_INVESTMENT_* environment variables."
            )

        # 계좌번호 형식 검증
        if '-' not in acc_no:
            raise ValueError(f"계좌번호 형식이 올바르지 않습니다. '12345678-01' 형식이어야 합니다. 입력값: {acc_no}")

        self.base_url = "https://openapi.koreainvestment.com:9443"

        # account number - 검증 후 split
        parts = acc_no.split('-')
        if len(parts) != 2 or len(parts[0]) != 8 or len(parts[1]) != 2:
            raise ValueError(f"계좌번호 형식이 올바르지 않습니다. 앞 8자리-뒤 2자리여야 합니다. 입력값: {acc_no}")

        self.acc_no = acc_no
        self.acc_no_prefix = parts[0]
        self.acc_no_postfix = parts[1]

        # resolved에서 token_storage 관련 설정 가져오기
        self._resolved_config = resolved

        # 토큰 저장소 생성 (factory 사용)
        storage = token_storage or create_token_storage(self._resolved_config)

        # TokenManager 초기화
        self._token_manager = TokenManager(
            storage=storage,
            base_url=self.base_url,
            api_key=self.api_key,
            api_secret=self.api_secret
        )

        # 하위 호환성을 위해 token_storage 속성 유지
        self.token_storage = storage

        # 유효한 토큰 확보 (TokenManager 사용)
        self.access_token = self._token_manager.get_valid_token()

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료 - 리소스 정리"""
        self.shutdown()
        return False  # 예외를 전파

    def shutdown(self):
        """리소스 정리"""
        # 컨텍스트 매니저 종료 시 호출됨
        # 향후 필요한 정리 작업이 있으면 여기에 추가
        pass


    def issue_access_token(self, force: bool = False):
        """OAuth인증/접근토큰발급 (TokenManager로 위임)

        Args:
            force: True면 저장소 상태와 무관하게 강제 재발급
        """
        if force:
            self._token_manager._issue_token()
            self.access_token = self._token_manager.access_token
        else:
            self.access_token = self._token_manager.get_valid_token()

    def _is_token_expired_response(self, resp_json: dict) -> bool:
        """API 응답에서 토큰 만료 여부 확인

        Note:
            공식 API 문서에는 토큰 만료 에러 메시지가 명시되어 있지 않음.
            실제 운영 환경에서 관측된 메시지: "기간이 만료된 token 입니다."
            다양한 만료 관련 메시지를 포괄하기 위해 "만료"와 "token" 키워드로 감지

        Args:
            resp_json: API 응답 JSON

        Returns:
            bool: 토큰 만료 에러이면 True
        """
        if resp_json.get('rt_cd') != '0':
            msg = resp_json.get('msg1', '')
            # "만료"와 "token"이 모두 포함된 경우 토큰 만료로 판단
            return '만료' in msg and 'token' in msg.lower()
        return False

    def _request_with_token_refresh(
        self,
        method: str,
        url: str,
        headers: dict,
        params: dict = None,
        max_retries: int = 1
    ) -> dict:
        """토큰 만료 시 자동 재발급 후 재시도하는 요청 래퍼

        Args:
            method: HTTP 메서드 ("GET" 또는 "POST")
            url: API URL
            headers: 요청 헤더 (authorization 포함)
            params: 쿼리 파라미터 또는 POST 바디
            max_retries: 토큰 재발급 후 재시도 횟수 (기본 1회)

        Returns:
            dict: API 응답 JSON
        """
        for attempt in range(max_retries + 1):
            if method == "GET":
                resp = requests.get(url, headers=headers, params=params)
            else:
                resp = requests.post(url, headers=headers, json=params)

            resp_json = resp.json()

            # 토큰 만료 에러 감지 및 재발급
            if self._is_token_expired_response(resp_json) and attempt < max_retries:
                logger.info("토큰 만료 감지, 재발급 시도...")
                self.issue_access_token(force=True)
                headers["authorization"] = self.access_token
                continue

            return resp_json

        return resp_json

    def check_access_token(self) -> bool:
        """토큰 유효성 확인 (TokenManager로 위임)

        Returns:
            bool: True: 토큰이 유효함, False: 토큰이 유효하지 않음
        """
        return self._token_manager.is_token_valid()

    def load_access_token(self):
        """토큰 로드 (TokenManager로 위임)"""
        self.access_token = self._token_manager.get_valid_token()

    def issue_hashkey(self, data: dict) -> str:
        """해쉬키 발급 (TokenManager로 위임)

        Args:
            data (dict): POST 요청 데이터

        Returns:
            str: 해쉬키 문자열
        """
        return self._token_manager.issue_hashkey(data)

    def fetch_price(self, symbol: str, country_code: str = "KR") -> dict:
        """국내주식시세/주식현재가 시세
           해외주식현재가/해외주식 현재체결가

        Args:
            symbol (str): 종목코드
            country_code (str): 국가 코드 ("KR", "US")

        Returns:
            dict: API 응답 데이터
        """

        if country_code == "KR":
            stock_info = self.fetch_stock_info(symbol, country_code)
            symbol_type = self.get_symbol_type(stock_info)
            resp_json = self.fetch_domestic_price(symbol, symbol_type)
        elif country_code == "US":
            # 기존: resp_json = self.fetch_oversea_price(symbol)  # 메서드 없음
            # 개선: 이미 구현된 fetch_price_detail_oversea() 활용
            resp_json = self.fetch_price_detail_oversea(symbol, country_code)
            # 참고: 이 API는 현재가 외에도 PER, PBR, EPS, BPS 등 추가 정보 제공
        else:
            raise ValueError("Unsupported country code")

        return resp_json

    def get_symbol_type(self, symbol_info):
        # API 오류 응답 처리
        if symbol_info.get('rt_cd') != '0' or 'output' not in symbol_info:
            return 'Stock'  # 기본값으로 주식 타입 반환

        symbol_type = symbol_info['output']['prdt_clsf_name']
        if symbol_type == '주권' or symbol_type == '상장REITS' or symbol_type == '사회간접자본투융자회사':
            return 'Stock'
        elif symbol_type == 'ETF':
            return 'ETF'

        return "Unknown"

    def fetch_domestic_price(
        self,
        symbol: str,
        symbol_type: str = "Stock"
    ) -> dict:
        """국내 주식/ETF 현재가시세

        Args:
            symbol: 종목코드 (ex: 005930)
            symbol_type: 상품 타입 ("Stock" 또는 "ETF")

        Returns:
            dict: API 응답 데이터
        """
        TR_ID_MAP = {
            "Stock": "FHKST01010100",
            "ETF": "FHPST02400000"
        }

        path = "uapi/domestic-stock/v1/quotations/inquire-price"
        url = f"{self.base_url}/{path}"
        headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "tr_id": TR_ID_MAP.get(symbol_type, "FHKST01010100")
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": FID_COND_MRKT_DIV_CODE_STOCK["KRX"],
            "FID_INPUT_ISCD": symbol
        }
        return self._request_with_token_refresh("GET", url, headers, params)

    def fetch_kospi_symbols(
        self,
        ttl_hours: int = 168,
        force_download: bool = False
    ) -> pd.DataFrame:
        """코스피 종목 코드

        실제 필요한 종목: ST, RT, EF, IF

        ST	주권
        MF	증권투자회사
        RT	부동산투자회사
        SC	선박투자회사
        IF	사회간접자본투융자회사
        DR	주식예탁증서
        EW	ELW
        EF	ETF
        SW	신주인수권증권
        SR	신주인수권증서
        BC	수익증권
        FE	해외ETF
        FS	외국주권

        Args:
            ttl_hours (int): 캐시 유효 시간 (기본 1주일 = 168시간)
            force_download (bool): 강제 다운로드 여부

        Returns:
            DataFrame: 코스피 종목 정보
        """
        base_dir = os.getcwd()
        file_name = "kospi_code.mst.zip"
        url = "https://new.real.download.dws.co.kr/common/master/" + file_name

        self.download_master_file(base_dir, file_name, url, ttl_hours, force_download)
        df = parse_kospi_master(base_dir)
        return df

    def fetch_kosdaq_symbols(
        self,
        ttl_hours: int = 168,
        force_download: bool = False
    ) -> pd.DataFrame:
        """코스닥 종목 코드

        Args:
            ttl_hours (int): 캐시 유효 시간 (기본 1주일 = 168시간)
            force_download (bool): 강제 다운로드 여부

        Returns:
            DataFrame: 코스닥 종목 정보
        """
        base_dir = os.getcwd()
        file_name = "kosdaq_code.mst.zip"
        url = "https://new.real.download.dws.co.kr/common/master/" + file_name

        self.download_master_file(base_dir, file_name, url, ttl_hours, force_download)
        df = parse_kosdaq_master(base_dir)
        return df

    def _should_download(
        self,
        file_path: Path,
        ttl_hours: int,
        force: bool
    ) -> bool:
        """다운로드 필요 여부 판단

        Args:
            file_path: ZIP 파일 경로
            ttl_hours: 캐시 유효 시간
            force: 강제 다운로드 여부

        Returns:
            bool: True=다운로드 필요, False=캐시 사용
        """
        if force:
            return True

        if not file_path.exists():
            return True

        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        age = datetime.now() - mtime

        if age.total_seconds() > ttl_hours * 3600:
            logger.debug(f"캐시 만료: {file_path} (age={age})")
            return True

        return False

    def download_master_file(
        self,
        base_dir: str,
        file_name: str,
        url: str,
        ttl_hours: int = 168,
        force_download: bool = False
    ) -> bool:
        """master 파일 다운로드 (캐싱 지원)

        Args:
            base_dir (str): 저장 디렉토리
            file_name (str): 파일명 (예: "kospi_code.mst.zip")
            url (str): 다운로드 URL
            ttl_hours (int): 캐시 유효 시간 (기본 1주일 = 168시간)
            force_download (bool): 강제 다운로드 여부

        Returns:
            bool: True=다운로드됨, False=캐시 사용
        """
        zip_path = Path(base_dir) / file_name

        # 다운로드 필요 여부 확인
        if not self._should_download(zip_path, ttl_hours, force_download):
            mtime = datetime.fromtimestamp(zip_path.stat().st_mtime)
            age_hours = (datetime.now() - mtime).total_seconds() / 3600
            logger.info(f"캐시 사용: {zip_path} (age: {age_hours:.1f}h, ttl: {ttl_hours}h)")
            return False

        # 다운로드
        logger.info(f"다운로드 중: {url} -> {zip_path}")
        resp = requests.get(url)
        resp.raise_for_status()

        with open(zip_path, "wb") as f:
            f.write(resp.content)

        # 압축 해제
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(base_dir)

        return True

    def fetch_price_detail_oversea(self, symbol: str, country_code: str = "US") -> dict:
        """해외주식 현재가상세

        해외주식 종목의 현재가, PER, PBR, EPS, BPS 등 상세 정보를 조회합니다.
        국가 코드에 따라 해당 국가의 거래소를 자동으로 탐색합니다.

        API 정보:
            - 경로: /uapi/overseas-price/v1/quotations/price-detail
            - TR ID: HHDFS76200200
            - 모의투자: 미지원

        Query Parameters:
            - AUTH (str): 사용자권한정보 (빈 문자열)
            - EXCD (str): 거래소코드
                - NYS: 뉴욕 (NYSE)
                - NAS: 나스닥 (NASDAQ)
                - AMS: 아멕스 (AMEX)
                - BAY: 뉴욕 주간거래
                - BAQ: 나스닥 주간거래
                - BAA: 아멕스 주간거래
                - HKS: 홍콩
                - TSE: 도쿄
                - SHS: 상하이
                - SZS: 심천
                - HSX: 호치민
                - HNX: 하노이
            - SYMB (str): 종목코드

        Args:
            symbol (str): 종목 코드 (예: AAPL, MSFT, TSLA)
            country_code (str): 국가 코드 (기본값: "US")
                - "US": 미국 (NYS → NAS → AMS → BAY → BAQ → BAA)
                - "HK": 홍콩 (HKS)
                - "JP": 일본 (TSE)
                - "CN": 중국 (SHS → SZS)
                - "VN": 베트남 (HSX → HNX)

        Returns:
            dict: API 응답. 주요 필드:
                - rt_cd (str): 성공/실패 ("0"=성공)
                - msg1 (str): 응답 메시지
                - output (dict): 응답 상세
                    - rsym (str): 실시간조회종목코드
                    - last (str): 현재가
                    - open (str): 시가
                    - high (str): 고가
                    - low (str): 저가
                    - base (str): 전일종가
                    - tvol (str): 거래량
                    - tamt (str): 거래대금
                    - tomv (str): 시가총액
                    - shar (str): 상장주수
                    - perx (str): PER
                    - pbrx (str): PBR
                    - epsx (str): EPS
                    - bpsx (str): BPS
                    - h52p (str): 52주최고가
                    - l52p (str): 52주최저가
                    - vnit (str): 매매단위
                    - e_hogau (str): 호가단위
                    - e_icod (str): 업종(섹터)
                    - curr (str): 통화

        Raises:
            ValueError: 지원하지 않는 country_code인 경우

        Note:
            - 지연시세: 미국 실시간무료(0분), 홍콩/베트남/중국/일본 15분 지연
            - 미국 주간거래 시간에도 동일한 API로 조회 가능
        """
        exchange_codes = EXCD_BY_COUNTRY.get(country_code)
        if not exchange_codes:
            raise ValueError(f"지원하지 않는 country_code: {country_code}")

        path = "/uapi/overseas-price/v1/quotations/price-detail"
        url = f"{self.base_url}/{path}"

        headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "tr_id": "HHDFS76200200"
        }

        for exchange_code in exchange_codes:
            logger.debug(f"exchange_code: {exchange_code}")
            params = {
                "AUTH": "",
                "EXCD": exchange_code,
                "SYMB": symbol
            }
            resp_json = self._request_with_token_refresh("GET", url, headers, params)
            if resp_json['rt_cd'] != API_RETURN_CODE["SUCCESS"] or resp_json['output']['rsym'] == '':
                continue

            return resp_json

        # 모든 거래소에서 실패한 경우
        raise ValueError(f"'{symbol}' 종목을 {country_code} 거래소에서 찾을 수 없습니다")

    def fetch_stock_info(self, symbol: str, country_code: str = "KR") -> dict:
        """상품기본조회 [v1_국내주식-029]

        국내/해외 주식의 기본 상품 정보를 조회합니다.
        국가 코드에 따라 해당 국가의 상품유형코드를 자동으로 탐색합니다.

        API 정보:
            - 경로: /uapi/domestic-stock/v1/quotations/search-info
            - Method: GET
            - 실전 TR ID: CTPF1604R
            - 모의투자: 미지원

        Query Parameters:
            PDNO (str): 상품번호
                - Required: Yes
                - Length: 12
                - 예) 000660 (하이닉스), AAPL (애플)

            PRDT_TYPE_CD (str): 상품유형코드
                - Required: Yes
                - Length: 3
                - 국내: 300 (주식), 301 (선물옵션), 302 (채권)
                - 미국: 512 (나스닥), 513 (뉴욕), 529 (아멕스)
                - 일본: 515
                - 홍콩: 501, 543 (CNY), 558 (USD)
                - 베트남: 507 (하노이), 508 (호치민)
                - 중국: 551 (상해A), 552 (심천A)

        Args:
            symbol (str): 종목 코드 (예: 005930, AAPL)
            country_code (str): 국가 코드 (기본값: "KR")
                - KR/KRX: 한국
                - US: 미국 (NASDAQ, NYSE, AMEX)
                - JP: 일본
                - HK: 홍콩
                - CN: 중국 (상해, 심천)
                - VN: 베트남 (하노이, 호치민)

        Returns:
            dict: API 응답 딕셔너리
                - rt_cd: 성공 실패 여부 ("0": 성공)
                - msg_cd: 응답코드
                - msg1: 응답메시지
                - output: 상품기본정보

        Raises:
            KeyError: 지원하지 않는 country_code인 경우

        Example:
            >>> broker.fetch_stock_info("005930", "KR")  # 삼성전자
            >>> broker.fetch_stock_info("AAPL", "US")    # 애플
        """
        path = "uapi/domestic-stock/v1/quotations/search-info"
        url = f"{self.base_url}/{path}"
        headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "tr_id": "CTPF1604R"
        }

        for prdt_type_cd in PRDT_TYPE_CD_BY_COUNTRY[country_code]:
            try:
                params = {
                    "PDNO": symbol,
                    "PRDT_TYPE_CD": prdt_type_cd
                }
                resp_json = self._request_with_token_refresh("GET", url, headers, params)

                if resp_json['rt_cd'] == API_RETURN_CODE['NO_DATA']:
                    continue
                return resp_json

            except Exception as e:
                logger.debug(f"fetch_stock_info 에러: {e}")
                if resp_json['rt_cd'] != API_RETURN_CODE['SUCCESS']:
                    continue
                raise e

    def fetch_search_stock_info(self, symbol: str, country_code: str = "KR") -> dict:
        """주식기본조회 [v1_국내주식-067]

        국내주식 종목의 상세 정보를 조회합니다.
        상장주수, 자본금, 액면가, 시장구분, 업종분류 등 상세 정보를 제공합니다.

        ⚠️ 주의: 이 API는 **국내주식만 지원**합니다.
        해외주식 정보는 fetch_stock_info() 또는 fetch_price_detail_oversea()를 사용하세요.

        API 정보:
            - 경로: /uapi/domestic-stock/v1/quotations/search-stock-info
            - Method: GET
            - 실전 TR ID: CTPF1002R
            - 모의투자: 미지원

        Query Parameters:
            PRDT_TYPE_CD (str): 상품유형코드
                - Required: Yes
                - Length: 3
                - 300: 주식, ETF, ETN, ELW
                - 301: 선물옵션
                - 302: 채권
                - 306: ELS

            PDNO (str): 상품번호
                - Required: Yes
                - Length: 12
                - 종목번호 6자리 (예: 005930)
                - ETN의 경우 Q로 시작 (예: Q500001)

        Args:
            symbol (str): 종목 코드 (예: 005930, 000660)
            country_code (str): 국가 코드 (기본값: "KR")
                - "KR"만 지원 (국내주식 전용 API)
                - 그 외 값은 ValueError 발생

        Returns:
            dict: API 응답 딕셔너리

        Raises:
            ValueError: country_code가 "KR"이 아닌 경우

        Example:
            >>> broker.fetch_search_stock_info("005930")        # 삼성전자
            >>> broker.fetch_search_stock_info("005930", "KR")  # 동일
        """
        if country_code != "KR":
            raise ValueError(f"fetch_search_stock_info는 국내주식 전용 API입니다. country_code='KR'만 지원합니다. (입력값: '{country_code}')")

        path = "uapi/domestic-stock/v1/quotations/search-stock-info"
        url = f"{self.base_url}/{path}"
        headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "tr_id": "CTPF1002R"
        }

        for prdt_type_cd in PRDT_TYPE_CD_BY_COUNTRY["KR"]:
            try:
                params = {
                    "PDNO": symbol,
                    "PRDT_TYPE_CD": prdt_type_cd
                }
                resp_json = self._request_with_token_refresh("GET", url, headers, params)

                if resp_json['rt_cd'] == API_RETURN_CODE['NO_DATA']:
                    continue
                return resp_json

            except Exception as e:
                logger.debug(f"fetch_search_stock_info 에러: {e}")
                if resp_json['rt_cd'] != API_RETURN_CODE['SUCCESS']:
                    continue
                raise e

    # IPO Schedule API
    def fetch_ipo_schedule(
        self,
        from_date: str = None,
        to_date: str = None,
        symbol: str = ""
    ) -> dict:
        """공모주 청약 일정 조회

        예탁원정보(공모주청약일정) API를 통해 공모주 정보를 조회합니다.

        Args:
            from_date: 조회 시작일 (YYYYMMDD, 기본값: 오늘)
            to_date: 조회 종료일 (YYYYMMDD, 기본값: 30일 후)
            symbol: 종목코드 (선택, 공백시 전체 조회)

        Returns:
            dict: 공모주 청약 일정 정보
        """
        # 날짜 기본값 설정
        if not from_date:
            from_date = datetime.now().strftime("%Y%m%d")
        if not to_date:
            to_date = (datetime.now() + timedelta(days=30)).strftime("%Y%m%d")

        # 날짜 유효성 검증
        if not validate_date_format(from_date) or not validate_date_format(to_date):
            raise ValueError("날짜 형식은 YYYYMMDD 이어야 합니다.")

        if not validate_date_range(from_date, to_date):
            raise ValueError("시작일은 종료일보다 이전이어야 합니다.")

        path = "uapi/domestic-stock/v1/ksdinfo/pub-offer"
        url = f"{self.base_url}/{path}"
        headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "tr_id": "HHKDB669108C0",
            "custtype": "P"  # 개인
        }

        params = {
            "SHT_CD": symbol,
            "CTS": "",
            "F_DT": from_date,
            "T_DT": to_date
        }

        return self._request_with_token_refresh("GET", url, headers, params)

    # 해외 주식 마스터 파일 API
    def fetch_overseas_symbols(
        self,
        market: str,
        ttl_hours: int = 168,
        force_download: bool = False
    ) -> pd.DataFrame:
        """해외 주식 종목 코드 조회

        해외 거래소(나스닥, 뉴욕, 홍콩 등) 마스터 파일을 다운로드하여
        종목 코드 목록을 DataFrame으로 반환합니다.

        지원 거래소 (11개):
            - nas: 나스닥 (NASDAQ)
            - nys: 뉴욕 (NYSE)
            - ams: 아멕스 (AMEX)
            - shs: 상해
            - shi: 상해지수
            - szs: 심천
            - szi: 심천지수
            - tse: 도쿄
            - hks: 홍콩
            - hnx: 하노이
            - hsx: 호치민

        Args:
            market: 시장 코드 (nas, nys, ams, shs, shi, szs, szi, tse, hks, hnx, hsx)
            ttl_hours: 캐시 유효 시간 (기본 1주일 = 168시간)
            force_download: 강제 다운로드 여부

        Returns:
            pd.DataFrame: 해외 종목 정보
                - 심볼: 종목 심볼 (티커)
                - 한글명: 종목 한글명
                - 영문명: 종목 영문명
                - 통화: 거래 통화
                - 거래소코드: 거래소 코드
                - ... (총 24개 컬럼)

        Raises:
            ValueError: 잘못된 시장 코드

        Example:
            >>> df = broker.fetch_overseas_symbols("nas")  # 나스닥
            >>> df = broker.fetch_overseas_symbols("hks")  # 홍콩
            >>> print(f"종목 수: {len(df)}")
        """
        if market not in OVERSEAS_MARKETS:
            valid_markets = ", ".join(OVERSEAS_MARKETS.keys())
            raise ValueError(f"잘못된 시장 코드: {market}. 지원 코드: {valid_markets}")

        base_dir = os.getcwd()
        file_name = f"{market}mst.cod.zip"
        url = f"https://new.real.download.dws.co.kr/common/master/{file_name}"

        self.download_master_file(base_dir, file_name, url, ttl_hours, force_download)
        df = parse_overseas_stock_master(base_dir, market)
        return df

    def fetch_nasdaq_symbols(
        self,
        ttl_hours: int = 168,
        force_download: bool = False
    ) -> pd.DataFrame:
        """나스닥(NASDAQ) 종목 코드 조회

        Args:
            ttl_hours: 캐시 유효 시간 (기본 1주일 = 168시간)
            force_download: 강제 다운로드 여부

        Returns:
            pd.DataFrame: 나스닥 종목 정보
        """
        return self.fetch_overseas_symbols("nas", ttl_hours, force_download)

    def fetch_nyse_symbols(
        self,
        ttl_hours: int = 168,
        force_download: bool = False
    ) -> pd.DataFrame:
        """뉴욕증권거래소(NYSE) 종목 코드 조회

        Args:
            ttl_hours: 캐시 유효 시간 (기본 1주일 = 168시간)
            force_download: 강제 다운로드 여부

        Returns:
            pd.DataFrame: 뉴욕 종목 정보
        """
        return self.fetch_overseas_symbols("nys", ttl_hours, force_download)

    def fetch_amex_symbols(
        self,
        ttl_hours: int = 168,
        force_download: bool = False
    ) -> pd.DataFrame:
        """아멕스(AMEX) 종목 코드 조회

        Args:
            ttl_hours: 캐시 유효 시간 (기본 1주일 = 168시간)
            force_download: 강제 다운로드 여부

        Returns:
            pd.DataFrame: 아멕스 종목 정보
        """
        return self.fetch_overseas_symbols("ams", ttl_hours, force_download)

    def fetch_investor_trading_by_stock_daily(
        self,
        symbol: str,
        date: str,
        market_code: str = "J"
    ) -> dict:
        """종목별 투자자매매동향(일별) 조회 [v1_국내주식]

        특정 종목의 날짜별 외국인/기관/개인 매수매도 현황을 조회합니다.
        한국투자 HTS [0416] 종목별 일별동향 화면과 동일한 기능입니다.

        ※ 단위: 금액(백만원), 수량(주)
        ※ 당일 데이터는 장 종료 후 정상 조회 가능

        API 정보:
            - 경로: /uapi/domestic-stock/v1/quotations/investor-trade-by-stock-daily
            - Method: GET
            - 실전 TR ID: FHPTJ04160001
            - 모의투자: 미지원

        Args:
            symbol (str): 종목코드 6자리 (예: "005930")
            date (str): 조회 날짜 YYYYMMDD 형식 (예: "20251213")
            market_code (str): 시장 분류 코드 (기본값: "J")
                - "J": KRX (기본값)
                - "NX": NXT
                - "UN": 통합

        Returns:
            dict: API 응답 딕셔너리
                - rt_cd: 성공 실패 여부 ("0": 성공)
                - msg_cd: 응답코드
                - msg1: 응답메시지
                - output1: 종목 현재가 정보
                - output2: 일별 투자자 매매동향 리스트

        Example:
            >>> # 삼성전자 2025년 12월 13일 투자자 매매동향
            >>> result = broker.fetch_investor_trading_by_stock_daily("005930", "20251213")
            >>> if result['rt_cd'] == '0':
            ...     for day in result['output2']:
            ...         print(f"날짜: {day['stck_bsop_date']}")
            ...         print(f"외국인 순매수: {day['frgn_ntby_qty']}주")
            ...         print(f"기관 순매수: {day['orgn_ntby_qty']}주")
            ...         print(f"개인 순매수: {day['prsn_ntby_qty']}주")
        """
        path = "uapi/domestic-stock/v1/quotations/investor-trade-by-stock-daily"
        url = f"{self.base_url}/{path}"
        headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "tr_id": "FHPTJ04160001"
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": market_code,
            "FID_INPUT_ISCD": symbol,
            "FID_INPUT_DATE_1": date,
            "FID_ORG_ADJ_PRC": "",
            "FID_ETC_CLS_CODE": ""
        }
        return self._request_with_token_refresh("GET", url, headers, params)

    def fetch_investor_trend_by_market(
        self,
        market_code: str = "KSP",
        sector_code: str = "0001"
    ) -> dict:
        """시장별 투자자매매동향(시세) 조회 [v1_국내주식-074]

        시장별 투자자 유형(외국인, 개인, 기관 등)의 매매 현황을 시간대별로 조회합니다.
        한국투자 HTS [0403] 시장별 시간동향 화면과 동일한 기능입니다.

        API 정보:
            - 경로: /uapi/domestic-stock/v1/quotations/inquire-investor-time-by-market
            - Method: GET
            - 실전 TR ID: FHPTJ04030000
            - 모의투자: 미지원

        Args:
            market_code (str): 시장구분 코드 (기본값: "KSP")
                - "KSP": 코스피
                - "KSQ": 코스닥
                - "ETF": ETF
                - "ELW": ELW
                - "ETN": ETN
                - "K2I": 선물/콜옵션/풋옵션
                - "999": 주식선물
                - "MKI": 미니
                - "WKM": 위클리(월)
                - "WKI": 위클리(목)
                - "KQI": 코스닥150
            sector_code (str): 업종구분 코드 (기본값: "0001")
                - "0001": 코스피 종합
                - "1001": 코스닥 종합
                - "F001": 선물
                - "OC01": 콜옵션
                - "OP01": 풋옵션
                - "T000": ETF 전체
                - "W000": ELW 전체
                - "E199": ETN 전체

        Returns:
            dict: API 응답 딕셔너리
                - rt_cd: 성공 실패 여부 ("0": 성공)
                - msg_cd: 응답코드
                - msg1: 응답메시지
                - output: 시간대별 투자자 매매동향 리스트

        투자자 유형별 응답 필드:
            - frgn_*: 외국인
            - prsn_*: 개인
            - orgn_*: 기관계
            - scrt_*: 증권
            - ivtr_*: 투자신탁
            - pe_fund_*: 사모펀드
            - bank_*: 은행
            - insu_*: 보험
            - mrbn_*: 종금
            - fund_*: 기금
            - etc_orgt_*: 기타단체
            - etc_corp_*: 기타법인

        세부 필드 접미사:
            - _seln_vol: 매도 거래량
            - _shnu_vol: 매수 거래량
            - _ntby_qty: 순매수 수량
            - _seln_tr_pbmn: 매도 거래 대금
            - _shnu_tr_pbmn: 매수 거래 대금
            - _ntby_tr_pbmn: 순매수 거래 대금

        Example:
            >>> # 코스피 종합 투자자 매매동향
            >>> result = broker.fetch_investor_trend_by_market("KSP", "0001")
            >>> if result['rt_cd'] == '0':
            ...     for item in result['output']:
            ...         print(f"시간: {item.get('bsop_hour_clss_code', 'N/A')}")
            ...         print(f"외국인 순매수: {item['frgn_ntby_qty']}주")
            ...         print(f"기관 순매수: {item['orgn_ntby_qty']}주")
            ...         print(f"개인 순매수: {item['prsn_ntby_qty']}주")

            >>> # 코스닥 종합 투자자 매매동향
            >>> result = broker.fetch_investor_trend_by_market("KSQ", "1001")

            >>> # ETF 전체 투자자 매매동향
            >>> result = broker.fetch_investor_trend_by_market("ETF", "T000")
        """
        path = "uapi/domestic-stock/v1/quotations/inquire-investor-time-by-market"
        url = f"{self.base_url}/{path}"
        headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "tr_id": "FHPTJ04030000"
        }
        params = {
            "fid_input_iscd": market_code,
            "fid_input_iscd_2": sector_code
        }
        return self._request_with_token_refresh("GET", url, headers, params)
