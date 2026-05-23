# Task Progress: Fix Analysis Failure & Add Detailed Error Logging

## Root Causes Identified

1. **SSE mismatch** - Celery task publishes to in-memory SSE manager, but frontend uses DB polling SSE endpoint (two completely separate mechanisms)
2. **Error messages lost** - DB polling SSE endpoint never reads `analysis.error_message` from Analysis table, only sends generic "分析失败"
3. **Event loop complexity** - Complex async wrapping in sync Celery context is fragile
4. **Frontend doesn't display actual error** - Toast only shows generic messages

## Fix Items
- [x] Analyze root causes
- [ ] Fix `projects.py` SSE endpoint: read `analysis.error_message` and pass to frontend
- [ ] Fix `analysis_engine.py`: simplify event loop handling, add detailed logging
- [ ] Fix `llm_service.py`: add step-by-step logging with error details
- [ ] Fix `ProjectPage.tsx`: display actual error messages from SSE failed events
- [ ] Fix `AnalysisPage.tsx`: display error_message from API response
- [ ] Rebuild and test