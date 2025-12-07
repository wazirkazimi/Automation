"""
React Frontend for AWS Lambda Video Editor
Users upload 2 videos, system processes, posts to Instagram
"""

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import AWS from 'aws-sdk';

// Configure AWS SDK
AWS.config.update({
  region: 'us-east-1',
  credentials: new AWS.CognitoIdentityCredentials({
    IdentityPoolId: process.env.REACT_APP_AWS_IDENTITY_POOL_ID
  })
});

const s3 = new AWS.S3();
const API_ENDPOINT = process.env.REACT_APP_API_ENDPOINT;

export default function VideoEditor() {
  const [memeFile, setMemeFile] = useState(null);
  const [gameplayFile, setGameplayFile] = useState(null);
  const [caption, setCaption] = useState('');
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);
  const [progress, setProgress] = useState(0);

  // Upload file to S3
  const uploadToS3 = async (file, jobId, type) => {
    const key = `uploads/${jobId}/${type}_${file.name}`;
    
    try {
      const params = {
        Bucket: process.env.REACT_APP_INPUT_BUCKET,
        Key: key,
        Body: file,
        ContentType: 'video/mp4'
      };

      await s3.upload(params).promise();
      console.log(`Uploaded ${type} to S3: ${key}`);
      return key;
    } catch (error) {
      console.error(`S3 upload error for ${type}:`, error);
      throw error;
    }
  };

  // Trigger Lambda by uploading metadata
  const triggerLambda = async (memeKey, gameplayKey) => {
    const jobId = `job-${Date.now()}`;
    setJobId(jobId);

    const metadata = {
      meme_video_key: memeKey,
      gameplay_video_key: gameplayKey,
      caption: caption,
      job_id: jobId,
      timestamp: new Date().toISOString()
    };

    try {
      // Upload metadata file - this triggers Lambda
      const params = {
        Bucket: process.env.REACT_APP_INPUT_BUCKET,
        Key: `uploads/${jobId}/data.json`,
        Body: JSON.stringify(metadata),
        ContentType: 'application/json'
      };

      await s3.upload(params).promise();
      console.log('Metadata uploaded - Lambda triggered');
      return jobId;
    } catch (error) {
      console.error('Error uploading metadata:', error);
      throw error;
    }
  };

  // Poll for job completion
  const pollJobStatus = async (jobId) => {
    const maxAttempts = 360; // 30 minutes with 5s interval
    let attempts = 0;

    const interval = setInterval(async () => {
      attempts++;
      setProgress(Math.min(95, (attempts / maxAttempts) * 100));

      if (attempts >= maxAttempts) {
        clearInterval(interval);
        setStatus('error');
        setLoading(false);
        return;
      }

      try {
        // Check if output file exists
        const outputKey = `outputs/${jobId}/output_${jobId}.mp4`;
        const params = {
          Bucket: process.env.REACT_APP_OUTPUT_BUCKET,
          Key: outputKey
        };

        await s3.headObject(params).promise();

        // File exists - job completed
        clearInterval(interval);
        setStatus('completed');
        setProgress(100);

        // Get public URL
        const url = `https://${process.env.REACT_APP_OUTPUT_BUCKET}.s3.amazonaws.com/${outputKey}`;
        setResult({
          video_url: url,
          job_id: jobId
        });

        setLoading(false);
      } catch (error) {
        // File not ready yet, continue polling
      }
    }, 5000);
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!memeFile || !gameplayFile) {
      alert('Please select both videos');
      return;
    }

    setLoading(true);
    setStatus('uploading');
    setProgress(10);

    try {
      // Generate job ID
      const jobId = `job-${Date.now()}`;

      // Upload both videos
      setProgress(20);
      const memeKey = await uploadToS3(memeFile, jobId, 'meme');
      
      setProgress(40);
      const gameplayKey = await uploadToS3(gameplayFile, jobId, 'gameplay');

      // Trigger Lambda
      setProgress(50);
      setStatus('processing');
      await triggerLambda(memeKey, gameplayKey);

      // Start polling
      pollJobStatus(jobId);
    } catch (error) {
      console.error('Error:', error);
      setStatus('error');
      setLoading(false);
      alert(`Error: ${error.message}`);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1>🎬 Video Editor</h1>
        <p style={styles.subtitle}>Upload 2 videos → Automatic edit → Posts to Instagram</p>

        {!result ? (
          <form onSubmit={handleSubmit} style={styles.form}>
            {/* Meme Video Upload */}
            <div style={styles.uploadGroup}>
              <label style={styles.label}>Meme Video</label>
              <input
                type="file"
                accept="video/mp4"
                onChange={(e) => setMemeFile(e.target.files[0])}
                disabled={loading}
                style={styles.input}
              />
              {memeFile && <p style={styles.filename}>✓ {memeFile.name}</p>}
            </div>

            {/* Gameplay Video Upload */}
            <div style={styles.uploadGroup}>
              <label style={styles.label}>Gameplay Video</label>
              <input
                type="file"
                accept="video/mp4"
                onChange={(e) => setGameplayFile(e.target.files[0])}
                disabled={loading}
                style={styles.input}
              />
              {gameplayFile && <p style={styles.filename}>✓ {gameplayFile.name}</p>}
            </div>

            {/* Caption Input */}
            <div style={styles.uploadGroup}>
              <label style={styles.label}>Caption (Optional)</label>
              <textarea
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                placeholder="Enter caption for Instagram..."
                disabled={loading}
                style={styles.textarea}
              />
            </div>

            {/* Loading Progress */}
            {loading && (
              <div style={styles.progressSection}>
                <p style={styles.status}>{status.toUpperCase()}</p>
                <div style={styles.progressBar}>
                  <div
                    style={{
                      ...styles.progressFill,
                      width: `${progress}%`
                    }}
                  />
                </div>
                <p style={styles.progressText}>{Math.round(progress)}%</p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              style={{
                ...styles.button,
                opacity: loading ? 0.6 : 1,
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              {loading ? `Processing... ${Math.round(progress)}%` : 'Process Video'}
            </button>
          </form>
        ) : (
          <div style={styles.resultSection}>
            <h2>✅ Video Processed Successfully!</h2>

            {/* Video Preview */}
            <video
              src={result.video_url}
              controls
              style={styles.videoPreview}
            />

            {/* Download Button */}
            <a
              href={result.video_url}
              download
              style={styles.downloadButton}
            >
              📥 Download Video
            </a>

            {/* Instagram Link */}
            {result.instagram_url && (
              <a
                href={result.instagram_url}
                target="_blank"
                rel="noopener noreferrer"
                style={styles.instagramButton}
              >
                📱 View on Instagram
              </a>
            )}

            {/* Process Another */}
            <button
              onClick={() => {
                setResult(null);
                setMemeFile(null);
                setGameplayFile(null);
                setCaption('');
                setProgress(0);
                setStatus('idle');
              }}
              style={styles.resetButton}
            >
              Process Another Video
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    padding: '20px'
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '40px',
    maxWidth: '600px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
  },
  subtitle: {
    color: '#666',
    marginBottom: '30px'
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px'
  },
  uploadGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px'
  },
  label: {
    fontWeight: 'bold',
    color: '#333'
  },
  input: {
    padding: '12px',
    border: '2px solid #ddd',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px'
  },
  textarea: {
    padding: '12px',
    border: '2px solid #ddd',
    borderRadius: '6px',
    minHeight: '80px',
    fontSize: '14px',
    fontFamily: 'inherit',
    resize: 'vertical'
  },
  filename: {
    color: '#27ae60',
    fontSize: '14px',
    margin: '0'
  },
  progressSection: {
    marginTop: '20px'
  },
  status: {
    fontWeight: 'bold',
    color: '#3498db',
    marginBottom: '10px'
  },
  progressBar: {
    height: '8px',
    backgroundColor: '#e0e0e0',
    borderRadius: '4px',
    overflow: 'hidden'
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#27ae60',
    transition: 'width 0.3s ease'
  },
  progressText: {
    textAlign: 'center',
    marginTop: '10px',
    color: '#666',
    fontSize: '14px'
  },
  button: {
    padding: '12px 20px',
    backgroundColor: '#3498db',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontWeight: 'bold',
    fontSize: '16px',
    cursor: 'pointer',
    transition: 'background-color 0.3s ease'
  },
  resultSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px',
    alignItems: 'center'
  },
  videoPreview: {
    width: '100%',
    maxHeight: '400px',
    borderRadius: '6px',
    marginVertical: '20px'
  },
  downloadButton: {
    padding: '12px 20px',
    backgroundColor: '#27ae60',
    color: 'white',
    textDecoration: 'none',
    borderRadius: '6px',
    fontWeight: 'bold',
    textAlign: 'center',
    width: '100%'
  },
  instagramButton: {
    padding: '12px 20px',
    backgroundColor: '#e1306c',
    color: 'white',
    textDecoration: 'none',
    borderRadius: '6px',
    fontWeight: 'bold',
    textAlign: 'center',
    width: '100%'
  },
  resetButton: {
    padding: '12px 20px',
    backgroundColor: '#95a5a6',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontWeight: 'bold',
    cursor: 'pointer',
    width: '100%'
  }
};
