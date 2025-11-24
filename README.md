# Skin Lookup Tool

Find and match Minecraft skins in Prism Launcher's cache using AI-powered image comparison. Identify the original skin texture from a 3D rendered character image.

## ✨ Features

- **🔍 Smart Matching** - Multi-algorithm comparison (color histograms, perceptual hashing, dominant colors)
  ![Skin Matcher Interface](https://private-user-images.githubusercontent.com/62304958/517998841-591bb810-efe9-4f5e-a7f3-34d36ca3d13f.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjM5NzI2MjEsIm5iZiI6MTc2Mzk3MjMyMSwicGF0aCI6Ii82MjMwNDk1OC81MTc5OTg4NDEtNTkxYmI4MTAtZWZlOS00ZjVlLWE3ZjMtMzRkMzZjYTNkMTNmLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTExMjQlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUxMTI0VDA4MTg0MVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTY5ZTAwMjMwNTFhZjY2NGE2MmYzMmIxN2M0M2IwZmY5Yzc4NWQwNzJlMjEzOWU3YzBhOTVlYTc2ZTlkOGRmMjkmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.V1Kij_DULgs3TOECb4271R7XD6Dq1KaC2l_PQ0o2CsU)

- **📂 Batch Processing** - Copy and rename entire directories with .png extension
  ![File Copier Interface](https://private-user-images.githubusercontent.com/62304958/517998956-699b9902-78e5-4bd7-9f8e-b133ae3fd0ac.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjM5NzI2MjEsIm5iZiI6MTc2Mzk3MjMyMSwicGF0aCI6Ii82MjMwNDk1OC81MTc5OTg5NTYtNjk5Yjk5MDItNzhlNS00YmQ3LTlmOGUtYjEzM2FlM2ZkMGFjLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTExMjQlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUxMTI0VDA4MTg0MVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTVmZjQ1OThlM2RjNjc4ZDkwOWU2MmMzMGFlODIzMTNiM2I3M2MzMGQ5YWE0MWNjMDcyODQzNzlhMWM4MDE3YWEmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.dkFfLXnp1ZyfAEBQN_EK1nxPeShnzn8-2gErsjbwonE)
- **📋 Skin Browser** - Browse Cached Skin files with or without file extensions
- **🖼️ Advanced Viewer** - Browse 10,000+ images with tree navigation, sorting, and jump controls
  ![Image Viewer Interface](https://private-user-images.githubusercontent.com/62304958/517999138-8b25862f-681d-4b2b-b636-1fb8de8f570e.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjM5NzI2MjEsIm5iZiI6MTc2Mzk3MjMyMSwicGF0aCI6Ii82MjMwNDk1OC81MTc5OTkxMzgtOGIyNTg2MmYtNjgxZC00YjJiLWI2MzYtMWZiOGRlOGY1NzBlLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTExMjQlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUxMTI0VDA4MTg0MVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTM4MzlmN2ViNThlMWE2MmNmNDIwYTUxNmM3ODdmZDdiOGFjZTc0MWJmNGY2ZTE3NTA5NmE3OWQ3Y2ZjZmNhZjYmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.Xv5sgiWvckbjjOhk-5nR3AIf-w32ySTwWgymivZMU9s)
- **⚡ Real-time Progress** - Live updates with ETA and cancellation support
- **🎯 Prism Launcher Integration** - Auto-detects skin cache location

## 📥 Installation

### Windows Executable (Recommended)
1. Download `Skin-Lookup-Tool-[version].exe` from [Releases](https://github.com/p-hannemann/skin-lookup/releases)
2. Run the executable - no installation needed!

> **Note:** Windows SmartScreen may warn about unsigned software. Click "More info" → "Run anyway". The app is open source and safe.

### Run from Source
```bash
git clone https://github.com/p-hannemann/skin-lookup.git
cd skin-lookup
pip install pillow numpy imagehash

# Optional: For AI Perceptual algorithm (most powerful)
pip install torch torchvision

python gui_main.py
```

## 🚀 Quick Start

### Skin Matcher
1. **Choose input method:**
   - **Local File** - Browse for an image file on your computer
   - **Direct URL** - Paste a direct link to a skin image (e.g., from minecraftskins.com)
   - **Hypixel Wiki** - Enter a Hypixel Wiki page URL to automatically extract the skin image
2. Provide input image (file path, URL, or wiki link)
3. Browse to Prism Launcher skin cache (auto-suggested)
4. **Select matching algorithm** (see Algorithms section below)
5. Set number of matches (1-20)
6. Click "Find Matching Skins"
7. View results in built-in viewer

**Example URLs:**
- Direct: `https://www.minecraftskins.com/uploads/preview-skins/2022/03/22/minos-inquisitor-20083594.png`
- Wiki: `https://wiki.hypixel.net/Minos_Inquisitor`

**Matching Algorithms:**
- 🎯 **Balanced (Default)** - Best general-purpose algorithm using dominant colors (60%), color histogram (35%), and perceptual hashing (5%)
- 🎨 **Skin-Optimized** - Specifically designed for Minecraft skins, detects 64x64/64x32 textures and analyzes texture patterns
- 🤖 **AI Perceptual (Neural Network)** ⭐ **MOST POWERFUL** - Uses ResNet18 deep learning model to understand visual similarity like humans do. Requires PyTorch.
- 🔬 **Deep Features** - Uses edge detection and structural similarity (SSIM), focuses on shapes and patterns
- 🌈 **Color Distribution** - Emphasizes overall color presence over exact placement, best for different poses/angles
- ⚡ **Fast Match** - Quick color-based matching for large datasets (10,000+ files)

**Cache Locations:**
- Windows: `%APPDATA%\PrismLauncher\assets\skins`
- Linux: `~/.local/share/PrismLauncher/assets/skins`
- macOS: `~/Library/Application Support/PrismLauncher/assets/skins`

### Image Viewer Features
- **Folder Tree** - Navigate hierarchical directory structure
- **Sorting** - By path, creation date, or modification date
- **Jump Controls** - Jump to specific image or subfolder position
- **Dual Counter** - Overall position (72/35545) + folder position (2/70)
- **Keyboard Navigation** - Arrow keys for quick browsing
- **Windows Integration** - Explorer, Paint, and default viewer buttons



## 🔧 Technical Details

**Matching Algorithms:**
The tool offers six different algorithms optimized for various scenarios:
- **Balanced** - General-purpose: dominant colors (60%), histogram (35%), hashing (5%)
- **Skin-Optimized** - Minecraft-specific: texture patterns (40%), colors (35%), dimension matching (15%), histogram (10%)
- **AI Perceptual** - Neural network: ResNet18 features (70%), colors (20%), histogram (10%) - **Most accurate**
- **Deep Features** - Structure-focused: edge detection (50%), SSIM (30%), colors (20%)
- **Color Distribution** - Color-emphasis: histogram (70%), dominant colors (30%)
- **Fast Match** - Speed-optimized: histogram (80%), hashing (20%)

**PyTorch Installation (for AI Perceptual):**
```bash
# CPU version (smaller, works everywhere)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# GPU version (faster, requires NVIDIA GPU)
pip install torch torchvision
```
- Perceptual Hash (5%) - Structural similarity

**Requirements:** Python 3.11+, Pillow, NumPy, ImageHash

**Project Structure:**
```
config/    - Shared styling and configuration
ui/        - Interface components and windows
utils/     - Business logic and utilities
```

## 📝 Contributing

Contributions welcome! Report bugs, suggest features, or submit PRs.

## 👤 Credits

**Made by SoulReturns** | Discord: `soulreturns`

## 📄 License

MIT License - See [LICENSE](LICENSE) for details
