#!/bin/bash
set -e
set -x  # Enable verbose mode to see each command

echo "=========================================="
echo "Running End-to-End Tests for SFT"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        printf "${GREEN}✓ PASSED${NC}: %s\n" "$2"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        printf "${RED}✗ FAILED${NC}: %s\n" "$2"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Cleanup function
cleanup() {
    printf "\n${YELLOW}Cleaning up test files...${NC}\n"
    rm -f test-file-*.txt downloaded-*.txt
}

trap cleanup EXIT

# Ensure SFT_SERVICE is set
if [ -z "$SFT_SERVICE" ]; then
    printf "${RED}Error: SFT_SERVICE environment variable not set${NC}\n"
    exit 1
fi

echo "Testing against: $SFT_SERVICE"
echo ""

# Test 1: Server Health Check
echo "Test 1: Server Health Check"
if curl -f -s http://${SFT_SERVICE}/health > /dev/null 2>&1; then
    print_result 0 "Server health check"
else
    print_result 1 "Server health check"
    exit 1
fi

# Test 2: Upload a small file
echo ""
echo "Test 2: Upload a small file"
echo "This is a test file for E2E testing" > test-file-1.txt
UPLOAD_OUTPUT=$(sft upload test-file-1.txt 1h 2>&1)
if echo "$UPLOAD_OUTPUT" | grep -q "Uploaded test-file-1.txt"; then
    print_result 0 "Upload small file"
    FILE_ID=$(echo "$UPLOAD_OUTPUT" | grep -oP 'sft download \K[0-9]+')
    echo "  File ID: $FILE_ID"
else
    print_result 1 "Upload small file"
    echo "$UPLOAD_OUTPUT"
fi

# Test 3: Download the uploaded file
if [ ! -z "$FILE_ID" ]; then
    echo ""
    echo "Test 3: Download the uploaded file"
    DOWNLOAD_OUTPUT=$(sft download $FILE_ID -o downloaded-1.txt 2>&1)
    if [ -f "downloaded-1.txt" ]; then
        print_result 0 "Download file"
        
        # Test 4: Verify file content
        echo ""
        echo "Test 4: Verify downloaded file content"
        if diff test-file-1.txt downloaded-1.txt > /dev/null 2>&1; then
            print_result 0 "File content verification"
        else
            print_result 1 "File content verification"
        fi
    else
        print_result 1 "Download file"
    fi
else
    echo ""
    printf "${YELLOW}Skipping download tests (no file ID)${NC}\n"
fi

# Test 5: Upload a larger file
echo ""
echo "Test 5: Upload a larger file (1MB)"
dd if=/dev/urandom of=test-file-2.txt bs=1024 count=1024 2>/dev/null
UPLOAD_OUTPUT=$(sft upload test-file-2.txt 30m 2>&1)
if echo "$UPLOAD_OUTPUT" | grep -q "Uploaded test-file-2.txt"; then
    print_result 0 "Upload large file (1MB)"
    FILE_ID_2=$(echo "$UPLOAD_OUTPUT" | grep -oP 'sft download \K[0-9]+')
else
    print_result 1 "Upload large file (1MB)"
fi

# Test 6: Download large file and verify checksum
if [ ! -z "$FILE_ID_2" ]; then
    echo ""
    echo "Test 6: Download large file and verify checksum"
    DOWNLOAD_OUTPUT=$(sft download $FILE_ID_2 -o downloaded-2.txt 2>&1)
    if [ -f "downloaded-2.txt" ]; then
        ORIGINAL_SHA=$(sha256sum test-file-2.txt | awk '{print $1}')
        DOWNLOADED_SHA=$(sha256sum downloaded-2.txt | awk '{print $1}')
        
        if [ "$ORIGINAL_SHA" = "$DOWNLOADED_SHA" ]; then
            print_result 0 "Large file checksum verification"
        else
            print_result 1 "Large file checksum verification"
            echo "  Original: $ORIGINAL_SHA"
            echo "  Downloaded: $DOWNLOADED_SHA"
        fi
    else
        print_result 1 "Download large file"
    fi
fi

# Test 7: Try to download non-existent file
echo ""
echo "Test 7: Download non-existent file (should fail)"
if sft download 999999 2>&1 | grep -q "Error"; then
    print_result 0 "Non-existent file error handling"
else
    print_result 1 "Non-existent file error handling"
fi

# Test 8: Upload with different time formats
echo ""
echo "Test 8: Upload with different time formats"
echo "Test file for time format" > test-file-3.txt

# Test 30 minutes
UPLOAD_OUTPUT=$(sft upload test-file-3.txt 30m 2>&1)
if echo "$UPLOAD_OUTPUT" | grep -q "Uploaded"; then
    print_result 0 "Upload with 30m time format"
else
    print_result 1 "Upload with 30m time format"
fi

# Test 2 hours
UPLOAD_OUTPUT=$(sft upload test-file-3.txt 2h 2>&1)
if echo "$UPLOAD_OUTPUT" | grep -q "Uploaded"; then
    print_result 0 "Upload with 2h time format"
else
    print_result 1 "Upload with 2h time format"
fi

# Print summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
printf "Tests Passed: ${GREEN}%s${NC}\n" "$TESTS_PASSED"
printf "Tests Failed: ${RED}%s${NC}\n" "$TESTS_FAILED"
echo "=========================================="

if [ $TESTS_FAILED -eq 0 ]; then
    printf "${GREEN}All tests passed!${NC}\n"
    exit 0
else
    printf "${RED}Some tests failed!${NC}\n"
    exit 1
fi
