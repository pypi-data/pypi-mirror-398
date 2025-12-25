#!/bin/bash
#
# 한국투자증권 API 전체 시장 테스트 스크립트
# 국내주식, 해외주식, 해외선물 인기 종목 조회
#
# 사용법: ./scripts/test_all_markets_api.sh
#

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 환경변수 확인
if [ -z "$KOREA_INVESTMENT_API_KEY" ] || [ -z "$KOREA_INVESTMENT_API_SECRET" ]; then
    echo -e "${RED}Error: 환경변수가 설정되지 않았습니다.${NC}"
    echo "다음 환경변수를 설정해주세요:"
    echo "  export KOREA_INVESTMENT_API_KEY='your-api-key'"
    echo "  export KOREA_INVESTMENT_API_SECRET='your-api-secret'"
    exit 1
fi

BASE_URL="https://openapi.koreainvestment.com:9443"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       한국투자증권 API 전체 시장 테스트                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ========================================
# Access Token 발급
# ========================================
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

# ========================================
# 결과 저장용 배열
# ========================================
declare -a RESULTS

# ========================================
# 1. 국내 주식 조회
# ========================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  [1] 국내 주식 (KOSPI/KOSDAQ)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 국내 주식 인기 종목
declare -a KR_STOCKS=(
    "005930:삼성전자"
    "000660:SK하이닉스"
    "035420:NAVER"
    "005380:현대차"
    "035720:카카오"
    "006400:삼성SDI"
    "051910:LG화학"
    "003670:포스코퓨처엠"
)

for item in "${KR_STOCKS[@]}"; do
    IFS=':' read -r symbol name <<< "$item"

    response=$(curl -s -X GET "${BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price?FID_COND_MRKT_DIV_CODE=J&FID_INPUT_ISCD=${symbol}" \
      -H "Content-Type: application/json; charset=utf-8" \
      -H "authorization: Bearer $ACCESS_TOKEN" \
      -H "appkey: $KOREA_INVESTMENT_API_KEY" \
      -H "appsecret: $KOREA_INVESTMENT_API_SECRET" \
      -H "tr_id: FHKST01010100" \
      -H "custtype: P")

    # 결과 파싱
    result=$(python3 << EOF
import json
try:
    data = json.loads('''$response''')
    if data.get('rt_cd') == '0':
        o = data.get('output', {})
        price = o.get('stck_prpr', 'N/A')
        change = o.get('prdy_vrss', 'N/A')
        rate = o.get('prdy_ctrt', 'N/A')
        sign = '+' if not change.startswith('-') else ''
        print(f"✓ {price:>10}원  {sign}{change:>8}원 ({sign}{rate}%)")
    else:
        print(f"✗ {data.get('msg1', 'Error')}")
except:
    print("✗ 파싱 오류")
EOF
)
    printf "  %-12s %-14s %s\n" "$symbol" "$name" "$result"
done

echo ""

# ========================================
# 2. 국내 ETF 조회
# ========================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  [2] 국내 ETF${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

declare -a KR_ETFS=(
    "069500:KODEX200"
    "102110:TIGER200"
    "252670:KODEX200선물인버스2X"
    "122630:KODEX레버리지"
    "371460:TIGER차이나전기차SOLACTIVE"
    "133690:TIGER미국나스닥100"
)

