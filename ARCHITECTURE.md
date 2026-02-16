# Application Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  HTML (index.html) + CSS (style.css) + JS (script.js)     │ │
│  │  • File upload (drag & drop)                               │ │
│  │  • Form validation                                         │ │
│  │  • Loading states                                          │ │
│  │  • Results display                                         │ │
│  │  • Copy to clipboard                                       │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP POST /process
                              │ (multipart/form-data)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FLASK APPLICATION                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  app.py                                                    │ │
│  │  • Route handlers                                          │ │
│  │  • File validation & security                             │ │
│  │  • Request processing                                      │ │
│  │  • Error handling                                          │ │
│  │  • Response formatting                                     │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Processing Pipeline
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESSING PIPELINE                           │
│                                                                  │
│  1. VIDEO UPLOAD                                                │
│     ├─ Validate file type                                       │
│     ├─ Check file size (<100MB)                                 │
│     ├─ Secure filename                                          │
│     └─ Save to uploads/                                         │
│                                                                  │
│  2. AUDIO EXTRACTION                                            │
│     ├─ Load video with MoviePy                                  │
│     ├─ Extract audio track                                      │
│     ├─ Convert to MP3                                           │
│     └─ Save audio file                                          │
│                                                                  │
│  3. TRANSCRIPTION (Groq Whisper API)                           │
│     ├─ Read audio file                                          │
│     ├─ Send to Whisper-large-v3                                 │
│     ├─ Get text transcription                                   │
│     └─ Return transcription text                                │
│                                                                  │
│  4. STYLE ANALYSIS (Groq LLaMA API)                            │
│     ├─ Send transcription to LLaMA-3.3                          │
│     ├─ Analyze tone, pacing, format                             │
│     └─ Return style analysis                                    │
│                                                                  │
│  5. SCRIPT GENERATION (Groq LLaMA API)                         │
│     ├─ Combine: transcription + style + brand input             │
│     ├─ Generate custom script with LLaMA-3.3                    │
│     └─ Return rewritten script                                  │
│                                                                  │
│  6. CLEANUP                                                     │
│     ├─ Delete uploaded video                                    │
│     └─ Delete extracted audio                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ JSON Response
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RESPONSE TO CLIENT                          │
│  {                                                               │
│    "success": true,                                              │
│    "transcription": "...",                                       │
│    "style_analysis": "...",                                      │
│    "rewritten_script": "..."                                     │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User Input Flow
```
User Action → JavaScript Validation → FormData Creation → Fetch API → Flask Route
```

### 2. Processing Flow
```
Video File → Audio Extraction → Whisper API → Transcription Text
                                                      ↓
Brand Input ────────────────────────────────────────→ LLaMA API → Style Analysis
                                                      ↓
                                              LLaMA API → Rewritten Script
```

### 3. Response Flow
```
Flask Response → JSON → JavaScript → DOM Update → User Interface
```

## Component Details

### Frontend (Client-Side)

**HTML (templates/index.html)**
- Semantic structure
- Form with file input and textarea
- Results display sections
- Loading and error states

**CSS (static/css/style.css)**
- Modern gradient design
- Responsive layout
- Interactive animations
- Custom file input styling
- Card-based results display

**JavaScript (static/js/script.js)**
- File upload handling
- Drag & drop support
- Form submission via Fetch API
- Dynamic UI updates
- Clipboard operations
- Error handling

### Backend (Server-Side)

**Flask Application (app.py)**

Main routes:
- `GET /` → Render index.html
- `POST /process` → Process video and return results

Core functions:
- `allowed_file()` → File validation
- `extract_audio()` → Video to audio conversion
- `transcribe_audio()` → Whisper API integration
- `analyze_and_rewrite_script()` → LLaMA API integration

### External APIs

**Groq API Integration**

1. **Whisper API (Transcription)**
   - Endpoint: `audio.transcriptions.create()`
   - Model: `whisper-large-v3`
   - Input: Audio file (MP3)
   - Output: Text transcription

2. **LLaMA API (AI Generation)**
   - Endpoint: `chat.completions.create()`
   - Model: `llama-3.3-70b-versatile`
   - Uses:
     - Style analysis (temperature=0.3)
     - Script rewriting (temperature=0.7)

## Security Measures

### File Upload Security
```
1. File type validation (whitelist)
2. File size limits (100MB max)
3. Secure filename sanitization
4. Temporary storage with cleanup
5. No file serving from uploads
```

### API Security
```
1. API key stored in environment variables
2. Never exposed to client
3. Server-side only validation
4. Error messages sanitized
```

### Input Validation
```
1. Server-side file validation
2. Brand input sanitization
3. File existence checks
4. Error handling for all operations
```

## Error Handling Strategy

### Client-Side
- Form validation before submission
- Network error handling
- User-friendly error messages
- Visual error states

### Server-Side
- Try-catch blocks for all operations
- Automatic file cleanup on errors
- Detailed error logging
- HTTP status codes
- JSON error responses

## Performance Optimization

### Video Processing
- Efficient audio extraction with MoviePy
- Automatic file cleanup (no bloat)
- Streaming-ready architecture

### API Usage
- Optimized prompts for faster responses
- Appropriate temperature settings
- Token limit management

### Frontend
- Minimal JavaScript (no frameworks)
- CSS animations (GPU accelerated)
- Efficient DOM updates
- No unnecessary re-renders

## Scalability Considerations

### Current Architecture (MVP)
- Single-threaded Flask development server
- Synchronous processing
- Local file storage
- Suitable for: Testing, demos, light usage

### Production Upgrades Needed
```
1. WSGI Server: Gunicorn or Waitress
2. Task Queue: Celery for async processing
3. Storage: Cloud storage (S3, GCS)
4. Caching: Redis for API responses
5. Database: PostgreSQL for user data
6. Load Balancer: Nginx or cloud LB
7. Monitoring: Logging and metrics
8. Rate Limiting: Per-user limits
```

## Technology Decisions

### Why Flask?
- Lightweight and fast to develop
- Python SSR requirement
- Excellent for MVP
- Easy to scale later

### Why MoviePy?
- Simple API for video processing
- FFmpeg integration
- Cross-platform support
- Active maintenance

### Why Groq API?
- Fast inference times
- Excellent Whisper implementation
- Powerful LLaMA models
- Generous free tier

### Why Vanilla JavaScript?
- No build step needed
- Faster page loads
- Simpler deployment
- Full control over behavior

## File Structure Rationale

```
app.py                  # Single entry point, easy to find
templates/              # Flask convention
  └── index.html        # Single page app
static/                 # Static assets
  ├── css/             # Styling
  └── js/              # Interactivity
requirements.txt        # Python dependencies
.env                    # Configuration
uploads/                # Temporary storage
```

## Configuration Management

### Environment Variables (.env)
```
GROQ_API_KEY=xxx        # Required for AI features
```

### Flask Config (app.py)
```python
MAX_CONTENT_LENGTH      # Upload size limit
UPLOAD_FOLDER           # Temporary storage
ALLOWED_EXTENSIONS      # Security whitelist
```

## Deployment Architecture

### Development
```
Local Machine → Flask Dev Server → http://localhost:5000
```

### Production (Recommended)
```
User → CDN/Load Balancer → Nginx → Gunicorn → Flask App → Task Queue
                                                           ↓
                                                      External APIs
```

## Monitoring & Logging

### Current Implementation
- Console logging for API key check
- Error messages to client
- Basic exception handling

### Production Needs
- Structured logging (JSON)
- Log aggregation (ELK, CloudWatch)
- Error tracking (Sentry)
- Performance monitoring (New Relic)
- API usage tracking
- User analytics

## API Rate Limits

### Groq Free Tier
- 30 requests/minute
- 14,400 requests/day

### Application Limits
- 100MB max file size
- No user rate limiting (add for production)
- No concurrent request limits (add for production)

## Testing Strategy

### Current Testing
- `test_setup.py` for environment verification
- Manual testing for features

### Production Testing Needs
- Unit tests for functions
- Integration tests for API
- End-to-end tests for workflow
- Load testing for performance
- Security testing for vulnerabilities
