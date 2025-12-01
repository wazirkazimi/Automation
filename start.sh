#!/bin/bash
# Quick start script for local development

echo "🚀 Video Reel Creator - Local Development Setup"
echo "=================================================="

# Check Python version
echo "Checking Python version..."
python --version

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate  # Windows Git Bash
else
    source venv/bin/activate  # macOS/Linux
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check FFmpeg
echo ""
echo "Checking FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg found: $(ffmpeg -version | head -n1)"
else
    echo "⚠️  FFmpeg not found. Install with:"
    echo "   Windows: scoop install ffmpeg"
    echo "   macOS: brew install ffmpeg"
    echo "   Linux: sudo apt-get install ffmpeg"
fi

# Create folders
echo "Creating upload/output folders..."
mkdir -p uploads outputs

# Run app
echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Starting app on http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

export FLASK_ENV=development
python app.py
