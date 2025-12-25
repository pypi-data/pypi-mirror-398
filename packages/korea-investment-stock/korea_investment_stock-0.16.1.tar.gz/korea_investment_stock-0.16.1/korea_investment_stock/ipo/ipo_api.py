"""
IPO API 모듈

공모주 청약 일정 조회 API를 제공합니다.
"""
import logging
from datetime import datetime, timedelta

import requests

from .ipo_helpers import validate_date_format, validate_date_range

logger = logging.getLogger(__name__)


def fetch_ipo_schedule(
    base_url: str,
    access_token: str,
    api_key: str,
    api_secret: str,
    from_date: str = None,
    to_date: str = None,
    symbol: str = ""
) -> dict:
    """공모주 청약 일정 조회

    예탁원정보(공모주청약일정) API를 통해 공모주 정보를 조회합니다.
    한국투자 HTS(eFriend Plus) > [0667] 공모주청약 화면과 동일한 기능입니다.

    Args:
        base_url: API base URL
        access_token: Bearer 토큰
        api_key: API key
        api_secret: API secret
        from_date: 조회 시작일 (YYYYMMDD, 기본값: 오늘)
        to_date: 조회 종료일 (YYYYMMDD, 기본값: 30일 후)
        symbol: 종목코드 (선택, 공백시 전체 조회)

    Returns:
        dict: 공모주 청약 일정 정보
            {
                "rt_cd": "0",  # 성공여부
                "msg_cd": "응답코드",
                "msg1": "응답메시지",
                "output1": [
                    {
                        "record_date": "기준일",
                        "sht_cd": "종목코드",
                        "isin_name": "종목명",
                        "fix_subscr_pri": "공모가",
                        "face_value": "액면가",
                        "subscr_dt": "청약기간",  # "2024.01.15~2024.01.16"
                        "pay_dt": "납입일",
                        "refund_dt": "환불일",
                        "list_dt": "상장/등록일",
                        "lead_mgr": "주간사",
                        "pub_bf_cap": "공모전자본금",
                        "pub_af_cap": "공모후자본금",
                        "assign_stk_qty": "당사배정물량"
                    }
                ]
            }

    Raises:
        ValueError: 날짜 형식 오류시

    Note:
        - 예탁원에서 제공한 자료이므로 정보용으로만 사용하시기 바랍니다.
        - 실제 청약시에는 반드시 공식 공모주 청약 공고문을 확인하세요.
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
    url = f"{base_url}/{path}"
    headers = {
        "content-type": "application/json",
        "authorization": access_token,
        "appKey": api_key,
        "appSecret": api_secret,
        "tr_id": "HHKDB669108C0",
        "custtype": "P"  # 개인
    }

    params = {
        "SHT_CD": symbol,
        "CTS": "",
        "F_DT": from_date,
        "T_DT": to_date
    }

    resp = requests.get(url, headers=headers, params=params)
    resp_json = resp.json()

    # 에러 처리
    if resp_json.get('rt_cd') != '0':
        logger.error(f"공모주 조회 실패: {resp_json.get('msg1', 'Unknown error')}")

    return resp_json
