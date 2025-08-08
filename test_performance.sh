#!/bin/bash

# performance_test.sh - Simple load testing script

echo "🧪 Testing Flask-only performance..."

URL="http://localhost:3000"
REQUESTS=1000
CONCURRENT=10

echo "Making $REQUESTS requests with $CONCURRENT concurrent connections to $URL"

# Simple curl-based test
start_time=$(date +%s)

for i in $(seq 1 $REQUESTS); do
    curl -s -o /dev/null -w "Request $i: %{http_code} - %{time_total}s\n" $URL &
    
    # Limit concurrent requests
    if (( i % CONCURRENT == 0 )); then
        wait  # Wait for this batch to complete
    fi
done

wait  # Wait for all remaining requests

end_time=$(date +%s)
total_time=$((end_time - start_time))

echo ""
echo "📊 Results:"
echo "Total time: ${total_time}s"
echo "Average time per request: $(echo "scale=3; $total_time / $REQUESTS" | bc)s"
echo "Requests per second: $(echo "scale=2; $REQUESTS / $total_time" | bc)"