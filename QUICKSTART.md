# Quick Start Guide

## Prerequisites

1. **Python 3.8+** - Check with `python --version`
2. **FFmpeg** - Required for video processing
   - Windows: Download from https://ffmpeg.org/download.html or use `winget install ffmpeg`
   - Mac: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg` or `sudo yum install ffmpeg`
3. **Groq API Key** - Get free key at https://console.groq.com

## Setup Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Groq API key
# GROQ_API_KEY=gsk_your_actual_key_here
```

### 3. Run the Application
```bash
python app.py
```

### 4. Open in Browser
Navigate to: http://localhost:5000

## Usage

1. **Upload Video**: Click to select or drag & drop an Instagram video (MP4, MOV, etc.)
2. **Enter Brand Info**: Add your website URL or describe your brand/company
3. **Generate**: Click "Analyze & Generate Script"
4. **Wait**: Processing takes 1-2 minutes depending on video length
5. **Review**: See the original transcription, style analysis, and custom script
6. **Copy**: Click "Copy Script" to use in your video production

## Troubleshooting

### Error: "GROQ_API_KEY not found"
- Make sure you created a `.env` file in the project root
- Verify your API key is correctly formatted: `GROQ_API_KEY=gsk_...`

### Error: "FFmpeg not found"
- Install FFmpeg (see prerequisites above)
- Restart your terminal after installation

### Video upload fails
- Check file size is under 100MB
- Ensure file format is supported (MP4, MOV, AVI, MKV, WEBM)
- Try converting the video to MP4 if issues persist

### "Module not found" errors
- Run `pip install -r requirements.txt` again
- Consider using a virtual environment:
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  pip install -r requirements.txt
  ```

## API Rate Limits

Groq free tier includes:
- 30 requests per minute
- 14,400 requests per day

This should be sufficient for testing and moderate usage.

## Production Considerations

For production deployment:
1. Set `debug=False` in `app.py`
2. Use a production WSGI server (gunicorn, waitress)
3. Set up proper file upload limits and security
4. Consider adding user authentication
5. Implement proper error logging
6. Use environment variables for all secrets
7. Add rate limiting to prevent abuse

## Features

✅ Video upload with drag & drop  
✅ Audio extraction from video  
✅ AI transcription with Whisper  
✅ Style analysis (tone, pacing, format)  
✅ Custom script generation  
✅ Copy-to-clipboard functionality  
✅ Responsive design  
✅ Error handling  

## Tech Stack

- **Backend**: Flask (Python)
- **AI**: Groq API (Whisper-large-v3, LLaMA-3.3-70b)
- **Video Processing**: MoviePy + FFmpeg
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Styling**: Custom CSS with modern design
