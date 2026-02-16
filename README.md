# Instagram Video Script Rewriter

A full-stack web application that analyzes Instagram videos and rewrites scripts for your brand.

## Features

- Upload Instagram video files
- Extract and transcribe audio using Groq's Whisper API
- Analyze video style (tone, pacing, format)
- Generate custom scripts tailored to your brand

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Add your Groq API key to `.env`:
```
GROQ_API_KEY=your_actual_api_key
```

4. Run the application:
```bash
python app.py
```

5. Open your browser to `http://localhost:5000`

## Usage

1. Upload an Instagram video file (MP4, MOV, etc.)
2. Enter your website URL or brand introduction
3. Click "Analyze & Generate Script"
4. View the original transcription, style analysis, and rewritten script

## Requirements

- Python 3.8+
- Groq API key (get one at https://console.groq.com)
- FFmpeg (for video processing)

## Tech Stack

- Backend: Flask (Python SSR)
- Audio Processing: MoviePy
- AI: Groq API (Whisper + LLaMA)
- Frontend: HTML, CSS, JavaScript (vanilla)
