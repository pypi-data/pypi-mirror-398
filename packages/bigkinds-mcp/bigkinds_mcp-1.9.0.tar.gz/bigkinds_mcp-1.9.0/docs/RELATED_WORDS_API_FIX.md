# Related Words API Fix

## Problem

The BigKinds related words API (`POST /api/analysis/relationalWords.do`) was returning a 500 error:

```json
{
  "code": "500",
  "message": "토픽랭크 연산 중 오류가 발생하였습니다."
}
```

This error occurred even after successful login, with various parameter combinations including:
- Different date ranges (recent, older, 3+ months)
- Different `maxNewsCount` values (50, 100, 200, 500, 1000)
- With and without `resultNumber`, `analysisType`, etc.

## Root Cause

By analyzing the JavaScript source code at `/js/ptech/news/visualization/relational-word.js`, we discovered that the API requires two critical parameters that were missing:

1. **`searchKey`**: Must be set to the same value as `keyword`
2. **`indexName`**: Must be set to `"news"`

These parameters are not documented in the API response but are required by the backend.

## Solution

### Code Changes

Updated `/Users/sdh/Dev/01_active_projects/bigkinds/src/bigkinds_mcp/core/async_client.py`:

```python
# Before (missing parameters)
data = {
    "keyword": keyword,
    "startDate": start_date,
    "endDate": end_date,
    "maxNewsCount": max_news_count,
    "resultNumber": result_number,
    "analysisType": "relational_word",
    "startNo": 0,
}

# After (with required parameters)
data = {
    "keyword": keyword,
    "startDate": start_date,
    "endDate": end_date,
    "maxNewsCount": max_news_count,
    "resultNumber": result_number,
    "analysisType": "relational_word",
    "sortMethod": "score",          # Added
    "startNo": 1,                    # Changed from 0 to 1
    "isTmUsable": True,              # Added (always True)
    "searchKey": keyword,            # ⚠️ REQUIRED
    "indexName": "news",             # ⚠️ REQUIRED
}
```

Also updated the login success check to handle the new response format:

```python
# Before
if result.get("success") or result.get("result") == "success":

# After
if result.get("userSn") or result.get("success") or result.get("result") == "success":
```

The login API now returns user information including `userSn` instead of just `{"success": true}`.

## Verification

### Test Results

```bash
$ export BIGKINDS_USER_ID=your_email
$ export BIGKINDS_USER_PASSWORD=your_password
$ uv run python tests/test_related_words_fix.py
✅ Found 33 related words
Top word: 인공지능 (weight: 42.95)
```

### Example Request (Working)

```python
POST /api/analysis/relationalWords.do
{
    "keyword": "AI",
    "startDate": "2024-12-01",
    "endDate": "2024-12-10",
    "maxNewsCount": 100,
    "resultNumber": 50,
    "analysisType": "relational_word",
    "sortMethod": "score",
    "startNo": 1,
    "isTmUsable": true,
    "searchKey": "AI",      # Same as keyword
    "indexName": "news"     # Always "news"
}
```

### Example Response

```json
{
    "topics": {
        "data": [
            {
                "id": 2,
                "level": 1,
                "name": "인공지능",
                "weight": 42.95
            },
            {
                "id": 3,
                "level": 3,
                "name": "생성형 AI",
                "weight": 10.5
            },
            ...
        ]
    },
    "news": {
        "documentCount": 1234,
        "resultList": [...]
    }
}
```

## MCP Tool Usage

The fixed API is available through the MCP tool:

```python
# Using the MCP tool
result = await get_related_keywords(
    keyword="AI",
    start_date="2024-12-01",
    end_date="2024-12-10",
    max_news_count=100,
    result_number=50,
)

# Returns:
{
    "success": true,
    "keyword": "AI",
    "date_range": "2024-12-01 to 2024-12-10",
    "related_words": [...],
    "news_count": 1234,
    "total_related_words": 33,
    "top_words": [
        {"name": "인공지능", "weight": 42.95, "tf": ...},
        ...
    ]
}
```

## Documentation Updates

- Updated `docs/VISUALIZATION_API.md` with required parameters marked with ⚠️
- Created `tests/test_related_words_fix.py` for regression testing
- This document (`docs/RELATED_WORDS_API_FIX.md`) for future reference

## Key Learnings

1. **Undocumented Parameters**: BigKinds API has required parameters not shown in network responses
2. **JavaScript is Source of Truth**: When API documentation is missing, check the actual JS implementation
3. **Parameter Values Matter**: Some parameters need specific values (e.g., `startNo: 1` not `0`)
4. **Login Response Changed**: The login API response format evolved to return user info instead of simple success flag

## Files Modified

1. `/Users/sdh/Dev/01_active_projects/bigkinds/src/bigkinds_mcp/core/async_client.py`
   - Fixed `get_related_keywords()` method
   - Updated login success check

2. `/Users/sdh/Dev/01_active_projects/bigkinds/docs/VISUALIZATION_API.md`
   - Documented required parameters

3. `/Users/sdh/Dev/01_active_projects/bigkinds/tests/test_related_words_fix.py`
   - Added regression test

## Related Issues

- The same parameters (`searchKey`, `indexName`) might be required for other visualization APIs
- Consider auditing other API calls to ensure all required parameters are present