for item in "${KR_ETFS[@]}"; do
    IFS=':' read -r symbol name <<< "$item"

    response=$(curl -s -X GET "${BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price?FID_COND_MRKT_DIV_CODE=J&FID_INPUT_ISCD=${symbol}" \
      -H "Content-Type: application/json; charset=utf-8" \
      -H "authorization: Bearer $ACCESS_TOKEN" \
      -H "appkey: $KOREA_INVESTMENT_API_KEY" \
      -H "appsecret: $KOREA_INVESTMENT_API_SECRET" \
      -H "tr_id: FHKST01010100" \
      -H "custtype: P")

    result=$(python3 << EOF
import json
try:
    data = json.loads('''$response''')
    if data.get('rt_cd') == '0':
        o = data.get('output', {})
        price = o.get('stck_prpr', 'N/A')
        change = o.get('prdy_vrss', 'N/A')
        rate = o.get('prdy_ctrt', 'N/A')
        sign = '+' if not change.startswith('-') else ''
        print(f"✓ {price:>10}원  {sign}{change:>8}원 ({sign}{rate}%)")
    else:
        print(f"✗ {data.get('msg1', 'Error')}")
except:
    print("✗ 파싱 오류")
EOF
)
    printf "  %-12s %-26s %s\n" "$symbol" "$name" "$result"
done

echo ""

# ========================================
# 3. 미국 주식 조회
# ========================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  [3] 미국 주식 (NASDAQ/NYSE)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 미국 주식 인기 종목 (거래소:심볼:이름)
declare -a US_STOCKS=(
    "NAS:AAPL:Apple"
    "NAS:MSFT:Microsoft"
    "NAS:NVDA:NVIDIA"
    "NAS:GOOGL:Alphabet"
    "NAS:AMZN:Amazon"
    "NAS:TSLA:Tesla"
    "NAS:META:Meta"
    "NYS:BRK.B:BerkshireB"
)

for item in "${US_STOCKS[@]}"; do
    IFS=':' read -r excd symbol name <<< "$item"

    response=$(curl -s -X GET "${BASE_URL}/uapi/overseas-price/v1/quotations/price?AUTH=&EXCD=${excd}&SYMB=${symbol}" \
      -H "Content-Type: application/json; charset=utf-8" \
      -H "authorization: Bearer $ACCESS_TOKEN" \
      -H "appkey: $KOREA_INVESTMENT_API_KEY" \
      -H "appsecret: $KOREA_INVESTMENT_API_SECRET" \
      -H "tr_id: HHDFS00000300" \
      -H "custtype: P")

    result=$(python3 << EOF
import json
try:
    data = json.loads('''$response''')
    if data.get('rt_cd') == '0':
        o = data.get('output', {})
        price = o.get('last', 'N/A')
        change = o.get('diff', 'N/A')
        rate = o.get('rate', 'N/A')
        sign = '+' if float(change) >= 0 else ''
        print(f"✓ \${float(price):>10.2f}  {sign}{float(change):>8.2f} ({sign}{rate}%)")
    else:
        print(f"✗ {data.get('msg1', 'Error')}")
except Exception as e:
    print(f"✗ 파싱 오류: {e}")
EOF
)
    printf "  %-6s %-12s %s\n" "$symbol" "$name" "$result"
done

echo ""

# ========================================
# 4. 해외 ETF 조회
# ========================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  [4] 미국 ETF${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

declare -a US_ETFS=(
    "AMS:SPY:S&P500ETF"
    "AMS:QQQ:NASDAQ100ETF"
    "AMS:IWM:Russell2000"
    "AMS:VTI:TotalStock"
    "AMS:SOXL:반도체3X"
    "AMS:TQQQ:나스닥3X"
)

for item in "${US_ETFS[@]}"; do
    IFS=':' read -r excd symbol name <<< "$item"

    response=$(curl -s -X GET "${BASE_URL}/uapi/overseas-price/v1/quotations/price?AUTH=&EXCD=${excd}&SYMB=${symbol}" \
      -H "Content-Type: application/json; charset=utf-8" \
      -H "authorization: Bearer $ACCESS_TOKEN" \
      -H "appkey: $KOREA_INVESTMENT_API_KEY" \
      -H "appsecret: $KOREA_INVESTMENT_API_SECRET" \
      -H "tr_id: HHDFS00000300" \
      -H "custtype: P")

    result=$(python3 << EOF
import json
try:
    data = json.loads('''$response''')
    if data.get('rt_cd') == '0':
        o = data.get('output', {})
        price = o.get('last', 'N/A')
        change = o.get('diff', 'N/A')
        rate = o.get('rate', 'N/A')
        sign = '+' if float(change) >= 0 else ''
        print(f"✓ \${float(price):>10.2f}  {sign}{float(change):>8.2f} ({sign}{rate}%)")
    else:
        print(f"✗ {data.get('msg1', 'Error')}")
except Exception as e:
    print(f"✗ 파싱 오류")
EOF
)
    printf "  %-6s %-14s %s\n" "$symbol" "$name" "$result"
