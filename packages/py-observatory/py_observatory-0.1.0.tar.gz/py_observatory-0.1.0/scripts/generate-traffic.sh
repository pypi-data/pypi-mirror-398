#!/bin/bash

# py-observatory Traffic Generator
# Generates various types of traffic to test the dashboard

BASE_URL="${1:-http://localhost:8001}"
DURATION="${2:-60}"

echo "=========================================="
echo " py-observatory Traffic Generator"
echo "=========================================="
echo "Target: $BASE_URL"
echo "Duration: ${DURATION}s"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Counters
REQUESTS=0
ERRORS=0

# Function to make request
request() {
    local method=$1
    local endpoint=$2
    local data=$3

    if [ "$method" == "POST" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" -d "$data" 2>/dev/null)
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint" 2>/dev/null)
    fi

    ((REQUESTS++))

    if [ "$response" -ge 400 ]; then
        ((ERRORS++))
        echo -e "${RED}[ERROR]${NC} $method $endpoint -> $response"
    else
        echo -e "${GREEN}[OK]${NC} $method $endpoint -> $response"
    fi
}

# Start time
START=$(date +%s)

echo ""
echo "Starting traffic generation..."
echo ""

while true; do
    ELAPSED=$(($(date +%s) - START))
    if [ $ELAPSED -ge $DURATION ]; then
        break
    fi

    # Random endpoint selection
    RAND=$((RANDOM % 10))

    case $RAND in
        0|1|2)
            # Root endpoint (30%)
            request GET "/"
            ;;
        3|4)
            # User endpoint with random ID (20%)
            USER_ID=$((RANDOM % 100 + 1))
            request GET "/api/users/$USER_ID"
            ;;
        5)
            # Invalid user (triggers 400)
            request GET "/api/users/0"
            ;;
        6|7)
            # Create order (20%)
            ORDER_TYPE=$([ $((RANDOM % 2)) -eq 0 ] && echo "online" || echo "store")
            TOTAL=$((RANDOM % 500 + 10))
            request POST "/api/orders" "{\"type\":\"$ORDER_TYPE\",\"total\":$TOTAL}"
            ;;
        8)
            # External call (10%)
            request GET "/api/external"
            ;;
        9)
            # Slow endpoint (10%)
            request GET "/api/slow"
            ;;
    esac

    # Trigger error endpoint occasionally
    if [ $((RANDOM % 20)) -eq 0 ]; then
        request GET "/api/error" 2>/dev/null || true
    fi

    # Random delay between requests (50-200ms)
    DELAY=$(echo "scale=3; (50 + $RANDOM % 150) / 1000" | bc)
    sleep $DELAY
done

echo ""
echo "=========================================="
echo " Traffic Generation Complete"
echo "=========================================="
echo "Duration: ${DURATION}s"
echo "Total Requests: $REQUESTS"
echo "Errors: $ERRORS"
echo ""
echo "View dashboard at: http://localhost:3001"
echo ""
