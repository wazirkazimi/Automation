# Video Reel Creator 🎬

A Flask web application that stacks video clips (meme/content on top, gameplay on bottom) to create vertical reels for social media. Perfect for TikTok, Reels, and YouTube Shorts.

## Features

- 📤 Upload two video files (meme + gameplay)
- ✍️ Add optional captions
- 🎨 Automatic vertical stacking (1080×1920 - 9:16 aspect ratio)
- 📊 Real-time progress tracking
- 👁️ In-browser video preview
- 📥 Download processed video
- 📱 **Upload directly to Instagram Reels with caption**
- ⚡ Background job processing with threading
- 🚀 Cloud-ready (Render.com deployment)
- 🌐 CORS support for cross-domain web app integration

## Tech Stack

- **Backend:** Flask 3.0.0, Python 3.12.6
- **Video Processing:** MoviePy 1.0.3
- **Web Server:** Gunicorn 23.0.0 (production)
- **Async:** Gevent for concurrent request handling
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Image Processing:** Pillow 10.4.0

## Local Development

### Prerequisites

- Python 3.12+
- FFmpeg (for video encoding)
  - **Windows:** Install via `scoop install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org)
  - **macOS:** `brew install ffmpeg`
  - **Linux:** `apt-get install ffmpeg`

### Setup

1. **Clone and navigate:**
   ```bash
   cd Automation
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create .env file (optional for dev):**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (defaults work for development)
   ```

5. **Run the app:**
   ```bash
   python app.py
   ```

6. **Open in browser:**
   ```
   http://localhost:5000
   ```

## Project Structure

```
Automation/
├── app.py                 # Flask application
├── vi.py                  # Video stacking core logic
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── runtime.txt            # Python version for Render
├── Procfile               # Render deployment config
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
├── DEPLOYMENT.md          # Cloud deployment guide
├── README.md              # This file
├── JScode/                # Frontend assets (optional)
├── uploads/               # Temporary upload storage
├── outputs/               # Processed video output
└── __pycache__/           # Python cache
```

## API Endpoints

### `GET /`
Returns the HTML upload form and dashboard.

**Response:** HTML page

---

### `POST /process`
Upload videos and start processing.

**Request:**
```
Content-Type: multipart/form-data

Parameters:
- meme_video (file, required): Video file for top layer
- gameplay_video (file, required): Video file for bottom layer
- caption (string, optional): Text caption to overlay
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "job_id": "d28c0c4f0abf4effa9263afddc4fbddf"
}
```

---

### `GET /status/<job_id>`
Poll the status of a processing job.

**Response:**
```json
{
  "status": "processing",
  "progress": 45,
  "message": "Encoding video...",
  // When complete:
  "preview_url": "/preview/output_abc123.mp4",
  "download_url": "/download/output_abc123.mp4"
}
```

Status values: `queued`, `processing`, `done`, `error`

---

### `GET /preview/<filename>`
Stream video for browser preview.

**Response:** MP4 video stream

---

### `GET /download/<filename>`
Download processed video as attachment.

**Response:** MP4 file download

---

### `POST /upload-to-instagram/<job_id>`
Upload processed video to Instagram Reels.

**Request:**
```json
{
  "caption": "Your caption text here",
  "hashtags": "#gaming #memes #viral"
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Instagram upload started",
  "status": "uploading"
}
```

---

### `GET /instagram-status/<job_id>`
Get Instagram upload status for a job.

**Response:**
```json
{
  "instagram_status": "success",
  "instagram_url": "https://www.instagram.com/reel/ABC123/",
  "message": "Uploaded to Instagram!"
}
```

Status values: `uploading`, `success`, `failed`

## Video Processing

### Input Requirements
- **Format:** MP4, MOV, AVI, MKV, WEBM
- **Max Size:** 500 MB per file
- **Recommended:** H.264 codec, AAC audio

### Output Specifications
- **Resolution:** 1080×1920 (9:16 aspect ratio - vertical)
- **Codec:** H.264 (libx264)
- **Audio:** AAC (from meme/top video)
- **FPS:** 30
- **File Size:** ~100-300 MB (depends on input)

### Processing Steps
1. Load both input videos
2. Resize to 1080×960 each
3. Pad with black bars if needed
4. Stack vertically
5. Add caption overlay (if provided)
6. Encode with H.264 + AAC
7. Apply fast-start flag for streaming

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | Set to `production` for cloud |
| `SECRET_KEY` | `dev-secret-key-...` | Change in production |
| `UPLOAD_FOLDER` | `uploads` | Where uploads are stored |
| `OUTPUT_FOLDER` | `outputs` | Where output videos go |
| `WORKERS` | `4` | Gunicorn worker count |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |
| `PORT` | `5000` | Server port |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | - | Instagram Business Account ID (required for Instagram upload) |
| `INSTAGRAM_ACCESS_TOKEN` | - | Instagram Graph API access token (required for Instagram upload) |
| `PUBLIC_VIDEO_URL` | - | Public base URL for video access (e.g., `https://yourdomain.com`) |

### Create .env file for custom settings:
```bash
FLASK_ENV=development
FLASK_APP=app.py
SECRET_KEY=your-random-secret-key-here
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Instagram API Configuration (optional - required for Instagram upload feature)
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_business_account_id
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
PUBLIC_VIDEO_URL=https://yourdomain.com
```

### Instagram API Setup

To enable Instagram Reels upload functionality:

