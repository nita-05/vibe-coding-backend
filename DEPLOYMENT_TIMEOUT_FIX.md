# Deployment Timeout Fix for Custom Prompts

## Problem
After deployment, custom prompts were failing with 502 errors, even though they worked locally.

## Root Cause
1. **Deployment platform timeouts**: Most platforms (Render, Railway, Heroku) have request timeout limits (typically 30-60 seconds)
2. **OpenAI API latency**: Complex custom prompts can take 20-45 seconds to generate
3. **Timeout mismatch**: Backend timeout (60s) exceeded platform limits, causing 502 before response

## Fixes Applied

### 1. Reduced OpenAI Client Timeout
- **File**: `backend/app/services/openai_service.py`
- **Change**: Reduced timeout from 60s to 45s
- **Reason**: Stay under most deployment platform limits (30-60s)

### 2. Improved Error Handling
- **File**: `backend/app/api/routes.py`
- **Changes**:
  - Better error detection (timeout, rate limit, API key issues)
  - More descriptive error messages for users
  - Enhanced logging for debugging
  - Specific handling for deployment timeout errors

## Deployment Platform Configuration

### Render
- Default timeout: **30 seconds** (free tier), **60 seconds** (paid)
- To increase: Go to service settings → Advanced → Increase "Request Timeout"
- Recommended: Set to 60+ seconds for AI generation

### Railway
- Default timeout: **60 seconds**
- Usually sufficient, but check service logs if issues persist

### Heroku
- Default timeout: **30 seconds**
- Can be increased with `heroku config:set WEB_TIMEOUT=60`

### Vercel (if using serverless)
- Default timeout: **10 seconds** (Hobby), **60 seconds** (Pro)
- Consider using background jobs for long-running requests

## Testing
1. Test with simple prompts first (should work quickly)
2. Test with complex custom prompts (may take 20-40 seconds)
3. Check deployment logs for timeout errors
4. Monitor OpenAI API response times

## If Issues Persist

1. **Check deployment logs** for specific error messages
2. **Verify OPENAI_API_KEY** is set correctly in deployment environment
3. **Check platform timeout settings** - may need to increase
4. **Consider using background jobs** for very long requests (future improvement)
5. **Simplify prompts** - break complex requests into smaller parts

## Error Messages

Users will now see helpful messages:
- "AI request timed out. Custom prompts can take longer. Please try: 1) Simplifying your prompt, 2) Breaking it into smaller requests, or 3) Try again (sometimes it works on retry)."
- "Deployment timeout or upstream service issue. The request took too long. Please try a simpler prompt or contact support."

## Next Steps (Future Improvements)
1. Implement background job system for long-running requests
2. Add request queuing for better resource management
3. Add progress indicators for long-running generations
4. Consider streaming responses for better UX
