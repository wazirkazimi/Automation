# Instagram API Token Management Guide

## Overview
Instagram access tokens are required for posting videos to Instagram using the Graph API. These tokens expire and need periodic refresh.

## Token Types

### 1. Short-lived Access Tokens (1-2 hours)
- Generated during Instagram app authorization
- Valid for 1-2 hours only
- Used for initial testing

### 2. Long-lived Access Tokens (60 days)
- Extended from short-lived tokens
- Valid for 60 days
- Recommended for production

## Current Status
Your Instagram access token expired on **Saturday, 06-Dec-25 13:00:00 PST**.

## Development Mode Solution
To test locally without Instagram API:

1. **Environment Setup**:
   ```bash
   # In your .env file
   FLASK_ENV=development
   # INSTAGRAM_ACCESS_TOKEN=   # Comment out or leave empty
   # INSTAGRAM_BUSINESS_ACCOUNT_ID=   # Comment out or leave empty
   ```

2. **Behavior in Development Mode**:
   - Instagram posting is automatically skipped
   - Video processing still works normally
   - Google Drive backup still functions (if configured)
   - No Instagram API calls are made

## Refreshing Instagram Token

### Method 1: Get New Long-lived Token
1. Visit Facebook Developer Console
2. Go to your app > Tools & Support > Access Token Tool
3. Select your Instagram Business Account
4. Generate a new User Access Token
5. Exchange for long-lived token:
   ```bash
   curl -i -X GET "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={short-lived-token}"
   ```

### Method 2: Extend Current Token (if not expired)
```bash
curl -i -X GET "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={current-token}"
```

### Method 3: Instagram Basic Display API (Alternative)
If using Instagram Basic Display API instead of Graph API:
1. Go to [Instagram Basic Display](https://developers.facebook.com/apps/)
2. Generate new access token for your app
3. Use the provided token

## Production Deployment

### For Railway/Render
1. Get a fresh long-lived token (60-day validity)
2. Add to environment variables:
   ```
   INSTAGRAM_ACCESS_TOKEN=your-new-token
   INSTAGRAM_BUSINESS_ACCOUNT_ID=your-account-id
   FLASK_ENV=production
   ```
3. Deploy the app

### Token Monitoring
Set up alerts for token expiration:
- Tokens expire every 60 days
- Instagram API will return error code 190 when expired
- Implement automatic token refresh if needed

## API Credentials Needed

### Instagram Graph API
- **App ID**: Your Facebook App ID
- **App Secret**: Your Facebook App Secret  
- **Business Account ID**: Instagram Business Account ID
- **Access Token**: Long-lived user access token

### Current Configuration
```
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841478601395535
INSTAGRAM_ACCESS_TOKEN=[EXPIRED - needs refresh]
```

## Testing Workflow

### Local Testing (Development Mode)
```bash
# 1. Set environment
FLASK_ENV=development

# 2. Run Flask app
python app.py

# 3. Test video upload - Instagram will be skipped
curl -X POST http://localhost:5000/process \
  -F "meme_video=@test_meme.mp4" \
  -F "gameplay_video=@test_gameplay.mp4" \
  -F "caption=Test Video"
```

### Production Testing (With Valid Token)
```bash
# 1. Set environment
FLASK_ENV=production
INSTAGRAM_ACCESS_TOKEN=your-valid-token

# 2. Deploy and test full workflow
# Video will be posted to Instagram
```

## Troubleshooting

### Error Code 190 (Session Expired)
- **Cause**: Access token has expired
- **Solution**: Refresh the access token using methods above

### Error Code 400 (Bad Request)
- **Cause**: Invalid parameters or token
- **Solution**: Check token validity and API parameters

### Error Code 403 (Forbidden)
- **Cause**: Insufficient permissions
- **Solution**: Verify app permissions include `instagram_basic` and `instagram_content_publish`

## Backup Strategy

If Instagram API is consistently problematic:

1. **Development**: Use development mode bypass
2. **Production**: Consider implementing:
   - Manual Instagram posting workflow
   - Alternative social media APIs (TikTok, Twitter)
   - Direct video hosting (Google Drive, AWS S3)

## Next Steps

1. ✅ Development mode implemented - can test locally
2. 🔄 Get new Instagram long-lived token for production
3. ⏳ Update production environment variables
4. ⏳ Test full production deployment