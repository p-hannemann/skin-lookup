# Skin Copier & Matcher

A powerful tool for finding Minecraft skins in Prism Launcher's skin cache. Match a rendered skin image against cached skin files and automatically identify the matching texture.

**Primary Use Case**: Find the original skin texture file from a 3D rendered character image by searching through Prism Launcher's skin cache.

## Features

### 🔍 Skin Matcher
- **Prism Launcher Integration**: Search through Prism Launcher's skin cache
- **Smart Image Matching**: Compare a rendered skin image against thousands of cached skin files
- **Multiple Algorithms**: Uses color histograms, dominant colors, and perceptual hashing
- **Top N Results**: Find the best 1-20 matches
- **Fast Processing**: Optimized for large directories (10,000+ files)
- **Auto-Copy Results**: Automatically copies matched skins to output folder

### 📁 File Copier
- **Batch Processing**: Recursively copy entire directories
- **Auto Extension**: Adds `.png` extension to all files
- **Merge Mode**: Option to flatten directory structure
- **Progress Tracking**: Real-time progress with ETA
- **Cancellation**: Stop processing anytime with cleanup

### 🖼️ Image Viewer
- **Built-in Viewer**: Browse matched skins or any image directory
- **Keyboard Navigation**: Arrow keys for quick browsing
- **Large Collections**: Handles 10,000+ images smoothly
- **Explorer Integration**: Open file location in Windows Explorer
- **Auto-resize**: Images scale to fit window

## Installation

### Option 1: Download Executable (Windows)
1. Go to [Releases](https://github.com/p-hannemann/skin-lookup/releases)
2. Download `SkinCopier-[version].exe`
3. Run the executable - no installation needed!

**Note:** Windows SmartScreen may show a warning for new downloads. This is normal for unsigned software.
- Click "More info" then "Run anyway" to proceed
- The software is open source and safe to run
- Signing Certificates are expensive so this has to be like this for now 🙃

### Option 2: Run from Source
```bash
# Clone the repository
git clone https://github.com/p-hannemann/skin-lookup.git
cd skin-lookup

# Install dependencies
pip install pillow numpy imagehash

# Run the application
python gui_main.py
```

## Usage

### Skin Matcher Tab

1. **Select Input Image**: Choose the rendered skin image (screenshot from Minecraft/Prism Launcher)
2. **Select Search Directory**: Navigate to Prism Launcher's skin cache folder:
   - Default location: `C:\Users\[YourUsername]\AppData\Roaming\PrismLauncher\assets\skins`
   - Or find it in your Prism Launcher installation directory: `[PrismLauncher]\assets\skins`
3. **Set Number of Matches**: Select how many top matches to find (1-20)
4. **Click "Find Matching Skins"**: Start the search
5. **View Results**: Matched skins are copied to `./output/` folder
6. **Click "View Matches"**: Browse the matched skins in the built-in viewer

**Finding Your Prism Launcher Skin Cache:**
```
Windows: C:\Users\[Username]\AppData\Roaming\PrismLauncher\assets\skins
Linux: ~/.local/share/PrismLauncher/assets/skins
macOS: ~/Library/Application Support/PrismLauncher/assets/skins
```

**Tips:**
- Works best with clear, front-facing skin renders
- The skin cache may contain thousands of files - be patient during first search
- Progress and ETA are shown in real-time
- Matched files are named with hash values - use the viewer to identify them visually

### File Copier Tab

1. **Select Input Folder**: Choose the directory to copy
2. **Optional: Enable Merge Mode**: Flatten all files into a single folder
3. **Click "Copy and Add .png Extension"**: Start copying
4. **Output**: Files are copied to `[input_folder]_png/`
5. **Click "View Output Images"**: Browse the copied files

**Tips:**
- Output folder is created automatically
- If output exists, you'll be asked to overwrite
- Cancel anytime - partial work is cleaned up

### Image Viewer

- **Navigation**: Use arrow keys or click Previous/Next buttons
- **Explorer**: Click "Open in Explorer" to see file location
- **Large Collections**: Images load in background, UI stays responsive



## Building from Source

### Create Executable with PyInstaller
```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name="SkinCopier" gui_main.py
```

The executable will be in `dist/SkinCopier.exe`

## Project Structure

```
.
├── gui_main.py         # Main GUI application
├── image_matcher.py    # Image comparison algorithms
├── skin_matcher.py     # Skin matching operations
├── file_utils.py       # File copying utilities
├── image_viewer.py     # Image viewer window
└── .github/
    └── workflows/
        └── build-exe.yml  # Automatic builds
```

## Requirements

- Python 3.11+
- PIL/Pillow
- NumPy
- ImageHash

## How It Works

### Prism Launcher Skin Cache

Prism Launcher stores downloaded Minecraft skins in a cache folder using hash-based filenames (e.g., `3e0d61a212d478a594f990a99c5683ca0f1b9b98`). These files have no extension and are stored in subdirectories.

This tool helps you:
1. Take a screenshot or render of a Minecraft character
2. Find the matching skin texture file in Prism Launcher's cache
3. Extract and view the original skin texture

### Image Matching Algorithm

The matcher uses a weighted combination of three techniques:

1. **Dominant Colors (60%)**: Extracts and compares the most prominent colors
2. **Color Histogram (35%)**: Analyzes overall color distribution
3. **Perceptual Hash (5%)**: Checks structural similarity

This balanced approach works well for matching rendered 3D character images to flat skin texture files stored in Prism Launcher's cache.

## Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## Credits

☕ Made by **SoulReturns**  
Discord: **soulreturns**

## License

This project is open source and available under the MIT License.
