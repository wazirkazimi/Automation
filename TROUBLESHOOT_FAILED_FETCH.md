# 🔧 Troubleshooting: "Failed to Fetch" Error

## ❌ What This Error Means

**"Failed to fetch"** appears when the browser JavaScript tries to connect to the Flask backend server but cannot reach it.

## ✅ Solutions (Try These in Order)

### 1. **Start the Flask Server** (Most Common Fix)

The Flask app needs to be running BEFORE you access it in the browser.

**Windows:**
```bash
python app.py
```

**macOS/Linux:**
```bash
python app.py
```

You should see:
```
🚀 Starting Video Reel Creator on http://localhost:5000
Environment: development
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

✅ **If you see this, the server is running!**

---

### 2. **Check the URL**

Open browser to:
```
http://localhost:5000
```

❌ **Don't use:**
- `http://127.0.0.1:5000` (might work but less reliable on Windows)
- `http://0.0.0.0:5000` (can't access from browser)
- `https://localhost:5000` (wrong protocol)

---

### 3. **Check Port 5000 is Available**

If you see this error:
```
OSError: [Errno 10048] Only one usage of each socket address (protocol/IP)
```

**Windows - Kill process on port 5000:**
```powershell
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**macOS/Linux:**
```bash
lsof -i :5000
kill -9 <PID>
```

---

### 4. **Check Browser Console for Details**

1. Open browser **Developer Tools** (Press **F12**)
2. Go to **Console** tab
3. Try uploading a video again
4. Look for error messages like:
   - `Connection refused` → Server not running
   - `ERR_NAME_NOT_RESOLVED` → Wrong domain/URL
   - `CORS error` → Check environment variables

---

### 5. **Check Firewall**

Windows Firewall might block Flask:

**Windows:**
1. Go to **Settings** → **Privacy & Security** → **Firewall**
2. Click **Allow an app through firewall**
3. Make sure **Python** is in the allowed list
4. Or temporarily disable firewall for testing

**macOS:**
```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
```

---

### 6. **Check Network Configuration**

Flask should be accessible on your network interface:

```bash
# Test if server is listening
netstat -an | findstr LISTENING  # Windows
lsof -i :5000                     # macOS/Linux
```

Look for:
```
LISTENING  0.0.0.0:5000
```

---

### 7. **Verify Dependencies Are Installed**

```bash
pip install -r requirements.txt
python -c "import flask; import moviepy; print('✅ All imports OK')"
```

---

### 8. **Test with curl** (Command Line)

**Windows (PowerShell):**
```powershell
curl http://localhost:5000
```

**macOS/Linux:**
```bash
curl http://localhost:5000
```

Should return HTML (the form). If this fails, server isn't running.

---

## 🧪 Step-by-Step Debugging

### Scenario 1: Server Running, Still Getting Error

**Actions:**
1. Check browser console (F12)
2. Open **Network** tab
3. Try uploading
4. See what request failed
5. Check Flask terminal for errors

### Scenario 2: Server Not Starting

**Error:** `ModuleNotFoundError: No module named 'flask'`

**Fix:**
```bash
pip install -r requirements.txt
python app.py
```

### Scenario 3: Port Already in Use

**Error:** `Address already in use`

**Windows:**
```powershell
netstat -ano | findstr :5000
taskkill /PID 1234 /F  # Replace 1234 with actual PID
python app.py
```

---

## 📋 Checklist Before Uploading

- [ ] Run `python app.py`
- [ ] See "Running on http://0.0.0.0:5000" in terminal
- [ ] Open `http://localhost:5000` in browser
- [ ] Form loads successfully
- [ ] Both video file inputs are visible
- [ ] Console shows no errors (F12)

---

## 💡 Better Error Messages (Now Available!)

I've updated the app to show better error messages. Now you'll see:

✅ **Instead of:** "❌ Error: Failed to fetch"

✅ **You'll see:** "❌ Error: Cannot connect to server. Make sure Flask is running on http://localhost:5000"

Plus console logs will show:
- `Sending request to /process...`
- `Response status: 202`
- `Job ID received: abc123...`

---

## 🆘 Still Not Working?

Try this complete reset:

```bash
# 1. Kill any Flask processes
# Windows: taskkill /F /IM python.exe
# macOS/Linux: killall python

# 2. Clear old sessions
rmdir /S uploads outputs 2>nul
mkdir uploads outputs

# 3. Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# 4. Start fresh
python app.py
```

Then:
1. Open `http://localhost:5000`
2. Press **F12** → **Console**
3. Try uploading a small test video
4. Screenshot the console output
5. Share that in bug report

---

## 📞 Quick Reference

| Error | Cause | Fix |
|-------|-------|-----|
| "Failed to fetch" | Server not running | `python app.py` |
| Connection refused | Port in use | `taskkill /F /IM python.exe` |
| Page won't load | Wrong URL | Use `http://localhost:5000` |
| CORS error | Domain mismatch | Set `CORS_ORIGINS` env var |
| 500 error | Python error | Check Flask terminal for traceback |
| Timeout | Video too large | Use smaller test video |

---

## ✅ Success Signs

✓ Form loads at `http://localhost:5000`  
✓ Can select files  
✓ Click "Create Video"  
✓ Progress bar appears  
✓ See console logs with `Sending request to /process...`  
✓ Response shows `status: 202`  
✓ Progress updates every second  
✓ Video preview appears when done  

---

**Questions?** Check the console (F12) for detailed error messages!
