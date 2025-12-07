# ngrok Setup Guide for Instagram Upload

## Quick Setup Steps

### 1. Download ngrok
1. Visit: https://ngrok.com/download
2. Download the Windows version (ZIP file)
3. Extract the `ngrok.exe` file to a folder (e.g., `C:\ngrok\`)

### 2. Add ngrok to PATH (Optional but Recommended)
1. Copy `ngrok.exe` to a folder in your PATH, OR
2. Add the folder containing `ngrok.exe` to your system PATH

**Quick PATH setup:**
- Press `Win + X` → System → Advanced system settings
- Click "Environment Variables"
- Under "System variables", find "Path" and click "Edit"
- Click "New" and add the folder path where ngrok.exe is located
- Click OK on all dialogs

### 3. Sign up for ngrok (Free)
1. Visit: https://dashboard.ngrok.com/signup
2. Create a free account
3. Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken

### 4. Configure ngrok
```powershell
ngrok config add-authtoken YOUR_AUTHTOKEN_HERE
```

### 5. Start ngrok tunnel
In a new terminal window:
```powershell
ngrok http 5000
```

### 6. Update .env file
Copy the HTTPS URL from ngrok (e.g., `https://abc123.ngrok.io`) and update your `.env`:
```
PUBLIC_VIDEO_URL=https://abc123.ngrok.io
```

### 7. Restart your Flask app
Restart your Flask application so it picks up the new environment variable.

## Alternative: Use ngrok in the same terminal
If you want to run ngrok in the background, you can use:
```powershell
Start-Process ngrok -ArgumentList "http", "5000"
```

## Testing
1. Start your Flask app: `python app.py`
2. Start ngrok: `ngrok http 5000`
3. Copy the HTTPS forwarding URL from ngrok
4. Update `.env` with that URL
5. Restart Flask app
6. Try uploading to Instagram again

## Note
- The free ngrok URL changes every time you restart ngrok (unless you have a paid plan)
- You'll need to update `PUBLIC_VIDEO_URL` in `.env` each time
- For production, deploy to a public server instead of using ngrok

