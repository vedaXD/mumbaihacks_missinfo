# AI News Reel Generator

Generate vertical video reels (9:16) from news summaries using Google Vertex AI.

## Architecture

### Orchestrator Agent System
- **Script Generator Agent**: Uses Gemini 2.0 Flash to convert news summaries into structured scene scripts
- **Image Generator Agent**: Uses Imagen 4.0 Fast to create 9:16 images from scene descriptions
- **Video Composer Agent**: Combines images with synced TTS audio using Google Cloud TTS and MoviePy

### Tech Stack
- **Backend**: Flask (Python) with Google Cloud AI Platform
- **Frontend**: React + Vite with Axios
- **AI Models**: 
  - Gemini 2.0 Flash Exp (script generation)
  - Imagen 4.0 Fast (image generation - 9:16 aspect ratio)
  - Google Cloud Text-to-Speech (narration)
- **Storage**: Google Cloud Storage
- **Video Processing**: MoviePy + FFmpeg

## Quick Start

### 1. Install Dependencies

#### Backend (orchestrator_agent)
```bash
cd orchestrator_agent
pip install -r requirements.txt
```

#### Frontend (reel-frontend)
```bash
cd reel-frontend
npm install
```

### 2. Configure Environment

Edit `orchestrator_agent/.env`:
```env
GCP_PROJECT_ID=your-project-id
GCS_BUCKET_NAME=your-bucket-name
LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
```

### 3. Run Backend
```bash
cd orchestrator_agent
python api_server.py
```
Backend runs on http://localhost:5000

### 4. Run Frontend
```bash
cd reel-frontend
npm run dev
```
Frontend runs on http://localhost:3000

## API Endpoints

### POST /api/generate_reel
Generate a news reel from summary
```json
{
  "news_summary": "Your news text...",
  "num_scenes": 5
}
```

Returns:
```json
{
  "job_id": "uuid",
  "status": "processing"
}
```

### GET /api/job_status/{job_id}
Check generation progress
```json
{
  "status": "processing|completed|failed",
  "progress": 0-100,
  "current_step": "Description...",
  "video_url": "https://...",
  "scenes": [...]
}
```

## How It Works

1. **User Input**: Enter news summary in frontend
2. **Script Generation**: Gemini analyzes summary and creates scene-by-scene script with:
   - Image prompts (detailed visual descriptions)
   - Narration text (what to say)
   - Duration (how long to show)

3. **Image Generation**: Imagen generates 1080x1920 (9:16) images for each scene

4. **Audio Generation**: Google TTS converts narration to speech

5. **Video Composition**: MoviePy syncs images with audio:
   - Each image displays while its narration plays
   - Smooth transitions between scenes
   - Final output: MP4 video (9:16 vertical format)

6. **Cloud Storage**: Video uploaded to GCS with signed URL

7. **Frontend Display**: User can watch, download, and review scene breakdown

## Project Structure

```
orchestrator_agent/
├── sub_agents/
│   ├── script_generator_agent.py    # Gemini script generation
│   ├── image_generator_agent.py     # Imagen image creation
│   └── video_composer_agent.py      # Video + audio composition
├── utils/
│   └── gcs_storage.py              # Cloud storage handling
├── orchestrator_tool.py            # Main orchestrator
├── api_server.py                   # Flask API
├── requirements.txt
└── .env

reel-frontend/
├── src/
│   ├── App.jsx                     # Main React component
│   ├── App.css                     # Styling
│   ├── main.jsx                    # React entry point
│   └── index.css                   # Global styles
├── public/
├── index.html
├── vite.config.js                  # Vite configuration
└── package.json
```

## Features

✅ AI-powered script generation from news summaries  
✅ High-quality 9:16 vertical images optimized for reels  
✅ Synchronized audio narration  
✅ Automatic scene timing and transitions  
✅ Real-time progress tracking  
✅ Cloud storage with secure signed URLs  
✅ Scene-by-scene breakdown in UI  
✅ Video download capability  
✅ Responsive React frontend  

## Requirements

- Python 3.8+
- Node.js 18+
- FFmpeg (for video processing)
- Google Cloud account with:
  - Vertex AI API enabled
  - Cloud Storage API enabled
  - Text-to-Speech API enabled
  - Service account with proper permissions

## License

MIT
