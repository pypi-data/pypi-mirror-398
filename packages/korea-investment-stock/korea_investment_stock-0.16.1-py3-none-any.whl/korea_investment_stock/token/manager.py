"""토큰 관리자 모듈

OAuth 토큰 발급, 검증, 갱신을 담당합니다.
"""

import json
import logging
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any

from .storage import TokenStorage

logger = logging.getLogger(__name__)


class TokenManager:
    """OAuth 토큰 관리자

    토큰 발급, 유효성 검증, 자동 갱신을 담당합니다.
    TokenStorage를 통해 토큰을 영구 저장합니다.

    Attributes:
        storage: 토큰 저장소 인스턴스
        access_token: 현재 액세스 토큰 (Bearer 포함)

    Example:
        >>> storage = FileTokenStorage()
        >>> manager = TokenManager(
        ...     storage=storage,
        ...     base_url="https://openapi.koreainvestment.com:9443",
        ...     api_key="your-key",
        ...     api_secret="your-secret"
        ... )
        >>> token = manager.get_valid_token()
    """

    OAUTH_PATH = "oauth2/tokenP"
    HASHKEY_PATH = "uapi/hashkey"

    def __init__(
        self,
        storage: TokenStorage,
        base_url: str,
        api_key: str,
        api_secret: str
    ):
        """TokenManager 초기화

        Args:
            storage: 토큰 저장소
            base_url: API 기본 URL
            api_key: API Key
            api_secret: API Secret
        """
        self.storage = storage
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self._access_token: Optional[str] = None

    @property
    def access_token(self) -> Optional[str]:
        """현재 액세스 토큰 (Bearer 포함)"""
        return self._access_token

    def get_valid_token(self) -> str:
        """유효한 토큰 반환 (필요시 발급/갱신)

        1. 저장된 토큰이 유효하면 반환
        2. 유효하지 않으면 새로 발급

        Returns:
            str: Bearer 토큰 문자열

        Raises:
            requests.RequestException: 토큰 발급 실패시
        """
        if self.is_token_valid():
            if self._access_token is None:
                self._load_token()
            return self._access_token

        # 토큰 발급
        self._issue_token()
        return self._access_token

    def is_token_valid(self) -> bool:
        """저장된 토큰의 유효성 확인

        Returns:
            bool: 토큰이 존재하고 만료되지 않았으면 True
        """
        return self.storage.check_token_valid(self.api_key, self.api_secret)

    def _load_token(self) -> None:
        """저장소에서 토큰 로드"""
        token_data = self.storage.load_token(self.api_key, self.api_secret)
        if token_data:
            self._access_token = f'Bearer {token_data["access_token"]}'
            logger.debug("토큰 로드 완료")

    def _issue_token(self) -> None:
        """OAuth 토큰 발급

        Korea Investment API의 OAuth 엔드포인트를 호출하여
        새 토큰을 발급받고 저장합니다.
        """
        url = f"{self.base_url}/{self.OAUTH_PATH}"
        headers = {"content-type": "application/json"}
        data = {
            "grant_type": "client_credentials",
            "appkey": self.api_key,
            "appsecret": self.api_secret
        }

        logger.debug(f"토큰 발급 요청: {url}")
        resp = requests.post(url, headers=headers, json=data)
        resp.raise_for_status()
        resp_data = resp.json()

        # Bearer 토큰 설정
        self._access_token = f'Bearer {resp_data["access_token"]}'

        # 만료 시간 파싱 (서울 시간대)
        token_data = self._parse_token_response(resp_data)

        # 저장
        self.storage.save_token(token_data)
        logger.info("새 토큰 발급 완료")

    def _parse_token_response(self, resp_data: Dict[str, Any]) -> Dict[str, Any]:
        """토큰 응답 파싱

        Args:
            resp_data: API 응답 데이터

        Returns:
            저장용 토큰 데이터 (timestamp 포함)
        """
        timezone = ZoneInfo('Asia/Seoul')
        dt = datetime.strptime(
            resp_data['access_token_token_expired'],
            '%Y-%m-%d %H:%M:%S'
        ).replace(tzinfo=timezone)

        return {
            **resp_data,
            'timestamp': int(dt.timestamp()),
            'api_key': self.api_key,
            'api_secret': self.api_secret
        }

    def issue_hashkey(self, data: dict) -> str:
        """해쉬키 발급

        POST 요청 데이터에 대한 해쉬키를 발급합니다.

        Args:
            data: POST 요청 데이터

        Returns:
            str: 해쉬키 문자열
        """
        url = f"{self.base_url}/{self.HASHKEY_PATH}"
        headers = {
            "content-type": "application/json",
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "User-Agent": "Mozilla/5.0"
        }

        resp = requests.post(url, headers=headers, data=json.dumps(data))
        resp.raise_for_status()
        return resp.json()["HASH"]

    def invalidate(self) -> bool:
        """저장된 토큰 무효화

        Returns:
            bool: 삭제 성공 여부
        """
        self._access_token = None
        return self.storage.delete_token(self.api_key, self.api_secret)