1. **Create a Facebook App:**
   - Go to [Facebook Developers](https://developers.facebook.com/)
   - Create a new app or use an existing one
   - Add "Instagram Graph API" product

2. **Get Instagram Business Account ID:**
   - Connect your Instagram Business account to your Facebook Page
   - Get your Instagram Business Account ID from the Graph API Explorer

3. **Generate Access Token:**
   - Use Graph API Explorer to generate a long-lived access token
   - Required permissions: `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`

4. **Set Public Video URL:**
   - Instagram requires videos to be accessible via a public URL
   - Set `PUBLIC_VIDEO_URL` to your server's public domain (e.g., `https://yourdomain.com`)
   - The app will construct video URLs as: `{PUBLIC_VIDEO_URL}/preview/{filename}`

**Note:** For local development, you may need to use a tunneling service (like ngrok) to make your local server publicly accessible for Instagram to download the video.

## Usage Examples

### Python Requests
```python
import requests

url = 'http://localhost:5000/process'
files = {
    'meme_video': open('meme.mp4', 'rb'),
    'gameplay_video': open('gameplay.mp4', 'rb'),
}
data = {'caption': 'Check this out! 🎮'}

response = requests.post(url, files=files, data=data)
job_id = response.json()['job_id']

# Poll status
import time
while True:
    status = requests.get(f'http://localhost:5000/status/{job_id}').json()
    print(f"Progress: {status['progress']}%")
    if status['status'] == 'done':
        print(f"Download: {status['download_url']}")
        break
    time.sleep(1)
```

### JavaScript/Fetch
```javascript
const formData = new FormData();
formData.append('meme_video', memeFile);
formData.append('gameplay_video', gameplayFile);
formData.append('caption', 'My awesome reel!');

const response = await fetch('/process', {
    method: 'POST',
    body: formData
});

const { job_id } = await response.json();

// Poll for completion
const pollStatus = async () => {
    const status = await fetch(`/status/${job_id}`).then(r => r.json());
    console.log(`Progress: ${status.progress}%`);
    
    if (status.status === 'done') {
        console.log('Video ready:', status.preview_url);
        // Download or preview
    } else if (status.status === 'error') {
        console.error('Processing failed:', status.error);
    } else {
        setTimeout(pollStatus, 1000);
    }
};

pollStatus();
```

## Troubleshooting

### "No such file or directory: ffmpeg"
**Solution:** FFmpeg not installed or not in PATH
```bash
# Windows (via scoop)
scoop install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg
```

### "413 Request Entity Too Large"
**Solution:** Increase `MAX_CONTENT_LENGTH` in `config.py` or `.env`

### Video processing hangs or times out
**Solution:** 
- Use shorter videos (under 30 seconds recommended)
- Upgrade to faster machine/cloud instance
- Increase timeout in Procfile: `--timeout 600`

### CORS errors when calling from web app
**Solution:** Set `CORS_ORIGINS` environment variable:
```bash
CORS_ORIGINS=https://your-web-app.com,http://localhost:3000
```

### Output video has no audio
**Solution:** Ensure meme/top video has audio track. The app uses audio from the top video.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive cloud deployment guide including:
- Render.com setup (recommended)
- GitHub integration
- FFmpeg buildpack configuration
- Environment variable setup
- Troubleshooting

**Quick Render Deploy:**
1. Push to GitHub
2. Create new Web Service on Render.com
3. Connect GitHub repo
4. Add FFmpeg to build command: `apt-get update && apt-get install -y ffmpeg && pip install -r requirements.txt`
5. Deploy!

## Performance

- **Free Tier (Render):** ~30-60 seconds per video pair
- **Standard Tier:** ~15-30 seconds per video pair
- **Local Desktop:** ~10-20 seconds per video pair

Processing time depends on:
- Input video duration
- Input file sizes
- System CPU/memory
- Network I/O (cloud only)

## Architecture

### Background Job Processing
- Uses Python `threading` for async job execution
- Client receives `job_id` immediately (HTTP 202)
- Client polls `/status/<job_id>` for progress
- Progress callback updates job state in real-time
- Job state stored in `app.config['JOBS']` dictionary

### Video Processing Pipeline
```
Input Videos → Load Clips → Resize/Pad → Composite Stack → 
Add Caption → Encode H.264 → Write MP4 → Stream/Download
```

### Frontend Architecture
- Single-page form with HTML5 file inputs
- Real-time progress bar (updates from server, not fake animation)
- HTML5 `<video>` element for preview
- Download button with auto-cleanup option
- Mobile-responsive design

## Security Considerations

1. **File Validation:** Only accepts video MIME types
2. **File Size Limits:** 500 MB per file (configurable)
3. **Filename Sanitization:** Uses `secure_filename()` from Werkzeug
4. **CORS Restrictions:** Configure `CORS_ORIGINS` for production
5. **Secret Key:** Must be set via environment variable in production
6. **Error Handling:** Detailed errors in development, generic in production

## Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and test locally
4. Commit (`git commit -m 'Add amazing feature'`)
5. Push (`git push origin feature/amazing-feature`)
6. Open Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues, feature requests, or questions:
- Open an issue on GitHub
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment issues
- Review logs for debugging: `docker logs` (if containerized) or `tail -f *.log`

## Roadmap

- [x] Instagram Reels upload with caption
- [ ] Add fade transitions between clips
- [ ] Support audio overlay/mixing
- [ ] Add watermark option
- [ ] Batch processing API
- [ ] S3 cloud storage for outputs
- [ ] Advanced caption styling
- [ ] Multiple stacking layouts
- [ ] Compression optimization

## Acknowledgments

- [MoviePy](https://zulko.github.io/moviepy/) - Video processing
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Render.com](https://render.com/) - Cloud hosting
- [FFmpeg](https://ffmpeg.org/) - Video encoding

---

**Made with ❤️ for content creators**
