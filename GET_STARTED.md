# 🚀 Get Started in 3 Minutes

## Quick Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create environment file
cp .env.example .env

# 3. Edit .env and add your Groq API key
# (Use any text editor: notepad, vim, nano, etc.)
```

## Get Your Groq API Key (Free)

1. Visit: https://console.groq.com
2. Sign up (free account)
3. Go to API Keys section
4. Create new key
5. Copy and paste into `.env` file

## Run the Application

```bash
# Start the server
python app.py

# You should see:
# ✓ Groq API key loaded
# * Running on http://0.0.0.0:5000
```

Open browser to: **http://localhost:5000**

## Test the Application

1. **Find a test video**: Use any Instagram video (MP4, MOV, etc.)
2. **Upload**: Drag & drop or click to select
3. **Enter brand info**: 
   - Example: "https://www.nike.com"
   - Or: "We sell eco-friendly water bottles"
4. **Click**: "Analyze & Generate Script"
5. **Wait**: ~1-2 minutes for processing
6. **View results**: Transcription, style analysis, and custom script

## Troubleshooting

### "GROQ_API_KEY not found"
```bash
# Make sure .env file exists (Windows: dir .env, Mac/Linux: ls .env)

# Check content (should have your key)
# Windows: type .env
# Mac/Linux: cat .env
```

### "FFmpeg not found"
```bash
# Windows: 
winget install ffmpeg

# Mac: 
brew install ffmpeg

# Linux:
sudo apt install ffmpeg  # Ubuntu/Debian
sudo yum install ffmpeg  # CentOS/RHEL

# Or download from: https://ffmpeg.org/download.html
```

### "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Verify setup
```bash
# Run verification script
python test_setup.py
```

## What You Get

### Input
- Instagram video file
- Your brand/website information

### Output
1. **Original Transcription**: What was said in the video
2. **Style Analysis**: Tone, pacing, format detected
3. **Custom Script**: New script matching the style for YOUR brand

### Example Output

**Original Transcription:**
> "Hey guys! Today I'm gonna show you the TOP 3 morning habits that changed my life. First up - cold showers! Yeah, I know it sounds crazy but hear me out..."

**Style Analysis:**
> Casual and energetic tone with direct address. Fast-paced delivery with numbered format. Uses rhetorical questions and conversational language. Hook-driven structure with immediate value proposition.

**Your Custom Script (for "eco water bottles"):**
> "Hey guys! Today I'm gonna show you the TOP 3 reasons our eco water bottles will change YOUR daily routine. First up - 24-hour cold retention! Yeah, I know everyone says that, but hear me out..."

## Project Structure

```
📁 instagram-script-rewriter/
│
├── 📄 app.py                    # Main Flask application
├── 📄 requirements.txt          # Python packages
├── 📄 .env                      # Your API key (create this)
│
├── 📁 templates/
│   └── 📄 index.html           # Main webpage
│
├── 📁 static/
│   ├── 📁 css/
│   │   └── 📄 style.css        # Styling
│   └── 📁 js/
│       └── 📄 script.js        # Interactions
│
└── 📁 uploads/                  # Temporary files (auto-created)
```

## Documentation Files

- **README.md** - Project overview
- **QUICKSTART.md** - Detailed setup guide
- **PROJECT_SUMMARY.md** - Complete feature list
- **ARCHITECTURE.md** - Technical architecture
- **GET_STARTED.md** - This file (fastest start)

## Features

✅ Upload videos (drag & drop)  
✅ Extract audio automatically  
✅ AI transcription (Whisper)  
✅ Style analysis (tone, pacing)  
✅ Custom script generation  
✅ Copy to clipboard  
✅ Clean, modern UI  
✅ Mobile responsive  
✅ Error handling  
✅ File cleanup  

## Tech Stack

- **Backend**: Flask (Python SSR)
- **AI**: Groq API (Whisper + LLaMA 3.3)
- **Video**: MoviePy + FFmpeg
- **Frontend**: HTML, CSS, JavaScript

## Next Steps

1. ✅ Set up the project (you are here!)
2. 🎥 Test with a sample video
3. 🚀 Use for your content creation
4. 📈 Scale to production (see QUICKSTART.md)

## Need Help?

1. Check `QUICKSTART.md` for detailed troubleshooting
2. Run `python test_setup.py` to verify setup
3. Review `PROJECT_SUMMARY.md` for features
4. Check `ARCHITECTURE.md` for technical details

## API Costs

**Groq is FREE** for:
- 30 requests/minute
- 14,400 requests/day

This is more than enough for personal/testing use!

## Common Use Cases

### Content Creators
Upload competitor videos → Get scripts for your brand

### Marketers
Analyze trending videos → Adapt style for your product

### Agencies
Batch process videos → Generate multiple variants

### Educators
Study successful videos → Learn what works

## Performance

- Upload: <5 seconds
- Audio extraction: 10-30 seconds
- Transcription: 20-60 seconds
- AI generation: 10-30 seconds
- **Total**: 1-2 minutes

## File Limits

- Max size: 100MB
- Formats: MP4, MOV, AVI, MKV, WEBM
- Length: Any (longer = slower processing)

## Privacy

- Videos stored temporarily
- Auto-deleted after processing
- No data retention
- Your API key = your control

---

## Ready to Start?

```bash
# Run the application
python app.py

# Open: http://localhost:5000
```

**That's it! You're ready to transform Instagram videos into custom scripts! 🎬✨**
