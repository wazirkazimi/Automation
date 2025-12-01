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
from pathlib import Path
from dotenv import load_dotenv
from config import get_config
from vi import stack_videos


# Load environment variables
load_dotenv()

# Create app with config
flask_env = os.getenv('FLASK_ENV', 'development')
config_obj = get_config(flask_env)

app = Flask(__name__)
app.config.from_object(config_obj)

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
                <textarea name="caption" placeholder="Add a caption for your reel..."></textarea>
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
            form.reset();
            document.getElementById('meme-info').textContent = '';
            document.getElementById('gameplay-info').textContent = '';
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
            'error': None
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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = app.config.get('DEBUG', False)
    print(f"🚀 Starting Video Reel Creator on http://localhost:{port}")
    print(f"Environment: {app.config.get('ENV', 'development')}")
    app.run(debug=debug, host='0.0.0.0', port=port)
