"""
AWS Lambda handler for video processing and Instagram posting.
Triggered by S3 uploads, processes videos, and posts to Instagram.
"""

import json
import boto3
import requests
import tempfile
import os
import logging
from pathlib import Path
from urllib.parse import unquote_plus

# Initialize AWS clients
s3_client = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import video processing functions
import sys
sys.path.insert(0, '/opt/python')
from vi import stack_videos

# Configuration from environment variables
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
OUTPUT_BUCKET = os.getenv('OUTPUT_BUCKET', 'video-editor-output')
CLOUDFRONT_URL = os.getenv('CLOUDFRONT_URL', '')


def get_object_from_s3(bucket, key):
    """Download file from S3 to Lambda /tmp directory."""
    try:
        local_path = f"/tmp/{Path(key).name}"
        s3_client.download_file(bucket, key, local_path)
        logger.info(f"Downloaded {key} to {local_path}")
        return local_path
    except Exception as e:
        logger.error(f"Error downloading from S3: {str(e)}")
        raise


def upload_to_s3(file_path, bucket, key):
    """Upload file from Lambda /tmp to S3."""
    try:
        s3_client.upload_file(
            file_path, 
            bucket, 
            key,
            ExtraArgs={
                'ContentType': 'video/mp4',
                'CacheControl': 'public, max-age=3600'
            }
        )
        logger.info(f"Uploaded {file_path} to s3://{bucket}/{key}")
        
        # Return public URL
        if CLOUDFRONT_URL:
            return f"{CLOUDFRONT_URL}/{key}"
        else:
            return f"https://{bucket}.s3.amazonaws.com/{key}"
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        raise


def post_to_instagram(video_url, caption=""):
    """Post video to Instagram using Graph API."""
    try:
        logger.info(f"Posting to Instagram: {video_url}")
        
        # Upload video container
        upload_url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"
        upload_data = {
            'media_type': 'VIDEO',
            'video_url': video_url,
            'caption': caption or 'New video created! 🎬 #VideoEdit #Content',
            'access_token': INSTAGRAM_ACCESS_TOKEN
        }
        
        response = requests.post(upload_url, data=upload_data, timeout=30)
        
        if response.status_code == 200:
            container_id = response.json().get('id')
            logger.info(f"Container created: {container_id}")
            
            # Publish the container
            publish_url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish"
            publish_data = {
                'creation_id': container_id,
                'access_token': INSTAGRAM_ACCESS_TOKEN
            }
            
            publish_response = requests.post(publish_url, data=publish_data, timeout=30)
            
            if publish_response.status_code == 200:
                media_id = publish_response.json().get('id')
                instagram_url = f"https://www.instagram.com/p/{media_id}/"
                logger.info(f"✅ Video posted to Instagram: {instagram_url}")
                return instagram_url
            else:
                error = publish_response.json()
                logger.error(f"Instagram publish failed: {error}")
                return None
        else:
            error = response.json()
            logger.error(f"Instagram upload failed: {error}")
            return None
            
    except Exception as e:
        logger.error(f"Error posting to Instagram: {str(e)}")
        return None


def lambda_handler(event, context):
    """
    Main Lambda handler triggered by S3 event.
    
    Expected S3 event with object metadata:
    {
        "Records": [{
            "s3": {
                "bucket": {"name": "video-editor-input"},
                "object": {
                    "key": "uploads/job-123/data.json"
                }
            }
        }]
    }
    
    data.json format:
    {
        "meme_video_key": "uploads/job-123/meme.mp4",
        "gameplay_video_key": "uploads/job-123/gameplay.mp4",
        "caption": "My awesome video",
        "job_id": "job-123"
    }
    """
    
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Parse S3 event
        if 'Records' not in event:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid event format'})
            }
        
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        
        logger.info(f"Processing S3 object: s3://{bucket}/{key}")
        
        # Download metadata file
        metadata_path = get_object_from_s3(bucket, key)
        
        with open(metadata_path, 'r') as f:
            job_data = json.load(f)
        
        meme_video_key = job_data['meme_video_key']
        gameplay_video_key = job_data['gameplay_video_key']
        caption = job_data.get('caption', '')
        job_id = job_data.get('job_id', 'unknown')
        
        logger.info(f"Job {job_id}: Processing videos")
        
        # Download input videos
        meme_path = get_object_from_s3(bucket, meme_video_key)
        gameplay_path = get_object_from_s3(bucket, gameplay_video_key)
        
        # Process videos
        output_filename = f"output_{job_id}.mp4"
        output_path = f"/tmp/{output_filename}"
        
        logger.info(f"Processing video: {output_path}")
        stack_videos(meme_path, gameplay_path, output_path, caption)
        
        logger.info(f"Video processed successfully: {output_path}")
        
        # Upload output to S3
        output_key = f"outputs/{job_id}/{output_filename}"
        video_url = upload_to_s3(output_path, OUTPUT_BUCKET, output_key)
        
        logger.info(f"Video URL: {video_url}")
        
        # Post to Instagram
        instagram_url = None
        if INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ACCOUNT_ID:
            instagram_url = post_to_instagram(video_url, caption)
        else:
            logger.warning("Instagram credentials not provided")
        
        # Cleanup temp files
        for path in [metadata_path, meme_path, gameplay_path, output_path]:
            if os.path.exists(path):
                os.remove(path)
        
        result = {
            'job_id': job_id,
            'video_url': video_url,
            'instagram_url': instagram_url,
            'status': 'completed'
        }
        
        logger.info(f"Job {job_id} completed: {result}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
