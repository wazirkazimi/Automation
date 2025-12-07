# Google Drive API Setup Guide

This guide will help you set up Google Drive API to automatically upload videos.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter a project name (e.g., "Video Automation")
4. Click "Create"

## Step 2: Enable Google Drive API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Google Drive API"
3. Click on it and press "Enable"

## Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" (unless you have a Google Workspace)
   - Fill in required fields (App name, User support email, Developer contact)
   - Add scopes: `https://www.googleapis.com/auth/drive.file`
   - Add test users (your Google account email)
   - Save and continue
4. Back to Credentials:
   - Application type: "Desktop app"
   - Name: "Video Automation Client"
   - Click "Create"
5. Download the credentials JSON file
6. Rename it to `credentials.json` and place it in your project root directory

## Step 4: Install Required Packages

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

## Step 5: First-Time Authentication

1. Run your Flask app: `python app.py`
2. The first time you process a video, it will open a browser window
3. Sign in with your Google account
4. Grant permissions to access Google Drive
5. A `token.json` file will be created (this stores your authentication)

## Step 6: Optional - Set Default Folder

If you want all videos uploaded to a specific Google Drive folder:

1. Create a folder in Google Drive
2. Right-click the folder → "Get link" → "Anyone with the link can view"
3. Copy the folder ID from the URL:
   - URL format: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
   - Copy the `FOLDER_ID_HERE` part
4. Add to your `.env` file:
   ```
   GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
   ```

## Step 7: Update .env File

Add these optional variables to your `.env`:

```env
# Google Drive API (Optional)
GOOGLE_DRIVE_CREDENTIALS_FILE=credentials.json
GOOGLE_DRIVE_TOKEN_FILE=token.json
GOOGLE_DRIVE_FOLDER_ID=  # Optional: specific folder ID
```

## How It Works

When you process videos:

1. **Input Videos** (gameplay and meme) are uploaded to:
   - `Video_{job_id}/Input Videos/`
   - Files: `gameplay_{job_id}.mp4` and `meme_{job_id}.mp4`

2. **Final Video** is uploaded to:
   - `Video_{job_id}/Final Videos/`
   - File: `final_{job_id}.mp4`

3. **Instagram Upload** uses the Google Drive link automatically
   - No need for ngrok or public server!
   - Google Drive links are publicly accessible

## Troubleshooting

### "Credentials file not found"
- Make sure `credentials.json` is in the project root directory
- Check the file name matches exactly

### "Access denied" or "Permission denied"
- Make sure you've enabled Google Drive API
- Check that you've added your email as a test user in OAuth consent screen
- Delete `token.json` and re-authenticate

### "File not publicly accessible"
- The script automatically makes files public
- If Instagram can't access, check the file permissions in Google Drive
- Right-click file → "Get link" → Ensure it's set to "Anyone with the link"

### Files not uploading
- Check your internet connection
- Verify Google Drive API is enabled
- Check the logs for error messages
- Ensure you have enough Google Drive storage space

## Security Notes

- `credentials.json` contains your OAuth client secrets - keep it private
- `token.json` contains your access token - keep it private
- Add both to `.gitignore` (already included)
- Never commit these files to version control

## Benefits

✅ **No ngrok needed** - Google Drive links work directly with Instagram  
✅ **Automatic backup** - All videos are saved to Google Drive  
✅ **Organized structure** - Videos organized by job ID  
✅ **Public access** - Files automatically made public for Instagram  

