#!/bin/bash
# AWS Lambda Setup Quick Script
# Automates most of the AWS Lambda deployment
# Prerequisites: AWS CLI configured, AWS account with permissions

set -e

echo "🚀 AWS Lambda Video Editor Setup"
echo "================================"

# Configuration
FUNCTION_NAME="VideoEditorFunction"
ROLE_NAME="VideoEditorLambdaRole"
INPUT_BUCKET="video-editor-input-$(date +%s)"
OUTPUT_BUCKET="video-editor-output-$(date +%s)"
LAYER_NAME="video-editor-ffmpeg"
REGION="${AWS_REGION:-us-east-1}"

# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account ID: $ACCOUNT_ID"
echo "Region: $REGION"

# Step 1: Create S3 Buckets
echo ""
echo "📦 Creating S3 buckets..."
aws s3 mb s3://$INPUT_BUCKET --region $REGION
aws s3 mb s3://$OUTPUT_BUCKET --region $REGION
echo "✓ Input bucket: s3://$INPUT_BUCKET"
echo "✓ Output bucket: s3://$OUTPUT_BUCKET"

# Step 2: Create IAM Role
echo ""
echo "🔐 Creating IAM role..."

# Create trust policy file
cat > trust-policy.json << 'EOF'
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
  --role-name $ROLE_NAME \
  --assume-role-policy-document file://trust-policy.json 2>/dev/null || echo "Role already exists"

ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

# Attach policies
aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole 2>/dev/null || true

aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess 2>/dev/null || true

echo "✓ IAM Role: $ROLE_ARN"

# Step 3: Package Lambda Function
echo ""
echo "📦 Packaging Lambda function..."
mkdir -p deployment
cd deployment

# Copy files
cp ../lambda_handler.py .
cp ../vi_lambda.py vi.py

# Install dependencies
pip install -r ../requirements.txt -t . -q

# Zip
zip -r lambda-function.zip . > /dev/null 2>&1
FILE_SIZE=$(ls -lh lambda-function.zip | awk '{print $5}')
echo "✓ Package size: $FILE_SIZE"

cd ..

# Step 4: Create Lambda Function
echo ""
echo "⚙️  Creating Lambda function..."

# Wait for role to be available
sleep 5

aws lambda create-function \
  --function-name $FUNCTION_NAME \
  --runtime python3.11 \
  --role $ROLE_ARN \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://deployment/lambda-function.zip \
  --timeout 300 \
  --memory-size 3008 \
  --environment Variables="{
    OUTPUT_BUCKET=$OUTPUT_BUCKET,
    INSTAGRAM_BUSINESS_ACCOUNT_ID=YOUR_ACCOUNT_ID,
    INSTAGRAM_ACCESS_TOKEN=YOUR_TOKEN
  }" \
  --region $REGION 2>/dev/null || echo "Function already exists"

echo "✓ Lambda Function: $FUNCTION_NAME"

# Step 5: Configure S3 Event Trigger
echo ""
echo "📬 Setting up S3 event notification..."

# Add permission
aws lambda add-permission \
  --function-name $FUNCTION_NAME \
  --statement-id AllowExecutionFromS3 \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::$INPUT_BUCKET \
  --region $REGION 2>/dev/null || true

# Create notification config
cat > s3-notification.json << 'EOF'
{
  "LambdaFunctionConfigurations": [
    {
      "LambdaFunctionArn": "LAMBDA_ARN",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {"Name": "prefix", "Value": "uploads/"},
            {"Name": "suffix", "Value": ".json"}
          ]
        }
      }
    }
  ]
}
EOF

LAMBDA_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${FUNCTION_NAME}"
sed -i "s|LAMBDA_ARN|$LAMBDA_ARN|g" s3-notification.json

aws s3api put-bucket-notification-configuration \
  --bucket $INPUT_BUCKET \
  --notification-configuration file://s3-notification.json \
  --region $REGION 2>/dev/null || true

echo "✓ S3 Event trigger configured"

# Summary
echo ""
echo "✅ Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Update Instagram credentials in Lambda console"
echo "2. Deploy React frontend"
echo "3. Test the workflow"
echo ""
echo "📊 Configuration Summary:"
echo "  Function: $FUNCTION_NAME"
echo "  Role: $ROLE_ARN"
echo "  Input Bucket: $INPUT_BUCKET"
echo "  Output Bucket: $OUTPUT_BUCKET"
echo "  Region: $REGION"
echo ""
echo "💾 Save these values in your .env:"
echo "AWS_REGION=$REGION"
echo "INPUT_BUCKET=$INPUT_BUCKET"
echo "OUTPUT_BUCKET=$OUTPUT_BUCKET"
echo "LAMBDA_FUNCTION=$FUNCTION_NAME"
echo ""
echo "🚀 View logs:"
echo "  aws logs tail /aws/lambda/$FUNCTION_NAME --follow"
echo ""
echo "💰 Estimated cost: $2-10/month for moderate usage"
