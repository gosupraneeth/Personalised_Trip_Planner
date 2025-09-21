# User-Specific Session Management

## Overview
Enhanced the Trip Planner application to support user-specific session management where all sessions for a specific user are saved and can be retrieved from Firestore.

## Key Features Implemented

### 1. Enhanced Firestore Data Structure
- **Main Sessions Collection**: `/sessions/{session_id}` - For global session access
- **User Sessions Subcollection**: `/users/{user_id}/sessions/{session_id}` - For user-specific queries
- **User Metadata**: `/users/{user_id}` - Tracks user statistics and last activity

### 2. New FirestoreTool Methods

#### Session Management
- `save_session(session_data)` - Enhanced to save in both global and user-specific collections
- `get_user_sessions(user_id, limit, active_only)` - Get all sessions for a user
- `get_user_latest_session(user_id)` - Get most recent session for a user
- `get_user_active_sessions(user_id)` - Get only active sessions for a user
- `get_user_info(user_id)` - Get user metadata and statistics
- `delete_user_session(user_id, session_id)` - Delete specific user session

### 3. Enhanced TripPlannerApp Methods

#### User Session Operations
- `get_user_sessions(user_id, limit, active_only)` - Returns formatted session list
- `get_user_latest_session(user_id)` - Loads latest session into app
- `format_user_sessions_summary(user_id)` - Creates formatted summary of user sessions

## Data Structure

### User Document (`/users/{user_id}`)
```json
{
  "user_id": "user-123",
  "last_session_id": "session-abc-123",
  "last_activity": "2025-09-21T10:34:28.057134+00:00",
  "total_sessions": 5
}
```

### Session Document (`/users/{user_id}/sessions/{session_id}`)
```json
{
  "session_id": "session-abc-123",
  "user_id": "user-123",
  "trip_request": { ... },
  "current_itinerary": { ... },
  "conversation_history": [...],
  "created_at": "2025-09-21T10:34:28.057134+00:00",
  "last_activity": "2025-09-21T10:34:28.057134+00:00",
  "is_active": true
}
```

## Usage Examples

### 1. Get All Sessions for a User
```python
sessions = app.get_user_sessions("user-123")
for session in sessions:
    print(f"Session: {session['session_id']}")
    print(f"Created: {session['created_at']}")
    print(f"Active: {session['is_active']}")
```

### 2. Get User Sessions Summary
```python
summary = app.format_user_sessions_summary("user-123")
print(summary)
# Output:
# 👤 **User user-123**
# 📊 **Total Sessions:** 3
# 🔄 **Active Sessions:** 2
# 📋 **Recent Sessions:**
# 🟢 **e2e202b8...** - 2025-09-21
# 🟢 **b109f854...** - 2025-09-20
```

### 3. Load Latest Session for User
```python
session = app.get_user_latest_session("user-123")
if session:
    response = await app.process_user_input("Continue planning my trip", session)
```

### 4. Direct Firestore Operations
```python
firestore_tool = app.tools["firestore"]

# Get user sessions
sessions = firestore_tool.get_user_sessions("user-123", limit=5)

# Get user info
user_info = firestore_tool.get_user_info("user-123")

# Delete user session
firestore_tool.delete_user_session("user-123", "session-abc-123")
```

## Benefits

1. **User-Centric Organization**: All sessions for a user are grouped together
2. **Efficient Queries**: Fast retrieval of user-specific sessions without scanning all sessions
3. **User Analytics**: Track user activity, session counts, and patterns
4. **Session Continuity**: Easy to find and continue previous conversations
5. **Scalability**: Efficient data structure that scales with user count

## Test Results

The test run successfully demonstrates:
- ✅ Multiple users can create sessions independently
- ✅ Sessions are saved to both global and user-specific collections
- ✅ User session retrieval works correctly
- ✅ Session summaries provide useful user information
- ✅ Individual session status tracking works
- ✅ All sessions maintain proper Firestore connectivity

## Migration Notes

- Existing sessions in the global `/sessions` collection will continue to work
- New sessions are automatically saved to both collections
- User metadata is created automatically when first session is saved
- No breaking changes to existing functionality