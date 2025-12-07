# 🚀 Quick Reference Card

## Files Overview

### 📋 Core Files
| File | Purpose | Size |
|------|---------|------|
| `vi.py` | Video processing engine | ~5KB |
| `config.py` | Configuration management | ~2KB |
| `.env` | Environment variables | ~1KB |
| `requirements.txt` | Python dependencies | ~1KB |

### ☁️ AWS Lambda Files (lambda_deployment/)
| File | Purpose | Size |
|------|---------|------|
| `lambda_handler.py` | Lambda entry point | 7.4KB |
| `vi_lambda.py` | Serverless video processor | 5.1KB |
| `VideoEditor.jsx` | React frontend component | 11.5KB |
| `requirements.txt` | Lambda dependencies | 123B |
| `AWS_LAMBDA_SETUP.md` | Complete deployment guide | 7.6KB |
| `quick-setup.sh` | Automated setup script | 4.7KB |

### 📚 Documentation
| Document | Purpose | Time |
|----------|---------|------|
| `SETUP.md` | Project overview | 5 min read |
| `MIGRATION_SUMMARY.md` | What changed & why | 5 min read |
| `INSTAGRAM_TOKEN_GUIDE.md` | Token management | 3 min read |
| `lambda_deployment/AWS_LAMBDA_SETUP.md` | Full AWS guide | 15 min setup |

---

## 🎯 Quick Commands

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask (if still available)
python -m flask run

# Process video manually
python -c "from vi import stack_videos; stack_videos('meme.mp4', 'gameplay.mp4', 'output.mp4')"
```

### AWS Lambda Setup
```bash
# Install AWS CLI
pip install awscli

# Configure AWS
aws configure

# Run auto setup
cd lambda_deployment
bash quick-setup.sh
```

### Git Operations
```bash
# View all changes
git status

# View recent commits
git log --oneline -5

# Push changes
git push origin main
```

---

## 💰 Cost Calculator

```
AWS Lambda Usage Calculator
============================

Videos per month: 100 (estimate)
Duration each: 20 minutes

Lambda costs:
  - Invocations: 100 × $0.20/M = $0.02
  - Compute: 100 × 20min × $0.0000166667/GB-sec = $0.33
  - Total Lambda: ~$0.35

S3 costs:
  - Storage (input): 50GB × $0.023 = $1.15
  - Storage (output): 50GB × $0.023 = $1.15
  - Upload requests: 1000 × $0.005/K = $0.50
  - Download requests: 1000 × $0.0004/K = $0.40
  - Data transfer: 50GB × $0.09 = $4.50
  - Total S3: ~$7.70

TOTAL MONTHLY: ~$8.05
(Free tier covers first $1M requests + 5GB storage)
```

---

## 🔑 Environment Variables

### Required
```env
# Instagram (leave empty for development mode)
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841478601395535
INSTAGRAM_ACCESS_TOKEN=your-token-here

# AWS Lambda
OUTPUT_BUCKET=video-editor-output-xxx
```

### Optional
```env
# Local Flask
FLASK_ENV=development
PUBLIC_VIDEO_URL=http://localhost:5000

# AWS
AWS_REGION=us-east-1
INPUT_BUCKET=video-editor-input-xxx
```

---

## 📊 Workflow Diagrams

### Local Flask Workflow
```
User Form
   ↓
File Upload (local /tmp)
   ↓
Video Processing (vi.py)
   ↓
S3 Upload (optional)
   ↓
Instagram Post (if enabled)
   ↓
Download Response
```

### AWS Lambda Workflow
```
User Upload (React)
   ↓
S3 Input Bucket
   ↓
S3 Event Trigger
   ↓
Lambda Function
   ↓
Download from S3
Process Video
Upload to S3 Output
Post to Instagram
   ↓
Return Results to Frontend
```

---

## 🎬 Video Processing Pipeline

```
Input Videos (MP4 H.264)
   ↓ (vi.py / vi_lambda.py)
1. Load clips
2. Pad to 1080×1920
3. Create split-screen
4. Add captions (optional)
5. Set audio
6. Encode optimized MP4
   ↓
Output (1080×1920, 30fps, H.264+AAC+YUV420P)
   ↓
Post to Instagram
```

---

## ✅ Deployment Checklist

### Before Local Testing
- [ ] Python 3.8+ installed
- [ ] Virtual environment activated
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] .env file configured
- [ ] FFmpeg installed on system

### Before AWS Deployment
- [ ] AWS account created
- [ ] AWS CLI installed & configured
- [ ] Instagram token obtained (fresh)
- [ ] Read `AWS_LAMBDA_SETUP.md`
- [ ] Run `quick-setup.sh` or follow manual steps

### Before Production
- [ ] All endpoints tested
- [ ] Instagram posting verified
- [ ] S3 buckets created
- [ ] IAM roles configured
- [ ] CloudWatch alarms set
- [ ] Backup strategy planned

---

## 🐛 Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `No module named moviepy` | Deps not installed | `pip install -r requirements.txt` |
| `FFmpeg not found` | FFmpeg not installed | Install FFmpeg system-wide |
| Instagram error 190 | Token expired | Refresh in FB Developer Console |
| S3 access denied | IAM permissions | Check Lambda execution role |
| Lambda timeout | Video too long | Increase timeout in console |
| Videos corrupted | Encoding issue | Check ffmpeg parameters |

---

## 📞 Support Resources

### Documentation
- Main Guide: `SETUP.md`
- AWS Setup: `lambda_deployment/AWS_LAMBDA_SETUP.md`
- Token Guide: `INSTAGRAM_TOKEN_GUIDE.md`
- Migration Info: `MIGRATION_SUMMARY.md`

### External Resources
- MoviePy: https://zulko.github.io/moviepy/
- AWS Lambda: https://docs.aws.amazon.com/lambda/
- Instagram API: https://developers.facebook.com/docs/instagram-api/

### GitHub
- Repository: https://github.com/wazirkazimi/Automation
- Issues: Use GitHub Issues for bug reports

---

## 🚀 Next Steps

### Immediate (Choose One)
1. **Try Local**: `pip install -r requirements.txt && python -m flask run`
2. **Try AWS**: Follow `lambda_deployment/AWS_LAMBDA_SETUP.md`
3. **Just Deploy**: Run `lambda_deployment/quick-setup.sh`

### Within 24 Hours
- [ ] Test video processing
- [ ] Verify Instagram posting
- [ ] Monitor CloudWatch logs
- [ ] Test with sample videos

### Within 1 Week
- [ ] Deploy React frontend
- [ ] Set up monitoring alerts
- [ ] Document any customizations
- [ ] Plan for token refresh schedule

---

## 💡 Pro Tips

1. **Use ngrok for local testing**: `ngrok http 5000`
2. **Monitor Lambda with**: `aws logs tail /aws/lambda/VideoEditorFunction --follow`
3. **Test videos locally before uploading**: `python -c "from vi import stack_videos; ..."`
4. **Keep Instagram token fresh**: Set calendar reminder for Feb 5, 2026
5. **Use Lambda layers for dependencies**: Reduces deployment package size
6. **Enable S3 versioning**: Backup old video versions automatically

---

**Version**: 2.0 (AWS Lambda Edition)  
**Updated**: December 7, 2025  
**Status**: Production Ready ✅
