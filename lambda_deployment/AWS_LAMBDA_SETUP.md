# AWS Lambda Deployment Guide

## Overview
This serverless setup allows you to process videos without managing any servers. Cost: ~$2-10/month for moderate usage.

## Architecture

```
User Uploads Videos (via API/Web)
           ↓
    AWS S3 (Input Bucket)
           ↓
    S3 Event → Lambda Trigger
           ↓
    Lambda Function (processes video)
           ↓
    AWS S3 (Output Bucket)
           ↓
    Post to Instagram
           ↓
    Store Result
```

## Prerequisites

1. **AWS Account** (Free tier available)
2. **AWS CLI** installed locally:
   ```bash
   pip install awscli
   ```
3. **Configured AWS credentials**:
   ```bash
   aws configure
   ```

## Step 1: Create S3 Buckets

```bash
# Input bucket for user uploads
aws s3 mb s3://video-editor-input-$(date +%s)

# Output bucket for processed videos
aws s3 mb s3://video-editor-output-$(date +%s)

# Store the bucket names
export INPUT_BUCKET="video-editor-input-xxx"
export OUTPUT_BUCKET="video-editor-output-xxx"
```

## Step 2: Create IAM Role for Lambda

```bash
# Create trust policy
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name VideoEditorLambdaRole \
  --assume-role-policy-document file://trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name VideoEditorLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
  --role-name VideoEditorLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

## Step 3: Create FFmpeg Layer

Lambda needs FFmpeg for video processing. Create a layer:

```bash
# Create layer directory
mkdir -p lambda-layer/python

# Download FFmpeg for Lambda (Amazon Linux 2)
cd lambda-layer
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar xf ffmpeg-release-amd64-static.tar.xz
cp ffmpeg-*/ffmpeg python/
cp ffmpeg-*/ffprobe python/

# Zip the layer
zip -r ffmpeg-layer.zip .

# Upload layer
aws lambda publish-layer-version \
  --layer-name video-editor-ffmpeg \
  --zip-file fileb://ffmpeg-layer.zip \
  --compatible-runtimes python3.11
```

Store the layer ARN returned.

## Step 4: Package Lambda Function

```bash
# Create deployment package
mkdir -p deployment
cd deployment

# Copy Lambda function
cp ../lambda_handler.py .
cp ../vi_lambda.py vi.py

# Install dependencies
pip install -r ../requirements.txt -t .

# Zip everything
zip -r lambda-function.zip .

# File size check (should be < 250MB)
ls -lh lambda-function.zip
```

## Step 5: Deploy Lambda Function

```bash
# Get your AWS Account ID
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/VideoEditorLambdaRole"
export LAYER_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:layer:video-editor-ffmpeg:1"

# Create Lambda function
aws lambda create-function \
  --function-name VideoEditorFunction \
  --runtime python3.11 \
  --role $ROLE_ARN \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://lambda-function.zip \
  --timeout 300 \
  --memory-size 3008 \
  --layers $LAYER_ARN \
  --environment Variables="{
    INSTAGRAM_BUSINESS_ACCOUNT_ID=$INSTAGRAM_BUSINESS_ACCOUNT_ID,
    INSTAGRAM_ACCESS_TOKEN=$INSTAGRAM_ACCESS_TOKEN,
    OUTPUT_BUCKET=$OUTPUT_BUCKET
  }"
```

## Step 6: Create S3 Event Trigger

```bash
# Create notification configuration
cat > s3-notification.json << EOF
{
  "LambdaFunctionConfigurations": [
    {
      "LambdaFunctionArn": "arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:VideoEditorFunction",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "prefix",
              "Value": "uploads/"
            },
            {
              "Name": "suffix",
              "Value": ".json"
            }
          ]
        }
      }
    }
  ]
}
EOF

# Add Lambda permission for S3
aws lambda add-permission \
  --function-name VideoEditorFunction \
  --statement-id AllowExecutionFromS3 \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::$INPUT_BUCKET

# Set S3 notification
aws s3api put-bucket-notification-configuration \
  --bucket $INPUT_BUCKET \
  --notification-configuration file://s3-notification.json
```

## Step 7: Create React Frontend

Users will upload videos via a React app that:
1. Uploads videos to S3 (pre-signed URLs)
2. Creates metadata file that triggers Lambda
3. Polls for completion
4. Downloads final video

See `REACT_FRONTEND.md` for complete React setup.

## Cost Estimation

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| Lambda  | 100 jobs (20min each) | $2.50 |
| S3 Storage | 50GB input + 50GB output | $2.30 |
| S3 Requests | 1000 uploads + processing | $0.50 |
| Data Transfer | 50GB out | $4.50 |
| **Total** | | **~$10/month** |

**Free tier covers**:
- First 1M Lambda requests
- First 5GB S3 storage
- First 100K PUT requests

## Testing Locally

```bash
# Test Lambda locally with sam
pip install aws-sam-cli

# Build
sam build

# Test with local event
sam local invoke VideoEditorFunction -e test-event.json
```

## Monitoring

```bash
# View Lambda logs
aws logs tail /aws/lambda/VideoEditorFunction --follow

# Monitor invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=VideoEditorFunction \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## Troubleshooting

### Lambda timeout
- Increase timeout (currently 300s = 5min)
- Video might take longer than expected
- Increase memory (more CPU) for faster processing

### File too large
- Lambda has 250MB deployment limit
- Use Lambda layers for FFmpeg (done above)
- Keep code minimal

### S3 access denied
- Check IAM role has S3 permissions
- Verify bucket names are correct
- Check CORS settings if needed

## Next Steps

1. Set up all AWS resources using this guide
2. Create React frontend (see REACT_FRONTEND.md)
3. Test end-to-end workflow
4. Monitor costs and optimize
5. Set up CloudFront for faster downloads (optional)

## Cleanup (Delete Everything)

```bash
# Delete Lambda function
aws lambda delete-function --function-name VideoEditorFunction

# Delete Lambda layers
aws lambda delete-layer-version --layer-name video-editor-ffmpeg --version-number 1

# Delete IAM role
aws iam detach-role-policy --role-name VideoEditorLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name VideoEditorLambdaRole

# Delete S3 buckets (CAUTION: This deletes all data)
aws s3 rm s3://$INPUT_BUCKET --recursive
aws s3 rb s3://$INPUT_BUCKET

aws s3 rm s3://$OUTPUT_BUCKET --recursive
aws s3 rb s3://$OUTPUT_BUCKET
```

---

**Total setup time**: ~30 minutes
**Skill level**: Intermediate (AWS knowledge helpful)
**Difficulty**: Medium (follow commands in order)

For help, see AWS Lambda documentation: https://docs.aws.amazon.com/lambda/