done

echo ""

# ========================================
# 5. 해외 선물 조회
# ========================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  [5] 해외 선물 (CME/NYMEX/COMEX) - 유료 시세${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 해외 선물 인기 종목 (2025년 3월물 기준)
declare -a FUTURES=(
    "ESH25:E-miniS&P500"
    "NQH25:E-mini나스닥"
    "GCG25:금(COMEX)"
    "CLG25:WTI원유"
    "6EH25:유로FX"
    "ZBH25:미국채30년"
)

for item in "${FUTURES[@]}"; do
    IFS=':' read -r symbol name <<< "$item"

    response=$(curl -s -X GET "${BASE_URL}/uapi/overseas-futureoption/v1/quotations/inquire-price?SRS_CD=${symbol}" \
      -H "Content-Type: application/json; charset=utf-8" \
      -H "authorization: Bearer $ACCESS_TOKEN" \
      -H "appkey: $KOREA_INVESTMENT_API_KEY" \
      -H "appsecret: $KOREA_INVESTMENT_API_SECRET" \
      -H "tr_id: HHDFC55010000" \
      -H "custtype: P")

    result=$(python3 << EOF
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
        # 메시지 축약
        if '신청' in msg:
            print(f"✗ 유료시세 미가입")
        else:
            print(f"✗ {msg[:30]}")
except Exception as e:
    print(f"✗ 파싱 오류")
EOF
)
    printf "  %-8s %-16s %s\n" "$symbol" "$name" "$result"
done

echo ""

# ========================================
# 6. 국내 지수 조회
# ========================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  [6] 국내 지수${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

declare -a KR_INDEX=(
    "0001:코스피"
    "1001:코스닥"
    "2001:코스피200"
)

for item in "${KR_INDEX[@]}"; do
    IFS=':' read -r symbol name <<< "$item"

    response=$(curl -s -X GET "${BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-index-price?FID_COND_MRKT_DIV_CODE=U&FID_INPUT_ISCD=${symbol}" \
      -H "Content-Type: application/json; charset=utf-8" \
      -H "authorization: Bearer $ACCESS_TOKEN" \
      -H "appkey: $KOREA_INVESTMENT_API_KEY" \
      -H "appsecret: $KOREA_INVESTMENT_API_SECRET" \
      -H "tr_id: FHPUP02100000" \
      -H "custtype: P")

    result=$(python3 << EOF
import json
try:
    data = json.loads('''$response''')
    if data.get('rt_cd') == '0':
        o = data.get('output', {})
        price = o.get('bstp_nmix_prpr', 'N/A')
        change = o.get('bstp_nmix_prdy_vrss', 'N/A')
        rate = o.get('bstp_nmix_prdy_ctrt', 'N/A')
        sign = '+' if not str(change).startswith('-') else ''
        print(f"✓ {float(price):>10.2f}  {sign}{float(change):>8.2f} ({sign}{rate}%)")
    else:
        print(f"✗ {data.get('msg1', 'Error')}")
except Exception as e:
    print(f"✗ 파싱 오류: {e}")
EOF
)
    printf "  %-8s %-12s %s\n" "$symbol" "$name" "$result"
done

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  조회 완료!                                                ║${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}║  ※ 해외선물은 유료 시세입니다.                            ║${NC}"
echo -e "${BLUE}║     HTS/MTS에서 유료 가입 후 익일부터 조회 가능            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
