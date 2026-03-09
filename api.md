# Browser API Documentation

This document describes the REST API endpoints available for the Advanced Web Browser backend.

## Base URL

```
http://127.0.0.1:5000/api
```

## Authentication

Currently, the API does not require authentication. This may change in future versions.

## Response Format

All responses are in JSON format. Success responses return the requested data, while error responses return:

```json
{
  "error": "Error description"
}
```

## Endpoints

### Bookmarks

#### Get All Bookmarks
```
GET /api/bookmarks
```

**Query Parameters:**
- `folder` (optional): Filter by folder name

**Response:**
```json
[
  {
    "id": 1,
    "title": "Google",
    "url": "https://www.google.com",
    "folder": "Search Engines",
    "tags": ["search", "google"],
    "favicon": "https://www.google.com/favicon.ico",
    "created_at": "2023-01-01T12:00:00",
    "last_visited": "2023-01-01T12:00:00"
  }
]
```

#### Add Bookmark
```
POST /api/bookmarks
```

**Request Body:**
```json
{
  "title": "Google",
  "url": "https://www.google.com",
  "folder": "Search Engines",
  "tags": ["search", "google"]
}
```

**Response:**
```json
{
  "id": 1,
  "message": "Bookmark added successfully"
}
```

#### Delete Bookmark
```
DELETE /api/bookmarks/{id}
```

**Response:**
```json
{
  "message": "Bookmark deleted successfully"
}
```

### History

#### Get History
```
GET /api/history
```

**Query Parameters:**
- `limit` (optional): Maximum number of entries (default: 100)
- `offset` (optional): Offset for pagination (default: 0)

**Response:**
```json
[
  {
    "id": 1,
    "url": "https://www.google.com",
    "title": "Google",
    "visit_count": 5,
    "last_visited": "2023-01-01T12:00:00",
    "favicon": "https://www.google.com/favicon.ico",
    "session_id": "session123"
  }
]
```

#### Add History Entry
```
POST /api/history
```

**Request Body:**
```json
{
  "url": "https://www.google.com",
  "title": "Google",
  "favicon": "https://www.google.com/favicon.ico",
  "session_id": "session123"
}
```

**Response:**
```json
{
  "id": 1,
  "message": "History entry added successfully"
}
```

#### Clear History
```
DELETE /api/history
```

**Response:**
```json
{
  "message": "History cleared successfully"
}
```

### Preferences

#### Get All Preferences
```
GET /api/preferences
```

**Response:**
```json
{
  "browser.theme": "dark",
  "browser.enable_javascript": true,
  "security.enable_ad_blocker": true
}
```

#### Get Specific Preference
```
GET /api/preferences/{key}
```

**Response:**
```json
{
  "key": "browser.theme",
  "value": "dark",
  "category": "appearance",
  "updated_at": "2023-01-01T12:00:00"
}
```

#### Set Preference
```
PUT /api/preferences/{key}
```

**Request Body:**
```json
{
  "value": "light",
  "category": "appearance"
}
```

**Response:**
```json
{
  "message": "Preference set successfully"
}
```

### Cache

#### Get Cached Content
```
GET /api/cache/{url}
```

**Response:** Returns the cached content as binary data

#### Cache Content
```
PUT /api/cache/{url}
```

**Request Body:**
```json
{
  "content": "base64-encoded-content",
  "content_type": "text/html",
  "expires_at": "2023-01-01T12:00:00"
}
```

**Response:**
```json
{
  "message": "Content cached successfully"
}
```

#### Cleanup Cache
```
POST /api/cache/cleanup
```

**Response:**
```json
{
  "message": "Cleaned up 25 expired cache entries"
}
```

### Sessions

#### Get Sessions
```
GET /api/sessions
```

**Response:**
```json
[
  {
    "session_id": "session123",
    "name": "Morning Browsing",
    "tabs": [
      {
        "url": "https://www.google.com",
        "title": "Google"
      }
    ],
    "created_at": "2023-01-01T12:00:00",
    "last_accessed": "2023-01-01T12:00:00"
  }
]
```

#### Save Session
```
POST /api/sessions
```

**Request Body:**
```json
{
  "name": "Morning Browsing",
  "tabs": [
    {
      "url": "https://www.google.com",
      "title": "Google"
    }
  ]
}
```

**Response:**
```json
{
  "session_id": "session123",
  "message": "Session saved successfully"
}
```

#### Delete Session
```
DELETE /api/sessions/{session_id}
```

**Response:**
```json
{
  "message": "Session deleted successfully"
}
```

### Security

#### Check URL Security
```
POST /api/security/check-url
```

**Request Body:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "safe": true
}
```

#### Get Blocklist
```
GET /api/security/blocklist
```

**Response:**
```json
{
  "blocklist": ["malware-site.com", "phishing-site.net"]
}
```

## Error Codes

- `400`: Bad Request - Invalid request parameters
- `404`: Not Found - Resource not found
- `500`: Internal Server Error - Server error

## Rate Limiting

Currently, there are no rate limits implemented. This may change in future versions.

## WebSocket Support

Real-time features like live updates and notifications will be implemented using WebSockets in a future version.

## Extension API

Extensions can access the browser API through the ExtensionAPI class, which provides methods for:

- Tab management
- Bookmark operations
- History access
- Settings management
- UI operations
- Network requests
- Storage operations

See the `extensions/api.py` file for detailed documentation of the Extension API.

## Data Models

### Bookmark Model
```json
{
  "id": "integer",
  "title": "string",
  "url": "string",
  "folder": "string",
  "tags": "array",
  "favicon": "string",
  "created_at": "datetime",
  "last_visited": "datetime"
}
```

### History Entry Model
```json
{
  "id": "integer",
  "url": "string",
  "title": "string",
  "visit_count": "integer",
  "last_visited": "datetime",
  "favicon": "string",
  "session_id": "string"
}
```

### Session Model
```json
{
  "session_id": "string",
  "name": "string",
  "tabs": "array",
  "created_at": "datetime",
  "last_accessed": "datetime"
}
```

## Usage Examples

### Python Example
```python
import requests

# Get all bookmarks
response = requests.get('http://127.0.0.1:5000/api/bookmarks')
bookmarks = response.json()

# Add a new bookmark
bookmark_data = {
    'title': 'Example Site',
    'url': 'https://example.com',
    'folder': 'Examples'
}
response = requests.post('http://127.0.0.1:5000/api/bookmarks', json=bookmark_data)
```

### JavaScript Example
```javascript
// Get history
fetch('http://127.0.0.1:5000/api/history')
  .then(response => response.json())
  .then(history => console.log(history));

// Set preference
const prefData = {
  value: 'light',
  category: 'appearance'
};
fetch('http://127.0.0.1:5000/api/preferences/browser.theme', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(prefData)
});
```

## Testing

The API can be tested using tools like:

- curl
- Postman
- Python requests library
- JavaScript fetch API

Example curl command:
```bash
curl -X GET http://127.0.0.1:5000/api/bookmarks
```

## Future Enhancements

Planned API enhancements include:

1. **Authentication**: User authentication and authorization
2. **WebSockets**: Real-time updates and notifications
3. **File Upload**: Support for uploading files
4. **Search API**: Advanced search functionality
5. **Analytics**: Usage analytics and reporting
6. **Multi-user Support**: Multiple user profiles
7. **Sync API**: Data synchronization across devices
