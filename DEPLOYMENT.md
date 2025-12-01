# Deployment Guide: Render.com

This guide walks you through deploying your Flask video processing app to Render.com.

## Prerequisites

- GitHub account with your code pushed to a repository
- Render.com account (sign up at https://render.com)
- FFmpeg buildpack enabled (required for MoviePy)

## Step-by-Step Deployment

### 1. Push Code to GitHub

First, ensure your code is pushed to GitHub:

```bash
git init
git add .
git commit -m "Initial commit: video stacking Flask app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

**Files that should be committed:**
- `app.py` - Flask application
- `vi.py` - Video processing module
- `requirements.txt` - Python dependencies
- `config.py` - Configuration management
- `Procfile` - Render startup command
- `.env.example` - Environment variables template (but NOT `.env`)
- `JScode/` - Frontend files (if using)
- `.gitignore` - Include: `uploads/`, `outputs/`, `.env`, `__pycache__/`, `.venv/`

### 2. Create a New Web Service on Render

1. Log in to [render.com](https://render.com)
2. Click **+ New** → Select **Web Service**
3. Choose **Deploy an existing Git repository**
4. Click **Connect** to link your GitHub account (first time only)
5. Select your repository from the list
6. Fill in the form:
   - **Name**: `video-stacking-app` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command (safe, recommended)**: `pip install -r requirements.txt`
   - **Start Command (no-gevent)**: `gunicorn --workers 4 --worker-class gthread --threads 4 --timeout 300 --bind 0.0.0.0:$PORT app:app`
   
   Note: `gevent` can require native system libraries (C compiler, libffi, etc.) to build on some hosts. If you prefer to use `gevent` for async workers, see the "Optional: Install system build deps for gevent" section below.
   - **Instance Type**: Start with "Free" tier (or "Standard" for production)
   - **Auto-deploy**: Yes (recommended)

### 3. Add Environment Variables

1. In the Render dashboard for your service, go to **Environment**
2. Add the following environment variables:

   | Key | Value | Notes |
   |-----|-------|-------|
   | `FLASK_ENV` | `production` | Required |
   | `SECRET_KEY` | `<generate random string>` | Use `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
   | `UPLOAD_FOLDER` | `uploads` | Should match your app |
   | `OUTPUT_FOLDER` | `outputs` | Should match your app |
   | `WORKERS` | `4` | Adjust based on dyno size |

3. Click **Save**

### 4. Add FFmpeg Buildpack

MoviePy requires FFmpeg to encode videos. Add it via build script:

**Option A: Modify Build Command (Recommended)**

Change your **Build Command** to:
```bash
apt-get update && apt-get install -y ffmpeg && pip install -r requirements.txt
```

**Optional: Install system build deps for `gevent` (only if you need gevent)**

If you want to use `gevent` workers on Render (instead of `gthread`), add the system-level build dependencies before `pip install` so `gevent` can compile. Add the following to your Build Command instead:

```bash
apt-get update && apt-get install -y build-essential libffi-dev python3-dev ffmpeg && pip install -r requirements.txt
```

Then change **Start Command** to:

```bash
gunicorn --workers 4 --worker-class gevent --worker-connections 1000 --timeout 300 --bind 0.0.0.0:$PORT app:app
```

Warning: installing system build packages may increase build time and requires that Render's base image supports apt; use this only if you need gevent-specific features.

**Option B: Use Render's Pre-built Buildpacks**

1. Go to **Environment** tab
2. Under **Buildpacks**, click **Add buildpack**
3. Search for `ffmpeg` and select the official buildpack
4. Ensure `pip install -r requirements.txt` is in your build command

### 5. Deploy

1. Click **Create Web Service**
2. Render will automatically start building and deploying
3. Monitor the logs in the **Logs** tab
4. Once deployment completes (you'll see "Your service is live at..."), your app is deployed!

### 6. Get Your Live URL

- Your app will be available at: `https://your-service-name.onrender.com`
- Share this URL with your web app to connect and process videos

## Testing Your Deployment

### Test via curl (Linux/Mac)

```bash
# Test form endpoint
curl https://your-service-name.onrender.com/

# Test upload
curl -F "meme_video=@test_meme.mp4" \
     -F "gameplay_video=@test_gameplay.mp4" \
     -F "caption=Test" \
     https://your-service-name.onrender.com/process
```

### Test via Python

```python
import requests

url = "https://your-service-name.onrender.com/process"
files = {
    'meme_video': open('test_meme.mp4', 'rb'),
    'gameplay_video': open('test_gameplay.mp4', 'rb'),
}
data = {'caption': 'Test Caption'}

response = requests.post(url, files=files, data=data)
print(response.json())  # Should return {'success': true, 'job_id': '...'}
```

## Integrating with Your Web App

### If Your Web App is on a Different Domain

The backend already includes CORS support. Calls from your web app should work automatically.

**Test from your web app:**
```javascript
const formData = new FormData();
formData.append('meme_video', memeFile);
formData.append('gameplay_video', gameplayFile);
formData.append('caption', 'Your Caption');

const response = await fetch('https://your-service-name.onrender.com/process', {
    method: 'POST',
    body: formData
});

const data = await response.json();
const jobId = data.job_id;

// Poll status
const statusResponse = await fetch(`https://your-service-name.onrender.com/status/${jobId}`);
const status = await statusResponse.json();
// status.preview_url and status.download_url ready when complete
```

## Troubleshooting

### Build Fails: "moviepy: command not found"

**Solution:** FFmpeg is not installed. Check that your build command includes FFmpeg installation or buildpack is added.

```bash
# Add to build command:
apt-get update && apt-get install -y ffmpeg && pip install -r requirements.txt
```

### Timeout Error: "504 Gateway Timeout"

**Solution:** Video processing takes too long. Increase timeout in Procfile:
```bash
gunicorn --workers 4 --worker-class gevent --timeout 600 --bind 0.0.0.0:$PORT app:app
```

Also consider upgrading to a larger instance type (free tier has limited CPU).

### Upload Fails: "413 Request Entity Too Large"

**Solution:** File size exceeds limit. Increase `MAX_CONTENT_LENGTH` in `config.py`:
```python
MAX_CONTENT_LENGTH = 1000 * 1024 * 1024  # 1GB instead of 500MB
```

### Cannot Connect from Web App: CORS Error

**Solution:** Browser blocks cross-origin requests. Check that your web app URL is in environment:

1. Add environment variable: `CORS_ORIGINS=https://your-web-app-domain.com`
2. Restart service

Or modify `app.py` to add CORS headers:
```python
from flask_cors import CORS
CORS(app, origins=['https://your-web-app-domain.com'])
```

### Video Processing Hangs / Never Completes

**Possible causes:**
- Codec issues → Ensure input videos are compatible MP4 format
- Memory limit → Upgrade instance type
- Audio issues → Check that top video has audio track

**Debug:** Check logs for FFmpeg errors:
```
# In Render logs, look for:
"Moviepy - Building video..."
```

## Performance Tips

### For Free Tier
- Keep input videos under 30 seconds
- Maximum concurrent uploads: 1-2 (due to single instance)
- Processing time: ~30-60 seconds per video pair

### For Standard/Pro Tier
- Increase workers: `--workers 8`
- Increase timeout if processing long videos
- Enable auto-scaling for multiple concurrent requests

### Auto-Scaling on Render

If you upgrade to Standard tier:
1. Set **Min Instances** to 1
2. Set **Max Instances** to 3-5 (adjust based on expected load)
3. Render will automatically scale based on CPU/memory

## Updating Your App

To deploy updates:

1. Make changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update video processing"
   git push origin main
   ```
3. Render automatically redeploys (if auto-deploy is enabled)

To manually trigger deployment:
1. Go to Render dashboard
2. Click **Redeploy** button

## Monitoring

### View Logs

1. In Render dashboard, click your service
2. Go to **Logs** tab
3. See real-time output

### Common Log Messages

```
INFO: Uvicorn running on 0.0.0.0:10000
# ↑ App started successfully

Moviepy - Building video...
Moviepy - Done!
# ↑ Video processing completed

ERROR: Address already in use
# ↑ Port conflict (should not happen on Render)
```

## Additional Resources

- [Render.com Docs](https://render.com/docs)
- [MoviePy Documentation](https://zulko.github.io/moviepy/)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/latest/settings.html)

## Security Considerations

1. **Change SECRET_KEY** → Generate a new key for production (not the default "dev-secret-key")
2. **Enable HTTPS** → Render provides free SSL certificates
3. **Validate Inputs** → Check file types and sizes before processing
4. **Rate Limiting** → Add rate limiting if you expect high traffic
5. **Hide Error Details** → Set `DEBUG=False` in production (already done in config.py)

## Support

If you encounter issues:
1. Check Render logs for error messages
2. Test locally: `FLASK_ENV=production python app.py`
3. Verify FFmpeg is installed: `ffmpeg -version`
4. Ensure all required environment variables are set
