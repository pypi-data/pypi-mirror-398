# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BackgroundRemover is a command-line tool and Python library that removes backgrounds from images and videos using AI-based U-Net models. It supports multiple output formats including transparent videos (.mov), GIFs, and matte keys for video editing software.

**Entry Points (defined in setup.py):**
- `backgroundremover`: Main CLI → `backgroundremover.cmd.cli:main`
- `backgroundremover-server`: HTTP API server → `backgroundremover.cmd.server:main`

**GUI Application:** `background_remover_gui.py` (tkinter-based, run directly with Python)

**Version:** Defined in two places (keep in sync):
- `setup.py` → `version="x.x.x"`
- `backgroundremover/__init__.py` → `__version__ = "x.x.x"`

## Development Commands

### Installation and Setup

```bash
# Install in development mode
pip install --upgrade pip
pip install -e .

# Install dependencies
pip install -r requirements.txt

# Run without installing (development)
python -m backgroundremover.cmd.cli -i "input.jpg" -o "output.png"
```

### Testing the CLI

```bash
# Test image background removal
backgroundremover -i "path/to/image.jpg" -o "output.png"

# Test video with matte key
backgroundremover -i "path/to/video.mp4" -mk -o "output.mov"

# Test with alpha matting (better quality)
backgroundremover -i "path/to/image.jpg" -a -ae 15 -o "output.png"

# Test different models
backgroundremover -i "path/to/image.jpg" -m "u2net_human_seg" -o "output.png"

# Test folder processing
backgroundremover -if "input_folder" -of "output_folder"

# Test pipe support
cat input.jpg | backgroundremover > output.png

# Test HTTP server
backgroundremover-server --addr 0.0.0.0 --port 5000
# Then test with: curl -X POST -F "file=@test.jpg" http://localhost:5000/ -o output.png

# Test GUI application
python background_remover_gui.py
```

### Building and Distribution

```bash
# Build distribution packages
python setup.py sdist bdist_wheel

# Docker build
docker build -t bgremover .
docker run -it --rm -v "$(pwd):/tmp" bgremover:latest -i "input.jpg" -o "output.png"
```

## Architecture

### Core Components

**Entry Point**: `backgroundremover/cmd/cli.py`
- Main command-line interface with argparse
- Handles both single file and folder batch processing
- Routes to appropriate processing function based on file type and flags

**Background Removal**: `backgroundremover/bg.py`
- `remove()`: Core function for image background removal
- `Net`: PyTorch model wrapper that handles model loading and inference
- `alpha_matting_cutout()`: Advanced alpha matting for better edge quality
- `naive_cutout()`: Fast cutout without alpha matting
- Device detection logic (CUDA/MPS/CPU) for optimal performance

**Video Processing**: `backgroundremover/utilities.py`
- `matte_key()`: Generates matte key files (green screen) for video editors
- `transparentvideo()`: Creates transparent .mov files
- `transparentgif()`: Creates transparent GIFs
- `transparentvideoovervideo()`: Overlays transparent video over another video
- `transparentvideooverimage()`: Overlays transparent video over static image
- Multiprocessing architecture with worker pools for parallel frame processing

**Model Management**: `backgroundremover/u2net/`
- `detect.py`: Model loading and prediction logic
- `u2net.py`: U-Net neural network architecture definitions
- `data_loader.py`: Image preprocessing and data transformations

**Model Download**: `backgroundremover/github.py`
- Downloads U2Net models from GitHub repository on first run
- Models stored in `~/.u2net/` directory
- Supports three models: u2net, u2net_human_seg, u2netp
- Implements automatic retry logic with exponential backoff for failed downloads
- Validates file size after download to detect corrupted files

**HTTP Server**: `backgroundremover/cmd/server.py`
- Flask-based HTTP API server with Waitress WSGI server
- Supports both POST (file upload) and GET (URL) methods
- Exposes same parameters as CLI (alpha matting, model selection, etc.)

### Model Types

1. **u2net**: General purpose background removal (default)
2. **u2net_human_seg**: Optimized for human segmentation
3. **u2netp**: Lightweight version for faster processing

### Video Processing Architecture

The video processing system uses a multi-worker architecture:

1. **Frame Ripper Worker**: Extracts frames from video using moviepy
2. **Processing Workers**: Multiple GPU/CPU workers process frames in parallel batches
3. **Frame Buffer**: Shared dictionary managing frame data between workers
4. **Result Aggregation**: Collects processed frames and pipes to ffmpeg

Key parameters:
- `worker_nodes`: Number of parallel workers (default: 1, max recommended: 4)
- `gpu_batchsize`: Batch size for GPU processing (default: 2)
- `framerate`: Override detected framerate
- `framelimit`: Limit frames for testing

**Warning:** Using more than 4 workers (`-wn`) can cause `ConnectionResetError` due to multiprocessing limitations. The CLI now warns about this.

### Device Detection

The codebase automatically detects and uses the best available device:
1. CUDA (NVIDIA GPU) if available
2. MPS (Apple Silicon GPU) if available
3. CPU as fallback

This is set in `backgroundremover/bg.py` via the `DEVICE` global variable.

### Alpha Matting

Alpha matting improves edge quality by:
1. Creating a trimap (foreground/background/unknown regions)
2. Using binary erosion to refine boundaries
3. Estimating alpha channel with closed-form matting
4. Estimating foreground colors

Parameters:
- `-af`: Foreground threshold (default: 240)
- `-ab`: Background threshold (default: 10)
- `-ae`: Erosion structure size (default: 10)
- `-az`: Base size for processing (default: 1000)

## Key Implementation Details

