"""
Feature extraction functions for image matching.
Shared by all matching algorithms.
"""

import numpy as np
from PIL import Image, ImageFilter
import imagehash

# Optional imports
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from skimage.metrics import structural_similarity as ssim
    SSIM_AVAILABLE = True
except ImportError:
    SSIM_AVAILABLE = False

try:
    import torch
    import torchvision.models as models
    import torchvision.transforms as transforms
    TORCH_AVAILABLE = True
    print(f"[INFO] PyTorch {torch.__version__} loaded successfully (CUDA: {torch.cuda.is_available()})")
    
    # Initialize models globally to avoid reloading
    _ai_model = None
    _ai_transform = None
    _mobile_model = None
    _mobile_transform = None
    
    def _get_ai_model():
        global _ai_model, _ai_transform
        if _ai_model is None:
            _ai_model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
            _ai_model.eval()
            _ai_model = torch.nn.Sequential(*list(_ai_model.children())[:-1])
            
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            _ai_model = _ai_model.to(device)
            print(f"[INFO] ResNet18 model loaded on device: {device}")
            
            _ai_transform = transforms.Compose([
                transforms.Resize((256, 256), interpolation=transforms.InterpolationMode.NEAREST),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
            ])
        return _ai_model, _ai_transform
    
    def _get_mobile_model():
        global _mobile_model, _mobile_transform
        if _mobile_model is None:
            _mobile_model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
            _mobile_model.eval()
            _mobile_model = torch.nn.Sequential(*list(_mobile_model.children())[:-1])
            
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            _mobile_model = _mobile_model.to(device)
            if device.type == 'cuda':
                _mobile_model = _mobile_model.half()
            print(f"[INFO] ResNet50 model loaded on device: {device} (FP16: {device.type == 'cuda'})")
            
            _mobile_transform = transforms.Compose([
                transforms.Resize((288, 288), interpolation=transforms.InterpolationMode.BILINEAR),
                transforms.CenterCrop(256),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        return _mobile_model, _mobile_transform
    
except ImportError as e:
    TORCH_AVAILABLE = False
    print(f"[WARNING] PyTorch import failed: {e}")


def extract_dominant_colors_fast(img_array, n_colors=12):
    """Fast extraction of dominant colors using numpy."""
    pixels_quantized = (img_array // 16) * 16
    pixels_flat = pixels_quantized.reshape(-1, 3)
    
    pixel_codes = (pixels_flat[:, 0] << 16) | (pixels_flat[:, 1] << 8) | pixels_flat[:, 2]
    unique_codes, counts = np.unique(pixel_codes, return_counts=True)
    
    top_indices = np.argsort(counts)[-n_colors:][::-1]
    top_codes = unique_codes[top_indices]
    top_counts = counts[top_indices]
    
    colors = np.zeros((len(top_codes), 3), dtype=np.uint8)
    colors[:, 0] = (top_codes >> 16) & 0xFF
    colors[:, 1] = (top_codes >> 8) & 0xFF
    colors[:, 2] = top_codes & 0xFF
    
    weights = top_counts / top_counts.sum()
    return colors, weights


def extract_render_features(img_array):
    """Extract features optimized for 3D render to 2D skin matching."""
    colors, weights = extract_dominant_colors_fast(img_array, n_colors=24)
    
    h, w = img_array.shape[:2]
    grid_size = 4
    cell_h, cell_w = h // grid_size, w // grid_size
    
    spatial_features = []
    for i in range(grid_size):
        for j in range(grid_size):
            cell = img_array[i*cell_h:(i+1)*cell_h, j*cell_w:(j+1)*cell_w]
            avg_color = np.mean(cell.reshape(-1, 3), axis=0)
            spatial_features.extend(avg_color)
    
    return {
        'colors': colors,
        'weights': weights,
        'spatial': np.array(spatial_features)
    }


def is_minecraft_skin_texture(img):
    """Detect if image is a Minecraft skin texture."""
    width, height = img.size
    if (width == 64 and height == 64) or (width == 64 and height == 32):
        return True
    return False


def extract_texture_pattern(img_array):
    """Extract texture pattern features."""
    edges = cv2.Canny(img_array, 50, 150) if CV2_AVAILABLE else np.zeros_like(img_array[:,:,0])
    edge_density = np.count_nonzero(edges) / edges.size
    
    gray = np.mean(img_array, axis=2).astype(np.uint8)
    contrast = np.std(gray)
    
    return {
        'edge_density': edge_density,
        'contrast': contrast
    }


def extract_edge_features(img):
    """Extract edge-based features from image."""
    if not CV2_AVAILABLE:
        return np.zeros((64, 64)), 0.0
    
    img_resized = img.resize((64, 64), Image.Resampling.LANCZOS)
    img_array = np.array(img_resized.convert('RGB'))
    
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.count_nonzero(edges) / edges.size
    
    return edges, edge_density


def extract_ai_features(img):
    """Extract features using ResNet18 neural network."""
    if not TORCH_AVAILABLE:
        return None
    
    try:
        model, transform = _get_ai_model()
        device = next(model.parameters()).device
        
        img_rgb = img.convert('RGB')
        img_tensor = transform(img_rgb).unsqueeze(0).to(device)
        
        with torch.no_grad():
            features = model(img_tensor)
        
        features = features.squeeze().cpu().numpy()
        return features
    except Exception as e:
        print(f"[ERROR] AI feature extraction failed: {e}")
        return None


def extract_mobile_features(img):
    """Extract features using ResNet50 with optimizations."""
    if not TORCH_AVAILABLE:
        return None
    
    try:
        model, transform = _get_mobile_model()
        device = next(model.parameters()).device
        
        img_rgb = img.convert('RGB')
        img_tensor = transform(img_rgb).unsqueeze(0).to(device)
        
        if device.type == 'cuda':
            img_tensor = img_tensor.half()
        
        with torch.no_grad():
            features = model(img_tensor)
        
        features = features.squeeze().cpu().float().numpy()
        return features
    except Exception as e:
        print(f"[ERROR] Mobile feature extraction failed: {e}")
        return None


def convert_render_to_skin(render_img):
    """Convert a 3D render to a 2D skin using pixel extraction."""
    if isinstance(render_img, np.ndarray):
        render_array = render_img
    else:
        render_array = np.array(render_img.convert('RGBA'))
    
    h, w = render_array.shape[:2]
    skin_array = np.zeros((64, 64, 4), dtype=np.uint8)
    
    def extract_and_resize(source_region, target_shape):
        y1, y2, x1, x2 = source_region
        y1, y2 = max(0, y1), min(h, y2)
        x1, x2 = max(0, x1), min(w, x2)
        region = render_array[y1:y2, x1:x2]
        if region.size == 0 or y2 <= y1 or x2 <= x1:
            return np.zeros(target_shape + (4,), dtype=np.uint8)
        extracted = Image.fromarray(region).resize((target_shape[1], target_shape[0]), Image.Resampling.LANCZOS)
        return np.array(extracted)
    
    def get_average_color(region_array):
        if region_array.size == 0:
            return np.array([0, 0, 0, 255], dtype=np.uint8)
        mask = region_array[:, :, 3] > 128
        if not mask.any():
            return np.array([0, 0, 0, 255], dtype=np.uint8)
        avg = np.mean(region_array[mask], axis=0).astype(np.uint8)
        avg[3] = 255
        return avg
    
    # Region detection
    head_top, head_bottom = int(h * 0.05), int(h * 0.35)
    head_left, head_right = int(w * 0.35), int(w * 0.65)
    body_top, body_bottom = int(h * 0.35), int(h * 0.70)
    body_left, body_right = int(w * 0.35), int(w * 0.65)
    leg_top, leg_bottom = int(h * 0.70), int(h * 0.95)
    leg_left, leg_right = int(w * 0.35), int(w * 0.65)
    
    # HEAD
    front_head = extract_and_resize((head_top + int((head_bottom-head_top)*0.4), head_bottom - int((head_bottom-head_top)*0.2),
                                    head_left + int((head_right-head_left)*0.3), head_right - int((head_right-head_left)*0.3)), (8, 8))
    skin_array[8:16, 8:16] = front_head
    
    left_head = extract_and_resize((head_top + int((head_bottom-head_top)*0.4), head_bottom - int((head_bottom-head_top)*0.2),
                                   head_left, head_left + int((head_right-head_left)*0.3)), (8, 8))
    skin_array[8:16, 16:24] = left_head
    
    top_head = extract_and_resize((head_top, head_top + int((head_bottom-head_top)*0.3),
                                  head_left + int((head_right-head_left)*0.3), head_right - int((head_right-head_left)*0.3)), (8, 8))
    skin_array[0:8, 8:16] = top_head
    
    skin_array[8:16, 0:8] = np.fliplr(left_head)
    avg_head = get_average_color(front_head)
    skin_array[8:16, 24:32] = avg_head
    skin_array[16:24, 8:16] = (avg_head * 0.8).astype(np.uint8)
    
    # BODY
    front_body = extract_and_resize((body_top + int((body_bottom-body_top)*0.1), body_bottom,
                                    body_left + int((body_right-body_left)*0.25), body_right - int((body_right-body_left)*0.25)), (12, 8))
    skin_array[20:32, 20:28] = front_body
    
    left_body = extract_and_resize((body_top + int((body_bottom-body_top)*0.1), body_bottom,
                                   body_left, body_left + int((body_right-body_left)*0.25)), (12, 4))
    skin_array[20:32, 16:20] = left_body
    skin_array[20:32, 28:32] = np.fliplr(left_body)
    
    avg_body = get_average_color(front_body)
    skin_array[20:32, 32:40] = avg_body
    
    # ARMS
    right_arm = extract_and_resize((body_top + int((body_bottom-body_top)*0.1), body_bottom,
                                   body_left - int((body_right-body_left)*0.15), body_left), (12, 4))
    skin_array[20:32, 44:48] = right_arm
    skin_array[20:32, 36:40] = right_arm
    
    # LEGS
    right_leg = extract_and_resize((leg_top, leg_bottom,
                                   leg_left + int((leg_right-leg_left)*0.2), leg_left + int((leg_right-leg_left)*0.4)), (12, 4))
    skin_array[20:32, 4:8] = right_leg
    
    left_leg = extract_and_resize((leg_top, leg_bottom,
                                  leg_left + int((leg_right-leg_left)*0.6), leg_left + int((leg_right-leg_left)*0.8)), (12, 4))
    skin_array[20:32, 20:24] = left_leg
    
    return Image.fromarray(skin_array, 'RGBA')


def extract_visible_skin_regions(skin_array):
    """Extract only the visible regions (front, top, left) from a skin for comparison."""
    visible_pixels = []
    
    # Head front, left, top
    visible_pixels.append(skin_array[8:16, 8:16])
    visible_pixels.append(skin_array[8:16, 16:24])
    visible_pixels.append(skin_array[0:8, 8:16])
    
    # Body front, left
    visible_pixels.append(skin_array[20:32, 20:28])
    visible_pixels.append(skin_array[20:32, 28:32])
    
    # Arms front
    visible_pixels.append(skin_array[20:32, 44:48])
    visible_pixels.append(skin_array[20:32, 36:40])
    
    # Legs front
    visible_pixels.append(skin_array[20:32, 4:8])
    visible_pixels.append(skin_array[20:32, 20:24])
    
    return np.concatenate([region.flatten() for region in visible_pixels])


def color_palette_distance_fast(colors1, weights1, colors2, weights2):
    """Calculate distance between two color palettes."""
    total_distance = 0
    for i, (c1, w1) in enumerate(zip(colors1, weights1)):
        min_dist = float('inf')
        for c2 in colors2:
            dist = np.linalg.norm(c1.astype(float) - c2.astype(float))
            min_dist = min(min_dist, dist)
        total_distance += w1 * min_dist
    return total_distance / (255.0 * np.sqrt(3))


def calculate_ssim_distance(img1, img2):
    """Calculate SSIM distance between two images."""
    if not SSIM_AVAILABLE:
        return 1.0
    
    try:
        img1_resized = img1.resize((64, 64), Image.Resampling.LANCZOS)
        img2_resized = img2.resize((64, 64), Image.Resampling.LANCZOS)
        
        img1_gray = np.array(img1_resized.convert('L'))
        img2_gray = np.array(img2_resized.convert('L'))
        
        similarity = ssim(img1_gray, img2_gray)
        return 1.0 - similarity
    except:
        return 1.0


def calculate_ai_similarity(features1, features2):
    """Calculate cosine similarity between AI feature vectors."""
    norm1 = np.linalg.norm(features1)
    norm2 = np.linalg.norm(features2)
    
    if norm1 == 0 or norm2 == 0:
        return 1.0
    
    cosine_sim = np.dot(features1, features2) / (norm1 * norm2)
    distance = (1.0 - cosine_sim) / 2.0
    return max(0.0, min(1.0, distance))
