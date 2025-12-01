"""
Instagram Reel Automation - Production Ready
Uses FFmpeg directly for better reliability and performance
"""

import os
import time
import json
import subprocess
import requests
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler
import threading
from pathlib import Path
from datetime import datetime
import logging
from werkzeug.utils import secure_filename

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instagram_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration (Use environment variables in production)
CONFIG = {
    'INSTAGRAM_BUSINESS_ACCOUNT_ID': os.getenv('IG_BUSINESS_ACCOUNT_ID', 'your_id'),
    'INSTAGRAM_ACCESS_TOKEN': os.getenv('IG_ACCESS_TOKEN', 'your_token'),
    'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', 'your_token'),
    'TELEGRAM_ADMIN_CHAT_ID': os.getenv('TELEGRAM_ADMIN_CHAT_ID', 'your_chat_id'),
    'UPLOAD_FOLDER': 'uploads',
    'PROCESSED_FOLDER': 'processed',
    'PUBLIC_VIDEO_URL': os.getenv('PUBLIC_VIDEO_URL', 'http://localhost:5000/videos/'),
    'HOST': '0.0.0.0',
    'PORT': 5000,
    'MAX_FILE_SIZE': 100 * 1024 * 1024,  # 100MB
    'ALLOWED_EXTENSIONS': {'mp4', 'mov', 'avi', 'mkv', 'webm'}
}

