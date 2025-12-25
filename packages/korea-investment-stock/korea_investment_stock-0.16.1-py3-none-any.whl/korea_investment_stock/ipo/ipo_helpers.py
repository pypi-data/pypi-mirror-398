"""
IPO 헬퍼 함수

공모주 관련 유틸리티 함수들을 제공합니다.
"""
import re
from datetime import datetime


def validate_date_format(date_str: str) -> bool:
    """날짜 형식 검증 (YYYYMMDD)

    Args:
        date_str: 검증할 날짜 문자열

    Returns:
        bool: 유효하면 True, 아니면 False
    """
    if len(date_str) != 8:
        return False
    try:
        datetime.strptime(date_str, "%Y%m%d")
        return True
    except ValueError:
        return False


def validate_date_range(from_date: str, to_date: str) -> bool:
    """날짜 범위 유효성 검증

    Args:
        from_date: 시작일 (YYYYMMDD)
        to_date: 종료일 (YYYYMMDD)

    Returns:
        bool: 시작일 <= 종료일이면 True
    """
    try:
        start = datetime.strptime(from_date, "%Y%m%d")
        end = datetime.strptime(to_date, "%Y%m%d")
        return start <= end
    except ValueError:
        return False


def parse_ipo_date_range(date_range_str: str) -> tuple:
    """청약기간 문자열 파싱

    Args:
        date_range_str: "2024.01.15~2024.01.16" 형식의 문자열

    Returns:
        tuple: (시작일 datetime, 종료일 datetime) 또는 (None, None)
    """
    if not date_range_str:
        return (None, None)

    # "2024.01.15~2024.01.16" 형식 파싱
    pattern = r'(\d{4}\.\d{2}\.\d{2})~(\d{4}\.\d{2}\.\d{2})'
    match = re.match(pattern, date_range_str)

    if match:
        try:
            start_str = match.group(1).replace('.', '')
            end_str = match.group(2).replace('.', '')
            start_date = datetime.strptime(start_str, "%Y%m%d")
            end_date = datetime.strptime(end_str, "%Y%m%d")
            return (start_date, end_date)
        except ValueError:
            pass

    return (None, None)


def format_ipo_date(date_str: str) -> str:
    """날짜 형식 변환 (YYYYMMDD -> YYYY-MM-DD)

    Args:
        date_str: 변환할 날짜 문자열

    Returns:
        str: 변환된 날짜 문자열
    """
    if len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    elif '.' in date_str:
        return date_str.replace('.', '-')
    return date_str


def calculate_ipo_d_day(ipo_date_str: str) -> int:
    """청약일까지 남은 일수 계산

    Args:
        ipo_date_str: 청약일 문자열 ("2024.01.15~2024.01.16" 형식)

    Returns:
        int: 청약 시작일까지 남은 일수 (유효하지 않으면 -999)
    """
    if '~' in ipo_date_str:
        start_date, _ = parse_ipo_date_range(ipo_date_str)
        if start_date:
            today = datetime.now()
            return (start_date - today).days
    return -999


def get_ipo_status(subscr_dt: str) -> str:
    """청약 상태 판단

    Args:
        subscr_dt: 청약기간 문자열 ("2024.01.15~2024.01.16" 형식)

    Returns:
        str: "예정", "진행중", "마감", "알수없음"
    """
    start_date, end_date = parse_ipo_date_range(subscr_dt)
    if not start_date or not end_date:
        return "알수없음"

    today = datetime.now()
    if today < start_date:
        return "예정"
    elif start_date <= today <= end_date:
        return "진행중"
    else:
        return "마감"


def format_number(num_str: str) -> str:
    """숫자 문자열에 천단위 콤마 추가

    Args:
        num_str: 숫자 문자열

    Returns:
        str: 천단위 콤마가 추가된 문자열
    """
    try:
        return f"{int(num_str):,}"
    except (ValueError, TypeError):
        return num_str
