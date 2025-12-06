"""
Flask web app for video stacking with upload form, progress tracking, and dashboard.
Upload meme video, gameplay video, and caption, then preview and download the stacked output.
"""

from flask import Flask, render_template_string, request, send_file, jsonify
from flask_cors import CORS  # type: ignore
from werkzeug.utils import secure_filename
import threading
import uuid
import time
import os
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv
from config import get_config
from vi import stack_videos


# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create app with config
flask_env = os.getenv('FLASK_ENV', 'development')
config_obj = get_config(flask_env)

app = Flask(__name__)
app.config.from_object(config_obj)

# Instagram API Configuration
INSTAGRAM_CONFIG = {
    'BUSINESS_ACCOUNT_ID': os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID', ''),
    'ACCESS_TOKEN': os.getenv('INSTAGRAM_ACCESS_TOKEN', ''),
    'PUBLIC_VIDEO_URL': os.getenv('PUBLIC_VIDEO_URL', '')  # Base URL for public video access
}

# Add CORS support for web app integration
CORS(app, origins=os.getenv('CORS_ORIGINS', '*').split(','))

# Setup folders
UPLOAD_FOLDER = Path(app.config.get('UPLOAD_FOLDER', 'uploads'))
OUTPUT_FOLDER = Path(app.config.get('OUTPUT_FOLDER', 'outputs'))
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