# Create necessary folders
Path(CONFIG['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(CONFIG['PROCESSED_FOLDER']).mkdir(exist_ok=True)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = CONFIG['MAX_FILE_SIZE']

# Initialize Telegram bot
try:
    telegram_bot = Bot(token=CONFIG['TELEGRAM_BOT_TOKEN'])
    logger.info("✅ Telegram bot initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize Telegram bot: {e}")
    telegram_bot = None

# Store pending approvals
pending_approvals = {}

# HTML Form
HTML_FORM = '''
<!DOCTYPE html>
<html>
<head>
    <title>Instagram Reel Automation</title>
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
            max-width: 600px;
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
        .subtitle {
            color: #666;
            margin-bottom: 30px;
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
        input[type="text"], textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border 0.3s;
        }
        input[type="text"]:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        textarea {
            resize: vertical;
            min-height: 100px;
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
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            display: none;
        }
        .success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .loading {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        .loader {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            display: inline-block;
            margin-right: 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .file-info {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Instagram Reel Uploader</h1>
        <p class="subtitle">Upload your gameplay + meme videos</p>
        
        <form id="uploadForm" enctype="multipart/form-data">
            <div class="form-group">
                <label>🎮 Gameplay Video (Bottom)</label>
                <input type="file" name="gameplay_video" id="gameplay" accept="video/*" required>
                <div class="file-info" id="gameplay-info"></div>
            </div>
            
            <div class="form-group">
                <label>😂 Meme/Content Video (Top)</label>
                <input type="file" name="meme_video" id="meme" accept="video/*" required>
                <div class="file-info" id="meme-info"></div>
            </div>
            
            <div class="form-group">
                <label>✍️ Caption</label>
                <textarea name="caption" placeholder="Write your caption here..." required></textarea>
            </div>
            
            <div class="form-group">
                <label>🏷️ Hashtags</label>
                <input type="text" name="hashtags" placeholder="#gaming #memes #viral">
            </div>
            
            <div class="form-group">
                <label>🖼️ Thumbnail (Optional)</label>
                <input type="file" name="thumbnail" accept="image/*">
            </div>
            
            <button type="submit" id="submitBtn">
                🚀 Upload & Process
            </button>
        </form>
        
        <div id="result" class="result"></div>
    </div>
    
    <script>
        const form = document.getElementById('uploadForm');
        const result = document.getElementById('result');
        const submitBtn = document.getElementById('submitBtn');
        
        document.getElementById('gameplay').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                document.getElementById('gameplay-info').textContent = 
                    `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
            }
        });
        
        document.getElementById('meme').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                document.getElementById('meme-info').textContent = 
                    `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
            }
        });
        
        form.onsubmit = async (e) => {
            e.preventDefault();
            
            result.className = 'result loading';
            result.style.display = 'block';
            result.innerHTML = '<div class="loader"></div> Processing your video... This may take a few minutes.';
            submitBtn.disabled = true;
            
            const formData = new FormData(form);
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    result.className = 'result success';
                    result.innerHTML = `✅ ${data.message}<br><small>Approval ID: ${data.approval_id}</small>`;
                    form.reset();
                    document.getElementById('gameplay-info').textContent = '';
                    document.getElementById('meme-info').textContent = '';
                } else {
                    result.className = 'result error';
                    result.innerHTML = `❌ ${data.error}`;
                }
            } catch (error) {
                result.className = 'result error';
                result.innerHTML = `❌ Error: ${error.message}`;
            } finally {
                submitBtn.disabled = false;
            }
        };
    </script>
</body>
</html>
'''


class FFmpegProcessor:
    """Handle video processing using FFmpeg directly"""
    
    @staticmethod
    def check_ffmpeg():
        """Check if FFmpeg is installed"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                    capture_output=True, 
                                    text=True, 
                                    timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def get_video_info(file_path):
        """Get video information using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return None
            
            info = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)
            
            if not video_stream:
                return None
            
            return {
                'duration': float(info['format'].get('duration', 0)),
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'codec': video_stream.get('codec_name', ''),
                'size': int(info['format'].get('size', 0))
            }
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None
    
    @staticmethod
    def validate_video(file_path):
        """Validate video meets requirements"""
        info = FFmpegProcessor.get_video_info(file_path)
        
        if not info:
            return False, ["Invalid or corrupted video file"], None
        
        errors = []
        
        if info['duration'] > 90:
            errors.append(f"Duration too long: {info['duration']:.1f}s (max 90s)")
        if info['duration'] < 1:
            errors.append(f"Duration too short: {info['duration']:.1f}s (min 1s)")
        if info['size'] > CONFIG['MAX_FILE_SIZE']:
            errors.append(f"File too large: {info['size'] / 1024 / 1024:.1f}MB (max 100MB)")
        
        return len(errors) == 0, errors, info
    
    @staticmethod
    def process_videos(gameplay_path, meme_path, output_path):
        """Combine videos vertically using FFmpeg"""
        try:
            logger.info(f"Processing videos with FFmpeg...")
            
            # Get video info
            gameplay_info = FFmpegProcessor.get_video_info(gameplay_path)
            meme_info = FFmpegProcessor.get_video_info(meme_path)
            
            if not gameplay_info or not meme_info:
                return False, "Failed to read video information"
            
            # Use shortest duration
            min_duration = min(gameplay_info['duration'], meme_info['duration'], 60)
            
            # FFmpeg command to stack videos vertically
            cmd = [
                'ffmpeg',
                '-i', meme_path,
                '-i', gameplay_path,
                '-filter_complex',
                f'[0:v]scale=1080:-2,setsar=1[meme];'
                f'[1:v]scale=1080:-2,setsar=1[gameplay];'
                f'[meme]pad=1080:ih+10:0:0:black[meme_pad];'
                f'[meme_pad][gameplay]vstack=inputs=2[stacked];'
                f'[stacked]scale=1080:1920:force_original_aspect_ratio=decrease,'
                f'pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black[final]',
                '-map', '[final]',
                '-map', '1:a?',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-profile:v', 'high',
                '-level', '4.2',
                '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-ar', '44100',
                '-t', str(min_duration),
                '-y',
                output_path
            ]
            
            logger.info(f"Running FFmpeg command...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False, f"FFmpeg processing failed: {result.stderr[-200:]}"
            
            # Verify output file exists and is valid
            if not os.path.exists(output_path):
                return False, "Output file was not created"
            
            if os.path.getsize(output_path) < 1000:
                return False, "Output file is too small (likely corrupted)"
            
            logger.info(f"✅ Video processed successfully: {output_path}")
            return True, "Video processed successfully"
            
        except subprocess.TimeoutExpired:
            return False, "Processing timeout (video too long or complex)"
        except Exception as e:
            logger.error(f"Processing exception: {e}")
            return False, str(e)


class InstagramAPI:
    """Handle Instagram Graph API operations"""
    
    @staticmethod
    def upload_reel(video_url, caption):
        """Upload reel to Instagram"""
        try:
            logger.info("Creating Instagram media container...")
            create_url = f"https://graph.facebook.com/v21.0/{CONFIG['INSTAGRAM_BUSINESS_ACCOUNT_ID']}/media"
            
            payload = {
                'video_url': video_url,
                'media_type': 'REELS',
                'caption': caption,
                'share_to_feed': True,
                'access_token': CONFIG['INSTAGRAM_ACCESS_TOKEN']
            }
            
            response = requests.post(create_url, data=payload, timeout=30)
            
            if response.status_code != 200:
                error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                logger.error(f"Failed to create container: {error_msg}")
                return False, f"Instagram API error: {error_msg}"
            
            container_id = response.json().get('id')
            logger.info(f"Container created: {container_id}")
            
            # Poll for status
            logger.info("Waiting for Instagram to process video...")
            for attempt in range(60):
                status_url = f"https://graph.facebook.com/v21.0/{container_id}"
                status_response = requests.get(
                    status_url,
                    params={
                        'fields': 'status_code,status',
                        'access_token': CONFIG['INSTAGRAM_ACCESS_TOKEN']
                    },
                    timeout=10
                )
                
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
            publish_url = f"https://graph.facebook.com/v21.0/{CONFIG['INSTAGRAM_BUSINESS_ACCOUNT_ID']}/media_publish"
            publish_response = requests.post(
                publish_url,
                data={
                    'creation_id': container_id,
                    'access_token': CONFIG['INSTAGRAM_ACCESS_TOKEN']
                },
                timeout=30
            )
            
            if publish_response.status_code != 200:
                logger.error(f"Failed to publish: {publish_response.text}")
                return False, "Failed to publish reel"
            
            media_id = publish_response.json().get('id')
            instagram_url = f"https://www.instagram.com/reel/{media_id}/"
            
            logger.info(f"✅ Reel published: {instagram_url}")
            return True, instagram_url
            
        except Exception as e:
            logger.error(f"Instagram upload exception: {e}")
            return False, str(e)


def send_to_telegram(video_path, caption, hashtags, approval_id):
    """Send preview to admin via Telegram"""
    try:
        if not telegram_bot:
            return False, "Telegram bot not initialized"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{approval_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{approval_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            f"🎬 New Reel for Approval\n\n"
            f"📝 Caption: {caption}\n"
            f"🏷️ Hashtags: {hashtags}\n\n"
            f"Approve or Reject?"
        )
        
        with open(video_path, 'rb') as video:
            telegram_bot.send_video(
                chat_id=CONFIG['TELEGRAM_ADMIN_CHAT_ID'],
                video=video,
                caption=message,
                reply_markup=reply_markup,
                timeout=120
            )
        
        logger.info(f"✅ Sent to Telegram: {approval_id}")
        return True, "Sent to admin"
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False, str(e)


@app.route('/')
def index():
    return render_template_string(HTML_FORM)


@app.route('/videos/<filename>')
def serve_video(filename):
    """Serve processed videos"""
    return send_from_directory(CONFIG['PROCESSED_FOLDER'], filename)


@app.route('/upload', methods=['POST'])
def upload():
    """Handle video upload"""
    try:
        # Check FFmpeg
        if not FFmpegProcessor.check_ffmpeg():
            return jsonify({'success': False, 'error': 'FFmpeg not installed on server'}), 500
        
        # Validate files
        if 'gameplay_video' not in request.files or 'meme_video' not in request.files:
            return jsonify({'success': False, 'error': 'Both videos required'}), 400
        
        gameplay_file = request.files['gameplay_video']
        meme_file = request.files['meme_video']
        caption = request.form.get('caption', '').strip()
        hashtags = request.form.get('hashtags', '').strip()
        
        if not gameplay_file.filename or not meme_file.filename:
            return jsonify({'success': False, 'error': 'Please select both videos'}), 400
        
        if not caption:
            return jsonify({'success': False, 'error': 'Caption is required'}), 400
        
        # Save files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        gameplay_path = os.path.join(CONFIG['UPLOAD_FOLDER'], f'gameplay_{timestamp}.mp4')
        meme_path = os.path.join(CONFIG['UPLOAD_FOLDER'], f'meme_{timestamp}.mp4')
        
        gameplay_file.save(gameplay_path)
        meme_file.save(meme_path)
        
        logger.info(f"Files saved: {timestamp}")
        
        # Validate videos
        valid1, errors1, _ = FFmpegProcessor.validate_video(gameplay_path)
        valid2, errors2, _ = FFmpegProcessor.validate_video(meme_path)
        
        if not valid1:
            return jsonify({'success': False, 'error': f"Gameplay video: {', '.join(errors1)}"}), 400
        if not valid2:
            return jsonify({'success': False, 'error': f"Meme video: {', '.join(errors2)}"}), 400
        
        # Process videos
        output_path = os.path.join(CONFIG['PROCESSED_FOLDER'], f'final_{timestamp}.mp4')
        success, message = FFmpegProcessor.process_videos(gameplay_path, meme_path, output_path)
        
        if not success:
            return jsonify({'success': False, 'error': f"Processing failed: {message}"}), 500
        
        # Store approval data
        approval_id = timestamp
        pending_approvals[approval_id] = {
            'video_path': output_path,
            'caption': caption,
            'hashtags': hashtags,
            'status': 'pending',
            'created_at': datetime.now()
        }
        
        # Send to admin
        success, message = send_to_telegram(output_path, caption, hashtags, approval_id)
        
        if not success:
            return jsonify({'success': False, 'error': f"Failed to notify admin: {message}"}), 500
        
        return jsonify({
            'success': True,
            'message': 'Video processed and sent to admin for approval!',
            'approval_id': approval_id
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def telegram_callback_handler(update, context):
    """Handle Telegram approval callbacks"""
    query = update.callback_query
    query.answer()
    
    try:
        action, approval_id = query.data.split('_', 1)
        
        if approval_id not in pending_approvals:
            query.edit_message_caption(caption="❌ Request expired or already processed")
            return
        
        approval_data = pending_approvals[approval_id]
        
        if action == 'approve':
            query.edit_message_caption(caption="⏳ Uploading to Instagram...")
            
            # Generate public URL
            filename = os.path.basename(approval_data['video_path'])
            video_url = f"{CONFIG['PUBLIC_VIDEO_URL']}{filename}"
            
            caption_full = f"{approval_data['caption']}\n\n{approval_data['hashtags']}"
            
            # Upload to Instagram
            success, result = InstagramAPI.upload_reel(video_url, caption_full)
            
            if success:
                query.edit_message_caption(caption=f"✅ Posted successfully!\n\n{result}")
                approval_data['status'] = 'published'
                approval_data['instagram_url'] = result
            else:
                query.edit_message_caption(caption=f"❌ Upload failed:\n{result}")
                approval_data['status'] = 'failed'
                approval_data['error'] = result
        
        elif action == 'reject':
            query.edit_message_caption(caption="❌ Reel rejected by admin")
            approval_data['status'] = 'rejected'
    
    except Exception as e:
        logger.error(f"Callback error: {e}")
        query.edit_message_caption(caption=f"❌ Error: {str(e)}")


def start_telegram_bot():
    """Start Telegram bot"""
    try:
        updater = Updater(CONFIG['TELEGRAM_BOT_TOKEN'], use_context=True)
        updater.dispatcher.add_handler(CallbackQueryHandler(telegram_callback_handler))
        updater.start_polling()
        logger.info("✅ Telegram bot started")
        updater.idle()
    except Exception as e:
        logger.error(f"Telegram bot error: {e}")


if __name__ == '__main__':
    # Check FFmpeg
    if not FFmpegProcessor.check_ffmpeg():
        logger.error("❌ FFmpeg not found! Please install FFmpeg first.")
        logger.error("   macOS: brew install ffmpeg")
        logger.error("   Ubuntu: sudo apt install ffmpeg")
        logger.error("   Windows: Download from ffmpeg.org")
        exit(1)
    
    logger.info("✅ FFmpeg is installed")
    
    # Start Telegram bot in separate thread
    if telegram_bot:
        telegram_thread = threading.Thread(target=start_telegram_bot, daemon=True)
        telegram_thread.start()
    
    # Start Flask app
    logger.info(f"🚀 Server starting on http://{CONFIG['HOST']}:{CONFIG['PORT']}")
    app.run(host=CONFIG['HOST'], port=CONFIG['PORT'], debug=False)