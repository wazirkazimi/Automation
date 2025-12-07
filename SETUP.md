# AWS Serverless Video Editor - Complete Setup

## 🚀 What You're Getting

A **production-ready serverless video editor** where:
- Users upload 2 videos
- AWS Lambda automatically processes them
- Final video posts to Instagram
- **Zero server management** - costs ~$2-10/month

## 📁 Project Structure

```
Automation/
├── lambda_deployment/          # AWS Lambda setup
│   ├── lambda_handler.py       # Lambda function entry point
│   ├── vi_lambda.py            # Video processing (serverless version)
│   ├── requirements.txt        # Python dependencies
│   ├── AWS_LAMBDA_SETUP.md     # Step-by-step AWS setup guide
│   ├── VideoEditor.jsx         # React component for frontend
│   └── layers/                 # FFmpeg layer for Lambda
│
├── .env                        # Environment variables
├── config.py                   # Configuration
├── vi.py                       # Video processing (local)
├── requirements.txt            # Main Python dependencies
├── cleanup.py                  # Run once to clean up old files
│
├── uploads/                    # Local uploads directory
├── outputs/                    # Local outputs directory
├── processed/                  # Local processed directory
│
└── JScode/                     # JavaScript frontend code
```

## 🎯 Quick Start (Choose Your Path)

### Path A: Local Testing (Current)
```bash
python app.py
# Flask app runs on http://localhost:5000
# Great for development
```

### Path B: AWS Lambda (Recommended for Production)
```bash
# 1. Follow AWS_LAMBDA_SETUP.md step-by-step
# 2. Deploy Lambda function
# 3. Deploy React frontend to Vercel/Netlify
# 4. Zero server costs, auto-scaling, Instagram integration
```

## 📋 Setup Instructions

### 1. Clean Up Old Files (Optional)
```bash
python cleanup.py
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables

**For Local Testing:**
```bash
# .env file
FLASK_ENV=development
FLASK_APP=app.py
PUBLIC_VIDEO_URL=http://localhost:5000
```

**For AWS Lambda:**
```bash
# Follow AWS_LAMBDA_SETUP.md for S3 bucket setup
# Then configure environment variables in Lambda console:
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841478601395535
INSTAGRAM_ACCESS_TOKEN=your-token
OUTPUT_BUCKET=video-editor-output-xxx
```

### 4. Test Locally
```bash
# Run Flask app
python app.py

# Visit http://localhost:5000
# Upload 2 videos via form
# Wait for processing
# Download result
```

### 5. Deploy to AWS Lambda
```bash
# Follow complete guide in lambda_deployment/AWS_LAMBDA_SETUP.md
# Takes ~30 minutes
# Costs ~$2-10/month for moderate usage
```

## 🔑 Key Files Explained

| File | Purpose |
|------|---------|
| `lambda_handler.py` | Entry point for AWS Lambda function |
| `vi_lambda.py` | Video processing engine (optimized for Lambda) |
| `VideoEditor.jsx` | React component for user uploads |
| `AWS_LAMBDA_SETUP.md` | Complete AWS deployment guide |
| `cleanup.py` | Removes old Flask/Procfile/Docker files |

## 💰 Cost Comparison

| Option | Monthly Cost | Server Management |
|--------|--------------|-------------------|
| **Local + ngrok** | $0 | Required (your PC) |
| **Railway** | $5-20 | Minimal |
| **AWS Lambda** | $2-10 | None ✅ |
| **Firebase** | $0-5 | None ✅ |

## 📱 Instagram Integration

Both local and Lambda versions support:
- ✅ Automatic Instagram posting
- ✅ Captions included
- ✅ Error handling for expired tokens
- ✅ Development mode bypass

## 🛠️ Technology Stack

- **Video Processing**: MoviePy + FFmpeg
- **Backend**: AWS Lambda + Flask (local)
- **Storage**: AWS S3
- **Frontend**: React + Axios
- **Instagram API**: Graph API v18

## 📖 Documentation

- **Local Development**: See comments in `app.py`
- **AWS Deployment**: See `lambda_deployment/AWS_LAMBDA_SETUP.md`
- **React Setup**: See `lambda_deployment/VideoEditor.jsx`
- **Instagram Config**: See `INSTAGRAM_TOKEN_GUIDE.md`

## 🚨 Important Notes

1. **Instagram Token**: Must be kept fresh (60 days). See token guide for refresh instructions.

2. **Lambda Cold Start**: First invocation takes 10-15 seconds. Subsequent calls are faster.

3. **Video Size Limits**: 
   - Maximum 5 minutes per input video
   - Output: 1080x1920 (9:16 reel format)

4. **AWS Free Tier**: 
   - 1M Lambda requests free
   - 5GB S3 storage free
   - Great for testing!

## ✅ Checklist for Production

- [ ] AWS account created
- [ ] S3 buckets set up
- [ ] Lambda function deployed
- [ ] FFmpeg layer added
- [ ] Instagram token configured
- [ ] React frontend deployed to Vercel
- [ ] Tested end-to-end workflow
- [ ] Set up CloudWatch monitoring
- [ ] Configured SNS alerts for failures

## 🆘 Troubleshooting

**Lambda timeout?**
- Increase timeout in Lambda console (currently 5 min)
- Increase memory (more CPU) for faster processing

**Instagram upload fails?**
- Check token is not expired
- Verify business account ID is correct
- Ensure video URL is publicly accessible

**S3 access denied?**
- Verify IAM role has S3 permissions
- Check bucket names are correct
- Review Lambda execution role

## 📞 Next Steps

1. **Try AWS Lambda**: Follow `lambda_deployment/AWS_LAMBDA_SETUP.md`
2. **Deploy React**: Set up React frontend from `VideoEditor.jsx`
3. **Monitor**: Use CloudWatch for Lambda monitoring
4. **Scale**: AWS auto-scales for any number of users

---

**Questions?** Check the detailed guides in each file or AWS Lambda documentation.

**Ready to go serverless?** 🚀 Start with `lambda_deployment/AWS_LAMBDA_SETUP.md`
