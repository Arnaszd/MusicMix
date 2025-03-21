# MP3 Combiner with Silence Removal

This script combines random MP3 files from a folder and removes silence from the beginning and end of each file.

## Requirements

- Python 3.6 or higher
- FFmpeg (required for audio processing)

## Installation

1. Install FFmpeg:
   - Windows: Download from https://ffmpeg.org/download.html and add to PATH
   - Linux: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Create a folder named `input_mp3s` in the same directory as the script
2. Place your MP3 files in the `input_mp3s` folder
3. Run the script:
   ```bash
   python combine_audio.py
   ```

The script will:
- Randomly select 20 MP3 files from the input folder
- Remove silence from the beginning and end of each file
- Combine them into a single MP3 file named `combined_output.mp3`

## Customization

You can modify the following parameters in the script:
- `input_folder`: The folder containing your MP3 files
- `output_file`: The name of the output file
- `num_files`: Number of random files to combine (default: 20)
- Silence detection parameters in the `remove_silence` function:
  - `min_silence_len`: Minimum length of silence to detect (in milliseconds)
  - `silence_thresh`: Silence threshold in dB 