UPLOAD_FOLDER.mkdir(exist_ok=True, parents=True)
OUTPUT_FOLDER.mkdir(exist_ok=True, parents=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['JOBS'] = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class InstagramAPI:
    """Handle Instagram Graph API operations for uploading reels"""
    
    @staticmethod
    def upload_reel(video_url, caption, access_token=None, account_id=None):
        """
        Upload reel to Instagram using Graph API
        
        Args:
            video_url: Publicly accessible URL to the video file
            caption: Caption text for the reel
            access_token: Instagram access token (optional, uses config if not provided)
            account_id: Instagram Business Account ID (optional, uses config if not provided)
        
        Returns:
            tuple: (success: bool, result: str or error message)
        """
        try:
            access_token = access_token or INSTAGRAM_CONFIG['ACCESS_TOKEN']
            account_id = account_id or INSTAGRAM_CONFIG['BUSINESS_ACCOUNT_ID']
            
            if not access_token or not account_id:
                return False, "Instagram credentials not configured. Please set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ACCOUNT_ID environment variables."
            
            logger.info("Creating Instagram media container...")
            create_url = f"https://graph.facebook.com/v21.0/{account_id}/media"
            
            payload = {
                'video_url': video_url,
                'media_type': 'REELS',
                'caption': caption,
                'share_to_feed': True,
                'access_token': access_token
            }
            
            response = requests.post(create_url, data=payload, timeout=30)
            
            if response.status_code != 200:
                error_data = response.json().get('error', {})
                error_msg = error_data.get('message', 'Unknown error')
                logger.error(f"Failed to create container: {error_msg}")
                return False, f"Instagram API error: {error_msg}"
            
            container_id = response.json().get('id')
            if not container_id:
                return False, "Failed to get container ID from Instagram API"
            
            logger.info(f"Container created: {container_id}")
            
            # Poll for status
            logger.info("Waiting for Instagram to process video...")
            max_attempts = 60  # 10 minutes max (60 * 10 seconds)
            for attempt in range(max_attempts):
                status_url = f"https://graph.facebook.com/v21.0/{container_id}"
                status_response = requests.get(
                    status_url,
                    params={
                        'fields': 'status_code,status',
                        'access_token': access_token
                    },
                    timeout=10
                )
                
                if status_response.status_code != 200:
                    return False, f"Failed to check status: {status_response.text}"
                
                status_data = status_response.json()
                status_code = status_data.get('status_code')
                
                if status_code == 'FINISHED':
                    logger.info("Video processing finished")
                    break
                elif status_code == 'ERROR':
                    error_msg = status_data.get('status', 'Unknown error')
                    logger.error(f"Instagram processing error: {error_msg}")
                    return False, f"Instagram processing error: {error_msg}"
                
                time.sleep(10)
            else:
                return False, "Timeout waiting for Instagram to process video"
            
            # Publish
            logger.info("Publishing reel...")
            publish_url = f"https://graph.facebook.com/v21.0/{account_id}/media_publish"
            publish_response = requests.post(
                publish_url,
                data={
                    'creation_id': container_id,
                    'access_token': access_token
                },
                timeout=30
            )
            
            if publish_response.status_code != 200:
                error_data = publish_response.json().get('error', {})
                error_msg = error_data.get('message', publish_response.text)
                logger.error(f"Failed to publish: {error_msg}")
                return False, f"Failed to publish reel: {error_msg}"
            
            publish_data = publish_response.json()
            media_id = publish_data.get('id')
            
            if not media_id:
                return False, "Failed to get media ID after publishing"
            
            instagram_url = f"https://www.instagram.com/reel/{media_id}/"
            
            logger.info(f"✅ Reel published: {instagram_url}")
            return True, instagram_url
            
        except requests.exceptions.Timeout:
            logger.error("Instagram API timeout")
            return False, "Request timeout - Instagram API took too long to respond"
        except requests.exceptions.RequestException as e:
            logger.error(f"Instagram API request error: {e}")
            return False, f"Network error: {str(e)}"
        except Exception as e:
            logger.error(f"Instagram upload exception: {e}")
            return False, str(e)

# HTML Form
HTML_FORM = '''
<!DOCTYPE html>
<html>
<head>
    <title>Video Reel Creator</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 700px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        h2 {
            color: #333;
            font-size: 20px;
            margin-bottom: 15px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 25px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }
        input[type="file"] {
            display: block;
            width: 100%;
            padding: 12px;
            border: 2px dashed #ddd;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        input[type="file"]:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }
        textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border 0.3s;
            font-family: inherit;
            resize: vertical;
            min-height: 100px;
        }
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .file-info {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        .progress-container {
            display: none;
            margin-top: 20px;
        }
        .progress-bar {
            width: 100%;
            height: 12px;
            background: #e0e0e0;
            border-radius: 6px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.3s;
        }
        .progress-text {
            font-size: 13px;
            color: #666;
            margin-top: 10px;
            text-align: center;
            font-weight: 500;
        }
        .dashboard {
            display: none;
            margin-top: 20px;
        }
        .video-preview {
            width: 100%;
            border-radius: 8px;
            margin-bottom: 20px;
            background: #000;
            max-height: 600px;
        }
        .dashboard-buttons {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .dashboard-buttons button {
            flex: 1;
        }
        .secondary-btn {
            background: #6c757d !important;
        }
        .secondary-btn:hover {
            box-shadow: 0 5px 20px rgba(108, 117, 125, 0.4) !important;
        }
        .error-msg {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            display: none;
        }
        .instagram-section {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            display: none;
        }
        .instagram-btn {
            background: linear-gradient(135deg, #E4405F 0%, #C13584 100%) !important;
            margin-top: 10px;
        }
        .instagram-status {
            margin-top: 10px;
            padding: 10px;
            border-radius: 6px;
            font-size: 14px;
            display: none;
        }
        .instagram-status.uploading {
            background: #d1ecf1;
            color: #0c5460;
        }
        .instagram-status.success {
            background: #d4edda;
            color: #155724;
        }
        .instagram-status.error {
            background: #f8d7da;
            color: #721c24;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border 0.3s;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 Video Reel Creator</h1>
        <p class="subtitle">Upload meme + gameplay videos to create a stacked reel</p>
        
        <form id="uploadForm" enctype="multipart/form-data">
            <div class="form-group">
                <label>😂 Meme/Content Video (Top)</label>
                <input type="file" name="meme_video" id="meme" accept="video/*" required>
                <div class="file-info" id="meme-info"></div>
            </div>
            
            <div class="form-group">
                <label>🎮 Gameplay Video (Bottom)</label>
                <input type="file" name="gameplay_video" id="gameplay" accept="video/*" required>
                <div class="file-info" id="gameplay-info"></div>
            </div>
            
            <div class="form-group">
                <label>✍️ Caption (Optional)</label>
                <textarea name="caption" id="captionInput" placeholder="Add a caption for your reel..."></textarea>
            </div>
            
            <div class="form-group">
                <label>🏷️ Hashtags (Optional)</label>
                <input type="text" name="hashtags" id="hashtagsInput" placeholder="#gaming #memes #viral">
            </div>
            
            <button type="submit" id="submitBtn">🚀 Create Video</button>
        </form>
        
        <!-- Progress Bar -->
        <div class="progress-container" id="progressContainer">
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="progress-text">
                <span id="progressText">Processing your video...</span>
            </div>
        </div>
        
        <!-- Dashboard -->
        <div class="dashboard" id="dashboard">
            <h2>✅ Video Created Successfully!</h2>
            <video class="video-preview" id="videoPreview" controls>
                <source id="videoSource" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            <div class="dashboard-buttons">
                <button onclick="downloadVideo()">📥 Download</button>
                <button class="secondary-btn" onclick="createAnother()">➕ Create Another</button>
            </div>
            
            <!-- Instagram Upload Section -->
            <div class="instagram-section" id="instagramSection">
                <h3 style="margin-bottom: 15px; color: #333;">📱 Upload to Instagram</h3>
                <div class="form-group" style="margin-bottom: 15px;">
                    <label>✍️ Caption for Instagram</label>
                    <textarea id="instagramCaption" placeholder="Add a caption for Instagram..."></textarea>
                </div>
                <div class="form-group" style="margin-bottom: 15px;">
                    <label>🏷️ Hashtags</label>
                    <input type="text" id="instagramHashtags" placeholder="#gaming #memes #viral">
                </div>
                <button class="instagram-btn" onclick="uploadToInstagram()" id="instagramUploadBtn">
                    📤 Upload to Instagram
                </button>
                <div class="instagram-status" id="instagramStatus"></div>
            </div>
        </div>
        
        <div class="error-msg" id="errorMsg"></div>
    </div>
    
    <script>
        const form = document.getElementById('uploadForm');
        const submitBtn = document.getElementById('submitBtn');
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const dashboard = document.getElementById('dashboard');
        const videoPreview = document.getElementById('videoPreview');
        const videoSource = document.getElementById('videoSource');
        const errorMsg = document.getElementById('errorMsg');
        
        let currentDownloadUrl = '';
        let currentJobId = '';
        let progressInterval;
        
        document.getElementById('meme').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                document.getElementById('meme-info').textContent = 
                    `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
            }
        });
        
        document.getElementById('gameplay').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                document.getElementById('gameplay-info').textContent = 
                    `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
            }
        });
        
        form.onsubmit = async (e) => {
            e.preventDefault();
            
            errorMsg.style.display = 'none';
            dashboard.style.display = 'none';
            progressContainer.style.display = 'block';
            progressFill.style.width = '0%';
            submitBtn.disabled = true;
            
            const formData = new FormData(form);
            
            // Start a short simulated spinner while we get a job id
            let fakeProgress = 0;
            progressInterval = setInterval(() => {
                if (fakeProgress < 20) {
                    fakeProgress += Math.random() * 6;
                    progressFill.style.width = Math.min(fakeProgress, 20) + '%';
                }
            }, 300);

            try {
                // Debug: Log fetch attempt
                console.log('Sending request to /process...');
                
                const response = await fetch('/process', {
                    method: 'POST',
                    body: formData
                });

                console.log('Response status:', response.status);

                if (!response.ok) {
                    const err = await response.json().catch(() => ({ error: 'Unknown error' }));
                    throw new Error(err.error || `Server error: ${response.status}`);
                }

                const data = await response.json();
                console.log('Response data:', data);
                clearInterval(progressInterval);

                if (data.success && data.job_id) {
                    // Poll the status endpoint for updates
                    const jobId = data.job_id;
                    currentJobId = jobId;
                    console.log('Job ID received:', jobId);
                    progressFill.style.width = '20%';
                    progressText.textContent = 'Queued';

                    const poll = setInterval(async () => {
                        try {
                            const st = await fetch(`/status/${jobId}`);
                            const js = await st.json();
                            console.log('Status:', js);
                            
                            if (js.error) {
                                clearInterval(poll);
                                progressContainer.style.display = 'none';
                                errorMsg.textContent = `❌ ${js.error}`;
                                errorMsg.style.display = 'block';
                                submitBtn.disabled = false;
                                return;
                            }
                            const pct = Math.min(Math.max(parseInt(js.progress || 0), 0), 100);
                            progressFill.style.width = pct + '%';
                            progressText.textContent = js.message || js.status || 'Processing';

                            if (js.status === 'done') {
                                clearInterval(poll);
                                // finalize and show dashboard
                                progressFill.style.width = '100%';
                                progressText.textContent = '✅ Complete!';
                                setTimeout(() => {
                                    progressContainer.style.display = 'none';
                                    currentDownloadUrl = js.download_url;
                                    videoSource.src = js.preview_url;
                                    videoPreview.load();
                                    dashboard.style.display = 'block';
                                    
                                    // Show Instagram section and populate caption/hashtags
                                    const instagramSection = document.getElementById('instagramSection');
                                    instagramSection.style.display = 'block';
                                    const captionInput = document.getElementById('captionInput');
                                    const hashtagsInput = document.getElementById('hashtagsInput');
                                    if (captionInput && captionInput.value) {
                                        document.getElementById('instagramCaption').value = captionInput.value;
                                    }
                                    if (hashtagsInput && hashtagsInput.value) {
                                        document.getElementById('instagramHashtags').value = hashtagsInput.value;
                                    }
                                    
                                    submitBtn.disabled = false;
                                }, 400);
                            } else if (js.status === 'error') {
                                clearInterval(poll);
                                progressContainer.style.display = 'none';
                                errorMsg.textContent = `❌ ${js.error || 'Processing error'}`;
                                errorMsg.style.display = 'block';
                                submitBtn.disabled = false;
                            }
                        } catch (err) {
                            clearInterval(poll);
                            progressContainer.style.display = 'none';
                            console.error('Status polling error:', err);
                            errorMsg.textContent = `❌ Status error: ${err.message}`;
                            errorMsg.style.display = 'block';
                            submitBtn.disabled = false;
                        }
                    }, 1000);

                    // reset form fields visually
                    form.reset();
                    document.getElementById('meme-info').textContent = '';
                    document.getElementById('gameplay-info').textContent = '';
                } else {
                    progressContainer.style.display = 'none';
                    errorMsg.textContent = `❌ ${data.error || 'Unknown error - check browser console'}`;
                    errorMsg.style.display = 'block';
                    submitBtn.disabled = false;
                }
            } catch (error) {
                clearInterval(progressInterval);
                progressContainer.style.display = 'none';
                console.error('Fetch error:', error);
                
                // More helpful error messages
                let msg = error.message;
                if (msg.includes('Failed to fetch')) {
                    msg = 'Cannot connect to server. Make sure Flask is running on http://localhost:5000';
                }
                
                errorMsg.textContent = `❌ Error: ${msg}`;
                errorMsg.style.display = 'block';
                submitBtn.disabled = false;
            }
        };
        
        function downloadVideo() {
            if (currentDownloadUrl) {
                window.location.href = currentDownloadUrl;
            }
        }
        
        function createAnother() {
            progressContainer.style.display = 'none';
            dashboard.style.display = 'none';
            errorMsg.style.display = 'none';
            document.getElementById('instagramSection').style.display = 'none';
            document.getElementById('instagramStatus').style.display = 'none';
            form.reset();
            document.getElementById('meme-info').textContent = '';
            document.getElementById('gameplay-info').textContent = '';
            currentJobId = '';
            currentDownloadUrl = '';
        }
        
        async function uploadToInstagram() {
            if (!currentJobId) {
                alert('No video available to upload');
                return;
            }
            
            const uploadBtn = document.getElementById('instagramUploadBtn');
            const statusDiv = document.getElementById('instagramStatus');
            const caption = document.getElementById('instagramCaption').value.trim();
            const hashtags = document.getElementById('instagramHashtags').value.trim();
            
            // Disable button
            uploadBtn.disabled = true;
            uploadBtn.textContent = '⏳ Uploading...';
            
            // Show status
            statusDiv.className = 'instagram-status uploading';
            statusDiv.style.display = 'block';
            statusDiv.textContent = 'Uploading to Instagram... This may take a few minutes.';
            
            try {
                const response = await fetch(`/upload-to-instagram/${currentJobId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        caption: caption,
                        hashtags: hashtags
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Poll for Instagram upload status
                    const pollInterval = setInterval(async () => {
                        try {
                            const statusResponse = await fetch(`/instagram-status/${currentJobId}`);
                            const statusData = await statusResponse.json();
                            
                            if (statusData.instagram_status === 'success') {
                                clearInterval(pollInterval);
                                statusDiv.className = 'instagram-status success';
                                statusDiv.innerHTML = `✅ Successfully uploaded to Instagram!<br><a href="${statusData.instagram_url}" target="_blank" style="color: #155724; text-decoration: underline;">View on Instagram</a>`;
                                uploadBtn.disabled = true;
                                uploadBtn.textContent = '✅ Uploaded';
                            } else if (statusData.instagram_status === 'failed') {
                                clearInterval(pollInterval);
                                statusDiv.className = 'instagram-status error';
                                statusDiv.textContent = `❌ Upload failed: ${statusData.instagram_error || 'Unknown error'}`;
                                uploadBtn.disabled = false;
                                uploadBtn.textContent = '📤 Upload to Instagram';
                            } else if (statusData.instagram_status === 'uploading') {
                                statusDiv.textContent = statusData.message || 'Uploading to Instagram...';
                            }
                        } catch (err) {
                            console.error('Status polling error:', err);
                        }
                    }, 2000); // Poll every 2 seconds
                    
                    // Stop polling after 10 minutes
                    setTimeout(() => {
                        clearInterval(pollInterval);
                    }, 600000);
                } else {
                    statusDiv.className = 'instagram-status error';
                    statusDiv.textContent = `❌ ${data.error || 'Upload failed'}`;
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = '📤 Upload to Instagram';
                }
            } catch (error) {
                statusDiv.className = 'instagram-status error';
                statusDiv.textContent = `❌ Error: ${error.message}`;
                uploadBtn.disabled = false;
                uploadBtn.textContent = '📤 Upload to Instagram';
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Serve the upload form."""
    return render_template_string(HTML_FORM)

@app.route('/process', methods=['POST'])
def process_video():
    """Process uploaded videos and return the stacked output."""
    try:
        # Validate files
        if 'meme_video' not in request.files or 'gameplay_video' not in request.files:
            return jsonify({'success': False, 'error': 'Both meme and gameplay videos are required'}), 400
        
        meme_file = request.files['meme_video']
        gameplay_file = request.files['gameplay_video']
        caption = request.form.get('caption', '').strip()
        
        if not meme_file.filename or not gameplay_file.filename:
            return jsonify({'success': False, 'error': 'Please select both videos'}), 400
        
        if not allowed_file(meme_file.filename):
            return jsonify({'success': False, 'error': 'Invalid meme video format'}), 400
        
        if not allowed_file(gameplay_file.filename):
            return jsonify({'success': False, 'error': 'Invalid gameplay video format'}), 400
        
        # Save uploaded files
        meme_filename = secure_filename(f"meme_{os.urandom(8).hex()}.mp4")
        gameplay_filename = secure_filename(f"gameplay_{os.urandom(8).hex()}.mp4")
        
        meme_path = app.config['UPLOAD_FOLDER'] / meme_filename
        gameplay_path = app.config['UPLOAD_FOLDER'] / gameplay_filename
        
        meme_file.save(str(meme_path))
        gameplay_file.save(str(gameplay_path))
        # Create a job and start background processing thread
        job_id = uuid.uuid4().hex
        output_filename = f"output_{uuid.uuid4().hex}.mp4"
        output_path = str(app.config['OUTPUT_FOLDER'] / output_filename)

        # Initialize job state
        app.config['JOBS'][job_id] = {
            'status': 'queued',
            'progress': 0,
            'message': 'Queued',
            'output_filename': output_filename,
            'error': None,
            'caption': caption,
            'instagram_status': None,
            'instagram_url': None
        }

        def progress_cb(pct, msg=''):
            app.config['JOBS'][job_id]['progress'] = int(pct)
            app.config['JOBS'][job_id]['message'] = msg
            app.config['JOBS'][job_id]['status'] = 'processing' if int(pct) < 100 else 'done'

        def run_job():
            try:
                app.config['JOBS'][job_id]['status'] = 'processing'
                app.config['JOBS'][job_id]['message'] = 'Starting'
                stack_videos(str(meme_path), str(gameplay_path), output_path, caption, progress_callback=progress_cb)
                app.config['JOBS'][job_id]['status'] = 'done'
                app.config['JOBS'][job_id]['progress'] = 100
                app.config['JOBS'][job_id]['message'] = 'Completed'
            except Exception as e:
                app.config['JOBS'][job_id]['status'] = 'error'
                app.config['JOBS'][job_id]['error'] = str(e)
                app.config['JOBS'][job_id]['message'] = 'Error'
            finally:
                # Attempt to remove uploads
                try:
                    meme_path.unlink()
                    gameplay_path.unlink()
                except Exception:
                    pass

        thread = threading.Thread(target=run_job, daemon=True)
        thread.start()

        # Return job id immediately
        return jsonify({'success': True, 'job_id': job_id}), 202
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Processing error: {str(e)}'}), 500


@app.route('/status/<job_id>')
def job_status(job_id):
    job = app.config['JOBS'].get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    # If done, include preview/download urls
    data = {
        'status': job.get('status'),
        'progress': job.get('progress', 0),
        'message': job.get('message', ''),
    }
    if job.get('status') == 'done':
        data['preview_url'] = f"/preview/{job['output_filename']}"
        data['download_url'] = f"/download/{job['output_filename']}"
        # Include Instagram status only if it's been set (not None)
        instagram_status = job.get('instagram_status')
        if instagram_status is not None:
            data['instagram_status'] = instagram_status
            if job.get('instagram_url'):
                data['instagram_url'] = job.get('instagram_url')
    if job.get('status') == 'error':
        data['error'] = job.get('error')
    return jsonify(data)

@app.route('/preview/<filename>')
def preview_video(filename):
    """Stream video for preview."""
    try:
        filepath = app.config['OUTPUT_FOLDER'] / secure_filename(filename)
        if not filepath.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(str(filepath), mimetype='video/mp4')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_video(filename):
    """Download processed video."""
    try:
        file_path = app.config['OUTPUT_FOLDER'] / secure_filename(filename)
        if not file_path.exists():
            return "File not found", 404
        return send_file(str(file_path), as_attachment=True, download_name=filename, mimetype='video/mp4')
    except Exception as e:
        return f"Download error: {str(e)}", 500


@app.route('/upload-to-instagram/<job_id>', methods=['POST'])
def upload_to_instagram(job_id):
    """Upload processed video to Instagram"""
    try:
        job = app.config['JOBS'].get(job_id)
        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404
        
        if job.get('status') != 'done':
            return jsonify({'success': False, 'error': 'Video processing not complete yet'}), 400
        
        # Get caption from request or use stored caption
        caption = request.json.get('caption', '') if request.is_json else request.form.get('caption', '')
        if not caption:
            caption = job.get('caption', '')
        
        # Get hashtags if provided
        hashtags = request.json.get('hashtags', '') if request.is_json else request.form.get('hashtags', '')
        if hashtags:
            caption = f"{caption}\n\n{hashtags}" if caption else hashtags
        
        # Build public video URL
        output_filename = job['output_filename']
        public_url = INSTAGRAM_CONFIG['PUBLIC_VIDEO_URL']
        
        if not public_url:
            # Try to construct from request
            scheme = request.scheme
            host = request.host
            public_url = f"{scheme}://{host}"
        
        video_url = f"{public_url}/preview/{output_filename}"
        
        # Update job status
        job['instagram_status'] = 'uploading'
        job['message'] = 'Uploading to Instagram...'
        
        # Upload to Instagram in background
        def upload_job():
            try:
                success, result = InstagramAPI.upload_reel(video_url, caption)
                if success:
                    job['instagram_status'] = 'success'
                    job['instagram_url'] = result
                    job['message'] = 'Uploaded to Instagram!'
                else:
                    job['instagram_status'] = 'failed'
                    job['instagram_error'] = result
                    job['message'] = f'Instagram upload failed: {result}'
            except Exception as e:
                job['instagram_status'] = 'failed'
                job['instagram_error'] = str(e)
                job['message'] = f'Instagram upload error: {str(e)}'
        
        thread = threading.Thread(target=upload_job, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Instagram upload started',
            'status': 'uploading'
        }), 202
    
    except Exception as e:
        logger.error(f"Instagram upload endpoint error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/instagram-status/<job_id>')
def instagram_status(job_id):
    """Get Instagram upload status for a job"""
    try:
        job = app.config['JOBS'].get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify({
            'instagram_status': job.get('instagram_status'),
            'instagram_url': job.get('instagram_url'),
            'instagram_error': job.get('instagram_error'),
            'message': job.get('message', '')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = app.config.get('DEBUG', False)
    print(f"🚀 Starting Video Reel Creator on http://localhost:{port}")
    print(f"Environment: {app.config.get('ENV', 'development')}")
    app.run(debug=debug, host='0.0.0.0', port=port)