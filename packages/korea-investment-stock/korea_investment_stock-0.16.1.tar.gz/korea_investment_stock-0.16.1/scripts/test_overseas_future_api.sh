#!/bin/bash
#
# 해외선물 API 테스트 스크립트
#
# 사용법:
#   ./scripts/test_overseas_future_api.sh [종목코드]  # 단일 종목 조회
#   ./scripts/test_overseas_future_api.sh --list      # 인기 상품 목록 보기
#   ./scripts/test_overseas_future_api.sh --all       # 인기 상품 전체 조회
#
# 예시:
#   ./scripts/test_overseas_future_api.sh GCG25       # 금 선물 조회
#   ./scripts/test_overseas_future_api.sh ESH25       # E-mini S&P500 조회
#

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ========================================
# 인기 상품 목록 (우선순위 순)
# ========================================
declare -a POPULAR_FUTURES=(
    "GCG25:금 선물:COMEX"
    "CLG25:WTI 원유:NYMEX"
    "NGG25:천연가스:NYMEX"
    "ESH25:E-mini S&P500:CME"
    "NQH25:E-mini 나스닥:CME"
    "6EH25:유로/달러:CME"
    "ZBH25:미국채 30년:CBOT"
)

# ========================================
# 도움말 및 목록 출력
# ========================================
show_list() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║           해외선물 인기 상품 목록                          ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}  우선순위  종목코드    상품명              거래소${NC}"
    echo -e "${CYAN}  ────────  ────────    ──────              ──────${NC}"

    local idx=1
    for item in "${POPULAR_FUTURES[@]}"; do
        IFS=':' read -r symbol name exchange <<< "$item"
        printf "     %d       %-10s  %-18s  %s\n" "$idx" "$symbol" "$name" "$exchange"
        ((idx++))
    done

    echo ""
    echo -e "${YELLOW}※ 모든 해외선물 시세는 유료입니다.${NC}"
    echo -e "  CME, SGX 거래소는 HTS/MTS에서 유료 가입 후 익일부터 조회 가능합니다."
    echo ""
    echo -e "${GREEN}사용법:${NC}"
    echo "  ./scripts/test_overseas_future_api.sh GCG25   # 금 선물 조회"
    echo "  ./scripts/test_overseas_future_api.sh --all   # 전체 인기 상품 조회"
}

show_help() {
    echo "사용법: ./scripts/test_overseas_future_api.sh [옵션|종목코드]"
    echo ""
    echo "옵션:"
    echo "  --list, -l    인기 상품 목록 보기"
    echo "  --all, -a     인기 상품 전체 조회"
    echo "  --help, -h    도움말"
    echo ""
    echo "예시:"
    echo "  ./scripts/test_overseas_future_api.sh GCG25   # 금 선물 조회"
    echo "  ./scripts/test_overseas_future_api.sh ESH25   # E-mini S&P500 조회"
}

# 옵션 처리
case "$1" in
    --list|-l)
        show_list
        exit 0
        ;;
    --help|-h)
        show_help
        exit 0
        ;;
esac

# 환경변수 확인
if [ -z "$KOREA_INVESTMENT_API_KEY" ] || [ -z "$KOREA_INVESTMENT_API_SECRET" ]; then
    echo -e "${RED}Error: 환경변수가 설정되지 않았습니다.${NC}"
    echo "다음 환경변수를 설정해주세요:"
    echo "  export KOREA_INVESTMENT_API_KEY='your-api-key'"
    echo "  export KOREA_INVESTMENT_API_SECRET='your-api-secret'"
    exit 1
fi

# 기본값 설정
BASE_URL="https://openapi.koreainvestment.com:9443"
ACCESS_TOKEN=""

# ========================================
# Access Token 발급 함수
# ========================================
get_access_token() {
    echo -e "${GREEN}[Token] Access Token 발급 중...${NC}"

    TOKEN_RESPONSE=$(curl -s -X POST "${BASE_URL}/oauth2/tokenP" \
      -H "Content-Type: application/json" \
      -d "{
        \"grant_type\": \"client_credentials\",
        \"appkey\": \"$KOREA_INVESTMENT_API_KEY\",
        \"appsecret\": \"$KOREA_INVESTMENT_API_SECRET\"
      }")

    ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

    if [ -z "$ACCESS_TOKEN" ]; then
        echo -e "${RED}Error: 토큰 발급 실패${NC}"
        echo "응답: $TOKEN_RESPONSE"
        exit 1
    fi

    echo -e "  토큰 발급 완료: ${ACCESS_TOKEN:0:20}..."
    echo ""
}

