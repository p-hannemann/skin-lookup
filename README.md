# Skin Lookup Tool

Find and match Minecraft skins in Prism Launcher's cache using AI-powered image comparison. Identify the original skin texture from a 3D rendered character image.

## ✨ Features

- **🔍 Smart Matching** - 9 matching algorithms including AI-powered options (ResNet18/50, color analysis, perceptual hashing)
  ![Skin Matcher Interface](https://private-user-images.githubusercontent.com/62304958/518159805-0b0695af-035c-4f53-b084-2a393de18c14.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjM5OTU2NTEsIm5iZiI6MTc2Mzk5NTM1MSwicGF0aCI6Ii82MjMwNDk1OC81MTgxNTk4MDUtMGIwNjk1YWYtMDM1Yy00ZjUzLWIwODQtMmEzOTNkZTE4YzE0LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTExMjQlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUxMTI0VDE0NDIzMVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWE2MzE4ODg2MzZiNTM1YjFiMDlmZGY1OWMwODY4NzYwOGYwY2NkYTc0YzlkMjI5MTIzNTUyNDkxMjViOThkZDEmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.0qnoOnL8AdhVlMoaazcAl-mY-PJsVAU9FMWbaskXdvk)

- **🌐 Multiple Input Methods** - Local files, direct URLs, or Hypixel Wiki pages (auto-extracts sprite images)
- **📂 Batch Processing** - Copy and rename entire directories with .png extension
  ![File Copier Interface](https://private-user-images.githubusercontent.com/62304958/518160716-bb064408-d623-4996-8452-260c098fb36f.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjM5OTYwMTIsIm5iZiI6MTc2Mzk5NTcxMiwicGF0aCI6Ii82MjMwNDk1OC81MTgxNjA3MTYtYmIwNjQ0MDgtZDYyMy00OTk2LTg0NTItMjYwYzA5OGZiMzZmLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTExMjQlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUxMTI0VDE0NDgzMlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTVkY2VmNTUwOTEyM2RmZmRiM2JkYzQ2ZDA4ZTVlMTE3NjM2YmZhMGQ0YzA0NTE0OWQzYWVmZDVhZTMxOGY4OTYmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.G_HJnv0DsuNrfryXn602_G52fZytYG7E0S4NYynE2tI)
- **📋 Skin Browser** - Browse Cached Skin files with or without file extensions
  ![Skin Browser Interface](https://private-user-images.githubusercontent.com/62304958/518163959-3dce5e9f-a786-42f2-ac41-11655af95d06.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjM5OTYwMTIsIm5iZiI6MTc2Mzk5NTcxMiwicGF0aCI6Ii82MjMwNDk1OC81MTgxNjM5NTktM2RjZTVlOWYtYTc4Ni00MmYyLWFjNDEtMTE2NTVhZjk1ZDA2LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTExMjQlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUxMTI0VDE0NDgzMlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTA2NTc5ZGRkZjcyNTE1ZWFhOGM5NjMwYjAyNTdiOWI5MGFhMDgwY2I3Mjc5ZTk2ZTE4ZjVmM2JhMTBkMTVjMGMmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.bnbxgQyZ9G7RPuQONqj5vuFBz-U9xvXC-UwrGRizFj0)
- **🖼️ Advanced Viewer** - Browse 10,000+ images with tree navigation, sorting, and jump controls
  ![Image Viewer Interface](https://private-user-images.githubusercontent.com/62304958/517999138-8b25862f-681d-4b2b-b636-1fb8de8f570e.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjM5NzI2MjEsIm5iZiI6MTc2Mzk3MjMyMSwicGF0aCI6Ii82MjMwNDk1OC81MTc5OTkxMzgtOGIyNTg2MmYtNjgxZC00YjJiLWI2MzYtMWZiOGRlOGY1NzBlLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTExMjQlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUxMTI0VDA4MTg0MVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTM4MzlmN2ViNThlMWE2MmNmNDIwYTUxNmM3ODdmZDdiOGFjZTc0MWJmNGY2ZTE3NTA5NmE3OWQ3Y2ZjZmNhZjYmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.Xv5sgiWvckbjjOhk-5nR3AIf-w32ySTwWgymivZMU9s)
- **🖼️ 3D Render Converter** - Convert 3D character renders to 2D Minecraft skins
  ![Render Converter Interface](https://private-user-images.githubusercontent.com/62304958/518161023-a351d434-3a67-4aed-8025-c24fc2d1aca0.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjM5OTU2NTEsIm5iZiI6MTc2Mzk5NTM1MSwicGF0aCI6Ii82MjMwNDk1OC81MTgxNjEwMjMtYTM1MWQ0MzQtM2E2Ny00YWVkLTgwMjUtYzI0ZmMyZDFhY2EwLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTExMjQlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUxMTI0VDE0NDIzMVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTVlMWIzOGVkNDBmMDQ4ZDdlMWM1MDhhYjRmNTFiYzFjODNkNTE2ZGZiYjM4ODdjOTkzMjM4ODA0NmQyMGIzMTQmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.Wj79WMFx-UVYMWDiVO7THTNQiFwYL8iJsnF-DrsyVOA)
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
   - **Direct URL** - Paste a direct link to a skin image
   - **Hypixel Wiki** - Enter a Hypixel Wiki page URL to automatically extract sprite/mob images
2. **Preview input** - Click the Preview button to verify the correct image is loaded
3. Browse to Prism Launcher skin cache (auto-suggested)
4. **Select matching algorithm** (see Algorithms section below)
5. Set number of matches (1-20)
6. Click "Find Matching Skins"
7. View results in built-in viewer

**Example URLs:**
- Direct: `https://www.minecraftskins.com/uploads/preview-skins/2022/03/22/minos-inquisitor-20083594.png`
- Wiki: `https://wiki.hypixel.net/Minos_Hunter` (auto-extracts sprite: `SkyBlock_sprite_entities_minos_hunter.png`)

**Matching Algorithms:**
- **Balanced (Default)** - Best general-purpose algorithm using dominant colors (60%), color histogram (35%), and perceptual hashing (5%)
- **Render to Skin (Convert+Match)** - Converts 3D renders to 2D skins first, then matches using balanced algorithm
- **Render Match (3D→2D)** - Fast algorithm optimized for matching 3D renders to 2D skins
- **Skin-Optimized** - Specifically designed for Minecraft skins, detects 64x64/64x32 textures and analyzes texture patterns
- **AI Perceptual (ResNet18)** ⭐ **MOST POWERFUL** - Uses deep learning to understand visual similarity like humans. Requires PyTorch.
- **AI Mobile (ResNet50)** - Stronger AI model with more parameters. Slower but more accurate. Requires PyTorch.
- **Deep Features** - Uses edge detection and structural similarity (SSIM), focuses on shapes and patterns
- **Color Distribution** - Emphasizes overall color presence over exact placement, best for different poses/angles
- **Fast Match** - Quick color-based matching for large datasets (10,000+ files)

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
The tool offers 9 different algorithms optimized for various scenarios:
- **Balanced** - General-purpose: dominant colors (60%), histogram (35%), hashing (5%)
- **Render to Skin** - Converts 3D renders using pixel extraction, then applies balanced matching
- **Render Match** - Optimized 3D→2D: visible regions (50%), colors (30%), histogram (20%)
- **Skin-Optimized** - Minecraft-specific: texture patterns (40%), colors (35%), dimension matching (15%), histogram (10%)
- **AI Perceptual (ResNet18)** - Neural network: ResNet18 features (70%), colors (20%), histogram (10%) - **Most accurate for general use**
- **AI Mobile (ResNet50)** - Stronger network: ResNet50 features (70%), colors (20%), histogram (10%) - **Most accurate overall**
- **Deep Features** - Structure-focused: edge detection (50%), SSIM (30%), colors (20%)
- **Color Distribution** - Color-emphasis: histogram (70%), dominant colors (30%)
- **Fast Match** - Speed-optimized: histogram (80%), hashing (20%)

**3D Render Converter Tab:**
- Extracts visible pixels from 3D character renders
- Reconstructs 2D skin texture (64×64)
- Supports front-facing and angled renders
- Preview before saving

**Hypixel Wiki Integration:**
- Automatically extracts mob sprite images (e.g., `SkyBlock_sprite_entities_*.png`)
- Falls back to 3D renders if no sprite found
- Filters out UI elements (logos, buttons, icons)
- Works with any Hypixel Wiki mob/NPC page

**PyTorch Installation (for AI algorithms):**
```bash
# CPU version (smaller, works everywhere)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# GPU version (faster, requires NVIDIA GPU with CUDA)
pip install torch torchvision
```

**Requirements:** Python 3.11+, Pillow, NumPy, ImageHash
**Optional:** PyTorch (for AI algorithms), scikit-image (for Deep Features)

**Project Structure:**
```
algorithms/       - Modular matching algorithm implementations
  base.py         - Abstract base class for all algorithms
  balanced.py     - Default balanced algorithm
  render_match.py - Fast 3D→2D matching
  render_to_skin.py - Convert+match algorithm
config/           - Shared styling and configuration
ui/               - Interface components and windows
  tabs/           - Modular tab implementations (converter, browser)
utils/            - Business logic and utilities
  wiki_parser.py  - Hypixel Wiki parsing and image extraction
  feature_extractors.py - Shared feature extraction functions
```

## 📝 Contributing

Contributions welcome! Report bugs, suggest features, or submit PRs.

## 👤 Credits

**Made by SoulReturns** | Discord: `soulreturns`

## 📄 License

MIT License - See [LICENSE](LICENSE) for details