### Model Loading

Models are downloaded on first use and cached in `~/.u2net/`. Large models (u2net, u2net_human_seg) are split into multiple parts (u2aa, u2ab, u2ac, u2ad) and concatenated during download to work around GitHub's file size limits. The u2netp model is small enough to be downloaded as a single file.

Model paths can be overridden via environment variables:
- `U2NET_PATH`: Path to u2net.pth or u2net_human_seg.pth
- `U2NETP_PATH`: Path to u2netp.pth

### Supported File Formats

**Images (input and output):**
- `.jpg`, `.jpeg`: Standard JPEG images
- `.png`: PNG images with transparency support
- `.heic`, `.heif`: HEIC format (requires optional `pillow-heif` package)

**Videos (input):**
- `.mp4`: MP4 video files
- `.mov`: QuickTime video files
- `.webm`: WebM video files
- `.ogg`: Ogg video files
- `.gif`: Animated GIF files

**Videos (output):**
- `.mov`: Transparent video using qtrle codec (for `-tv` flag)
- `.mp4`: Matte key video (for `-mk` flag)
- `.gif`: Transparent GIF (for `-tg` flag)

### Video Frame Processing

Videos are resized to 320px height for processing to balance speed and quality. The multiprocessing architecture ensures efficient GPU utilization by processing frames in batches while the frame ripper continues extracting frames.

### FFmpeg Integration

The tool heavily relies on ffmpeg for:
- Video frame extraction (via moviepy wrapper)
- Alpha channel merging (`alphamerge` filter)
- Format conversion and encoding
- Overlay composition

### Library Usage

The `remove()` function in `backgroundremover/bg.py` can be imported and used programmatically:

```python
from backgroundremover.bg import remove

with open("input.jpg", "rb") as f:
    data = f.read()

result = remove(data, model_name="u2net", alpha_matting=True)

with open("output.png", "wb") as f:
    f.write(result)
```

## Dependencies

Critical dependencies:
- **torch/torchvision**: Neural network inference
- **moviepy**: Video frame extraction
- **ffmpeg-python**: FFmpeg command generation
- **pymatting**: Alpha matting algorithms
- **PIL/Pillow**: Image processing
- **scikit-image**: Image manipulation utilities

## Common Issues

1. **Python version**: Supports Python 3.6+ (recently updated for Python 3.12 compatibility)
2. **FFmpeg requirement**: Must have ffmpeg 4.4+ installed and in PATH
3. **Model download**: First run requires internet connection to download models
4. **Memory usage**: Video processing can be memory-intensive; adjust `gpu_batchsize` and `worker_nodes` accordingly
5. **Multiprocessing**: Uses 'spawn' method for cross-platform compatibility
6. **EOFError on model loading**: Indicates corrupted model file - delete from `~/.u2net/` and rerun to re-download
7. **EXIF orientation**: Images are automatically corrected using `ImageOps.exif_transpose()` to prevent rotation issues
8. **ConnectionResetError with multiple workers**: Reduce worker count with `-wn 1` or `-wn 2`
9. **-toi/-tov requires separate -bi/-bv**: Use `backgroundremover -i video.mp4 -toi -bi background.png -o output.mov` (not `-toi background.png`)

## Key Code Patterns

### Pipe Support (stdin/stdout)
The CLI supports Unix pipes by detecting when `args.input.name == "<stdin>"` or `args.output.name == "<stdout>"`. This allows commands like `cat input.jpg | backgroundremover > output.png`.

### Folder Processing
When using `-if`/`--input-folder`, the code iterates through files, filtering by extension with `is_video_file()` and `is_image_file()` helper functions, then routes each file to appropriate processing function.

### Background Replacement
The `remove()` function in `bg.py` supports three output modes:
1. Transparent cutout (default)
2. Solid color background (via `background_color` RGB tuple)
3. Custom image background (via `background_image` bytes)

### Video Frame Processing Flow
1. `capture_frames()` worker extracts frames using moviepy and stores in shared `frames_dict`
2. Multiple `worker()` processes consume frames in batches from `frames_dict`
3. Each worker uses JIT-traced PyTorch model for faster inference
4. Processed frames stored in shared `results_dict` keyed by output index
5. Main process collects results and pipes to ffmpeg for final video encoding

## Development Notes

### Running without Installation
You can run the tool directly from source without installing:
```bash
python -m backgroundremover.cmd.cli -i "input.jpg" -o "output.png"
python -m backgroundremover.cmd.server --port 5000
```

### Debugging Model Issues
If encountering model loading errors:
1. Check if model exists: `ls -lh ~/.u2net/`
2. Delete corrupted model: `rm ~/.u2net/u2net.pth`
3. Set custom model path: `export U2NET_PATH=/path/to/model.pth`
4. Enable verbose output by examining `github.py` download logs

### Testing Video Processing
Use `-fl` flag to limit frames during development:
```bash
# Process only first 30 frames for quick testing
backgroundremover -i "video.mp4" -tv -fl 30 -o "test.mov"
```

### Modifying Code
When making changes:
- **Background removal logic**: Edit `backgroundremover/bg.py` → `remove()` function
- **CLI arguments**: Edit `backgroundremover/cmd/cli.py` → `argparse` setup
- **Video processing**: Edit `backgroundremover/utilities.py` → worker functions
- **Model architecture**: Edit `backgroundremover/u2net/u2net.py` → U2NET/U2NETP classes
- **HTTP API**: Edit `backgroundremover/cmd/server.py` → Flask routes
- **GUI**: Edit `background_remover_gui.py` → tkinter interface

After modifying, reinstall in development mode: `pip install -e .`
