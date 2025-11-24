"""Hypixel Wiki Parser Utility

This module handles parsing Hypixel wiki pages to extract mob sprite images.
"""

import urllib.request
import re
from urllib.parse import urljoin
from PIL import Image
import io


def parse_wiki_for_image(wiki_url, debug_callback=None):
    """
    Parse Hypixel wiki page to find the sprite head icon image.
    
    Args:
        wiki_url: URL of the Hypixel wiki page
        debug_callback: Optional function to call with debug messages
    
    Returns:
        PIL Image object or None if parsing fails
    
    Raises:
        Exception: If image cannot be found or downloaded
    """
    def debug_log(msg):
        if debug_callback:
            debug_callback(msg)
    
    try:
        debug_log(f"Parsing Hypixel Wiki: {wiki_url}")
        
        # Extract page name from URL (e.g., "Minos_Hunter" from https://wiki.hypixel.net/Minos_Hunter)
        page_name = wiki_url.rstrip('/').split('/')[-1].lower()
        debug_log(f"Page name extracted: {page_name}")
        
        # Download the wiki page with User-Agent header
        req = urllib.request.Request(
            wiki_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            debug_log(f"Downloaded HTML page ({len(html)} chars)")
        
        # Find both absolute and relative PNG URLs
        # Pattern 1: Absolute URLs
        absolute_pngs = re.findall(r'https://[^\s"<>]+\.png', html)
        # Pattern 2: Relative URLs in src attributes
        relative_pngs = re.findall(r'src="(/[^"]+\.png)"', html)
        # Pattern 3: Relative URLs in href attributes
        relative_href_pngs = re.findall(r'href="(/[^"]+\.png)"', html)
        
        # Convert relative URLs to absolute
        base_url = 'https://wiki.hypixel.net'
        png_matches = absolute_pngs + [urljoin(base_url, url) for url in relative_pngs + relative_href_pngs]
        
        debug_log(f"Found {len(png_matches)} PNG URLs in HTML (absolute: {len(absolute_pngs)}, relative: {len(relative_pngs + relative_href_pngs)})")
        
        if not png_matches:
            raise Exception("Could not find any skin images on the wiki page")
        
        # Filter out common non-mob images (logos, icons, UI elements)
        exclude_keywords = ['logo', 'icon_', 'wiki', 'button', 'background', 'banner']
        filtered_matches = [img for img in png_matches if not any(keyword in img.lower() for keyword in exclude_keywords)]
        debug_log(f"After filtering UI elements: {len(filtered_matches)} PNG URLs")
        
        # If filtering removed all images, keep the original list
        if not filtered_matches:
            debug_log("Warning: Filtering removed all images, using unfiltered list")
            filtered_matches = png_matches
        
        # PRIORITY 1: Look for sprite images that contain the page name
        # (e.g., SkyBlock_sprite_entities_minos_hunter.png for page Minos_Hunter)
        sprite_images = [img for img in filtered_matches if 'sprite' in img.lower()]
        debug_log(f"Found {len(sprite_images)} sprite images")
        
        # Find sprite with matching page name
        matching_sprites = [img for img in sprite_images if page_name in img.lower()]
        debug_log(f"Found {len(matching_sprites)} sprites matching page name '{page_name}'")
        
        if matching_sprites:
            image_url = matching_sprites[0]
            debug_log(f"Selected matching sprite image URL: {image_url}")
        else:
            # FALLBACK: No sprite matching page name, use render/skin image
            debug_log(f"No sprite found matching '{page_name}', falling back to render/skin images")
            # Look for images with page name OR common mob image keywords
            skin_images = [img for img in filtered_matches if (page_name in img.lower() or any(keyword in img.lower() for keyword in ['skyblock_npcs', 'skyblock_entities', 'skin', 'render', 'full', 'body']))]
            debug_log(f"Filtered to {len(skin_images)} likely skin/render images")
            
            # If no specific skin images found, use the first image from filtered list
            if not skin_images:
                debug_log("No specific skin/render images found, using first filtered PNG")
                skin_images = filtered_matches
            
            if skin_images:
                image_url = skin_images[0]
                debug_log(f"Selected fallback image URL: {image_url}")
            else:
                raise Exception("No suitable images found after filtering")
        
        # Download the image
        debug_log(f"Downloading image from URL: {image_url}")
        req = urllib.request.Request(
            image_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            image_data = response.read()
        
        # Load image
        img = Image.open(io.BytesIO(image_data))
        debug_log(f"Successfully loaded image: {img.size} {img.mode}")
        
        return img
        
    except Exception as e:
        debug_log(f"Error parsing wiki page: {str(e)}")
        raise


def download_image_from_url(url, debug_callback=None):
    """
    Download an image from a direct URL.
    
    Args:
        url: Direct URL to the image
        debug_callback: Optional function to call with debug messages
    
    Returns:
        PIL Image object or None if download fails
    
    Raises:
        Exception: If image cannot be downloaded
    """
    def debug_log(msg):
        if debug_callback:
            debug_callback(msg)
    
    try:
        debug_log(f"Downloading image from URL: {url}")
        
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            image_data = response.read()
        
        img = Image.open(io.BytesIO(image_data))
        debug_log(f"Successfully downloaded image: {img.size} {img.mode}")
        
        return img
        
    except Exception as e:
        debug_log(f"Error downloading image: {str(e)}")
        raise
