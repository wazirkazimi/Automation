import express from 'express';
import multer from 'multer';
import ffmpeg from 'fluent-ffmpeg';
import ffmpegStatic from 'ffmpeg-static';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

ffmpeg.setFfmpegPath(ffmpegStatic);

const app = express();
const PORT = 3000;

// Configure storage
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = path.join(__dirname, 'uploads');
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + '-' + file.originalname);
  },
});

const upload = multer({
  storage: storage,
  fileFilter: (req, file, cb) => {
    const allowedMimes = ['video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo'];
    if (allowedMimes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Only video files are allowed'));
    }
  },
  limits: {
    fileSize: 500 * 1024 * 1024, // 500MB
  },
});

// Serve static files
app.use(express.static(__dirname));

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'Server is running' });
});

// Upload and process videos
app.post('/upload', upload.fields([
  { name: 'memeVideo', maxCount: 1 },
  { name: 'gameplayVideo', maxCount: 1 },
]), async (req, res) => {
  try {
    if (!req.files || !req.files.memeVideo || !req.files.gameplayVideo) {
      return res.status(400).json({
        success: false,
        message: 'Both video files are required',
      });
    }

    const memeFile = req.files.memeVideo[0];
    const gameplayFile = req.files.gameplayVideo[0];
    const outputDir = path.join(__dirname, 'downloads');
    const outputPath = path.join(outputDir, `output-${Date.now()}.mp4`);

    // Create downloads directory if it doesn't exist
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    console.log(`Processing: ${memeFile.path} + ${gameplayFile.path}`);

    // FFmpeg command
    const command = ffmpeg()
      .input(memeFile.path)
      .input(gameplayFile.path)
      .complexFilter([
        {
          filter: 'scale',
          options: { w: 1080, h: 960 },
          inputs: '0:v',
          outputs: 'top',
        },
        {
          filter: 'scale',
          options: { w: 1080, h: 960 },
          inputs: '1:v',
          outputs: 'bottom',
        },
        {
          filter: 'vstack',
          options: { inputs: 2 },
          inputs: ['top', 'bottom'],
          outputs: 'stacked',
        },
      ])
      .audioCodec('aac')
      .videoCodec('libx264')
      .outputOptions(['-map', '[stacked]', '-map', '0:a?', '-preset', 'ultrafast'])
      .save(outputPath);

    let processingStarted = false;

    command.on('start', () => {
      processingStarted = true;
      console.log('FFmpeg process started');
    });

    command.on('progress', (progress) => {
      console.log(`Progress: ${Math.round(progress.percent)}%`);
    });

    command.on('end', () => {
      console.log('Video processing completed');

      // Clean up input files
      fs.unlink(memeFile.path, (err) => {
        if (err) console.error('Error deleting meme file:', err);
      });
      fs.unlink(gameplayFile.path, (err) => {
        if (err) console.error('Error deleting gameplay file:', err);
      });

      // Send success response
      res.json({
        success: true,
        message: 'Video merged successfully',
        downloadUrl: `/download/${path.basename(outputPath)}`,
      });
    });

    command.on('error', (err) => {
      console.error('FFmpeg error:', err);

      // Clean up files
      fs.unlink(memeFile.path, (err) => {
        if (err) console.error('Error deleting meme file:', err);
      });
      fs.unlink(gameplayFile.path, (err) => {
        if (err) console.error('Error deleting gameplay file:', err);
      });

      if (fs.existsSync(outputPath)) {
        fs.unlink(outputPath, (err) => {
          if (err) console.error('Error deleting output file:', err);
        });
      }

      res.status(500).json({
        success: false,
        message: 'Error processing videos: ' + err.message,
      });
    });
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error: ' + error.message,
    });
  }
});

// Download processed video
app.get('/download/:filename', (req, res) => {
  try {
    const filename = req.params.filename;
    const filepath = path.join(__dirname, 'downloads', filename);
    const isDownload = req.query.download === 'true';

    // Prevent directory traversal attacks
    if (!filepath.startsWith(path.join(__dirname, 'downloads'))) {
      return res.status(403).json({ error: 'Access denied' });
    }

    if (!fs.existsSync(filepath)) {
      return res.status(404).json({ error: 'File not found' });
    }

    const stat = fs.statSync(filepath);
    const fileSize = stat.size;

    // Handle range requests for video streaming
    const range = req.headers.range;
    if (range) {
      const parts = range.replace(/bytes=/, '').split('-');
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
      const chunksize = end - start + 1;

      res.writeHead(206, {
        'Content-Range': `bytes ${start}-${end}/${fileSize}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': chunksize,
        'Content-Type': 'video/mp4',
        'Content-Disposition': isDownload ? 'attachment; filename="output.mp4"' : 'inline',
      });
      fs.createReadStream(filepath, { start, end }).pipe(res);
    } else {
      res.writeHead(200, {
        'Content-Length': fileSize,
        'Content-Type': 'video/mp4',
        'Accept-Ranges': 'bytes',
        'Content-Disposition': isDownload ? 'attachment; filename="output.mp4"' : 'inline',
      });
      fs.createReadStream(filepath).pipe(res);
    }
  } catch (error) {
    console.error('Download error:', error);
    res.status(500).json({ error: 'Download error' });
  }
});

app.listen(PORT, () => {
  console.log(`Server is running at http://localhost:${PORT}`);
  console.log('Open your browser and navigate to http://localhost:3000');
});
