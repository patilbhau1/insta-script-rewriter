# Instagram Video Transcription API

## Overview

This API allows you to transcribe Instagram videos (Reels, Posts, IGTV) by simply providing the URL. The API downloads the video, extracts the audio, and returns the transcription using OpenAI's Whisper model via Groq.

**Base URL:** `https://web-production-08d4.up.railway.app`

---

## Endpoints

### 1. Transcribe Video

Transcribe an Instagram video from URL.

**Endpoint:** `POST /api/transcribe`

**Headers:**
| Header | Value |
|--------|-------|
| Content-Type | application/json |

**Request Body:**
```json
{
  "url": "https://www.instagram.com/reel/ABC123/"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "transcription": "The transcribed text from the video...",
  "video_info": {
    "title": "Instagram Video",
    "url": "https://www.instagram.com/reel/ABC123/"
  }
}
```

**Error Response (400/500):**
```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

---

### 2. API Info

Get API usage information.

**Endpoint:** `GET /api/transcribe`

**Response:**
```json
{
  "api": "Instagram Video Transcription API",
  "version": "1.0",
  "usage": {
    "method": "POST",
    "endpoint": "/api/transcribe",
    "content_type": "application/json",
    "body": {
      "url": "https://www.instagram.com/reel/ABC123/"
    }
  },
  "example_curl": "curl -X POST -H 'Content-Type: application/json' -d '{\"url\": \"YOUR_INSTAGRAM_URL\"}' https://YOUR_DOMAIN/api/transcribe"
}
```

---

## Usage Examples

### cURL

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/reel/DS_2muXDP1p/"}' \
  https://web-production-08d4.up.railway.app/api/transcribe
```

### Python

```python
import requests

url = "https://web-production-08d4.up.railway.app/api/transcribe"
payload = {
    "url": "https://www.instagram.com/reel/DS_2muXDP1p/"
}

response = requests.post(url, json=payload)
data = response.json()

if data["success"]:
    print("Transcription:", data["transcription"])
else:
    print("Error:", data["error"])
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

async function transcribeVideo(instagramUrl) {
    try {
        const response = await axios.post(
            'https://web-production-08d4.up.railway.app/api/transcribe',
            { url: instagramUrl }
        );
        
        if (response.data.success) {
            console.log('Transcription:', response.data.transcription);
        } else {
            console.error('Error:', response.data.error);
        }
    } catch (error) {
        console.error('Request failed:', error.message);
    }
}

transcribeVideo('https://www.instagram.com/reel/DS_2muXDP1p/');
```

### JavaScript (Browser/Fetch)

```javascript
async function transcribeVideo(instagramUrl) {
    const response = await fetch('https://web-production-08d4.up.railway.app/api/transcribe', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: instagramUrl })
    });
    
    const data = await response.json();
    
    if (data.success) {
        console.log('Transcription:', data.transcription);
    } else {
        console.error('Error:', data.error);
    }
}
```

### PowerShell

```powershell
$body = @{url = "https://www.instagram.com/reel/DS_2muXDP1p/"} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "https://web-production-08d4.up.railway.app/api/transcribe" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"

if ($response.success) {
    Write-Host "Transcription: $($response.transcription)"
} else {
    Write-Host "Error: $($response.error)"
}
```

---

## Supported URL Formats

The API supports the following Instagram URL formats:

| Type | Example URL |
|------|-------------|
| Reel | `https://www.instagram.com/reel/ABC123/` |
| Post | `https://www.instagram.com/p/ABC123/` |
| TV/IGTV | `https://www.instagram.com/tv/ABC123/` |
| With tracking params | `https://www.instagram.com/reel/ABC123/?utm_source=ig_web_copy_link` |

---

## Error Codes

| Error | Description |
|-------|-------------|
| `Missing required field: url` | No URL was provided in the request body |
| `Invalid Instagram URL` | The URL is not a valid Instagram URL |
| `Failed to download video` | Could not download the video (private account, deleted, etc.) |
| `Failed to extract audio` | Could not extract audio from the video |
| `Failed to transcribe audio` | Transcription failed (no speech, audio issues) |

---

## Rate Limits & Notes

- **Processing Time:** Each request takes approximately 10-60 seconds depending on video length
- **Video Length:** Works best with videos under 5 minutes
- **Private Accounts:** Cannot transcribe videos from private accounts
- **Language:** Currently optimized for English transcription

---

## Integration Ideas

1. **Content Repurposing:** Transcribe viral reels and analyze their scripts
2. **Accessibility:** Add captions to your own videos
3. **Research:** Analyze trends in Instagram content
4. **Automation:** Build workflows that process multiple videos
5. **Note-taking:** Extract key information from educational content

---

## Support

For issues or feature requests, please open an issue on the GitHub repository:
https://github.com/patilbhau1/insta-script-rewriter