# ========================================
# 단일 종목 조회 함수 (상세)
# ========================================
fetch_future_detail() {
    local symbol=$1

    echo -e "${GREEN}해외선물 현재가 조회: ${symbol}${NC}"
    echo -e "  API: /uapi/overseas-futureoption/v1/quotations/inquire-price"
    echo -e "  TR_ID: HHDFC55010000"
    echo ""

    PRICE_RESPONSE=$(curl -s -X GET "${BASE_URL}/uapi/overseas-futureoption/v1/quotations/inquire-price?SRS_CD=${symbol}" \
      -H "Content-Type: application/json; charset=utf-8" \
      -H "authorization: Bearer $ACCESS_TOKEN" \
      -H "appkey: $KOREA_INVESTMENT_API_KEY" \
      -H "appsecret: $KOREA_INVESTMENT_API_SECRET" \
      -H "tr_id: HHDFC55010000" \
      -H "custtype: P")

    # 결과 출력 (포맷팅)
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  API 응답 (Raw JSON)${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo "$PRICE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$PRICE_RESPONSE"

    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  주요 필드 요약${NC}"
    echo -e "${BLUE}========================================${NC}"

    python3 << EOF
import json

try:
    data = json.loads('''$PRICE_RESPONSE''')
    rt_cd = data.get('rt_cd', '')
    msg1 = data.get('msg1', '')

    if rt_cd == '0':
        output = data.get('output1', {})
        print(f"상태: 성공 (rt_cd={rt_cd})")
        print(f"메시지: {msg1}")
        print()
        print(f"현재가: {output.get('last_price', 'N/A')}")
        print(f"시가: {output.get('open_price', 'N/A')}")
        print(f"고가: {output.get('high_price', 'N/A')}")
        print(f"저가: {output.get('low_price', 'N/A')}")
        print(f"전일종가: {output.get('prev_price', 'N/A')}")
        print(f"전일대비: {output.get('prev_diff_price', 'N/A')} ({output.get('prev_diff_rate', 'N/A')}%)")
        print(f"거래량: {output.get('vol', 'N/A')}")
        print(f"거래소: {output.get('exch_cd', 'N/A')}")
        print(f"통화: {output.get('crc_cd', 'N/A')}")
        print(f"만기일: {output.get('expr_date', 'N/A')}")
        print(f"증거금: {output.get('trst_mgn', 'N/A')}")
    else:
        print(f"상태: 실패 (rt_cd={rt_cd})")
        print(f"메시지: {msg1}")
        print()
        print("※ 해외선물 시세는 유료입니다.")
        print("  CME, SGX 거래소는 HTS/MTS에서 유료 가입 후 익일부터 조회 가능합니다.")
except Exception as e:
    print(f"오류: {e}")
EOF
}

# ========================================
# 단일 종목 조회 함수 (요약 - 전체 조회용)
# ========================================
fetch_future_summary() {
    local symbol=$1
    local name=$2
    local exchange=$3

    local response=$(curl -s -X GET "${BASE_URL}/uapi/overseas-futureoption/v1/quotations/inquire-price?SRS_CD=${symbol}" \
      -H "Content-Type: application/json; charset=utf-8" \
      -H "authorization: Bearer $ACCESS_TOKEN" \
      -H "appkey: $KOREA_INVESTMENT_API_KEY" \
      -H "appsecret: $KOREA_INVESTMENT_API_SECRET" \
      -H "tr_id: HHDFC55010000" \
      -H "custtype: P")

    local result=$(python3 << EOF
import json
try:
    data = json.loads('''$response''')
    if data.get('rt_cd') == '0':
        o = data.get('output1', {})
        price = o.get('last_price', 'N/A')
        change = o.get('prev_diff_price', 'N/A')
        rate = o.get('prev_diff_rate', 'N/A')
        print(f"✓ {price:>12}  {change:>10} ({rate}%)")
    else:
        msg = data.get('msg1', 'Error')
        if '신청' in msg:
            print("✗ 유료시세 미가입")
        else:
            print(f"✗ {msg[:25]}")
except:
    print("✗ 파싱 오류")
EOF
)
    printf "  %-8s %-18s %-8s %s\n" "$symbol" "$name" "$exchange" "$result"
}

# ========================================
# 전체 인기 상품 조회 (--all)
# ========================================
fetch_all_futures() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║           해외선물 인기 상품 전체 조회                      ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    get_access_token

    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  종목코드  상품명              거래소    결과${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    for item in "${POPULAR_FUTURES[@]}"; do
        IFS=':' read -r symbol name exchange <<< "$item"
        fetch_future_summary "$symbol" "$name" "$exchange"
        sleep 0.1  # Rate limit 방지
    done

    echo ""
    echo -e "${YELLOW}※ 해외선물 시세는 유료입니다.${NC}"
    echo -e "  HTS/MTS에서 유료 가입 후 익일부터 조회 가능합니다."
    echo ""
    echo -e "${GREEN}완료!${NC}"
}

# ========================================
# 메인 로직
# ========================================

# --all 옵션 처리
if [ "$1" == "--all" ] || [ "$1" == "-a" ]; then
    fetch_all_futures
    exit 0
fi

# 단일 종목 조회
SYMBOL="${1:-GCG25}"  # 기본값: 금 선물

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  해외선물 API 테스트${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}종목코드:${NC} $SYMBOL"
echo ""

get_access_token
fetch_future_detail "$SYMBOL"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}완료!${NC}"
