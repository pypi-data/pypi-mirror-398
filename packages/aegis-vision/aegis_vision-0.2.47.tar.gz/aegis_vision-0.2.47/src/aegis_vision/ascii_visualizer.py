"""
ASCII Art Visualization for Dataset Verification

Utility functions to display dataset images with bounding boxes in ASCII art format.
Used during training agent dataset processing to verify bounding box handling correctness.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def image_to_ascii(image: Image.Image, width: int = 80, height: int = 40) -> List[str]:
    """
    Convert PIL Image to ASCII art
    
    Args:
        image: PIL Image object
        width: Target width in characters
        height: Target height in characters
        
    Returns:
        List of strings, each representing a line of ASCII art
    """
    img = image.convert('RGB')
    img_resized = img.resize((width, height), Image.Resampling.LANCZOS)
    
    # ASCII characters from darkest to lightest
    ascii_chars = " .:-=+*#%@"
    
    ascii_lines = []
    for y in range(height):
        line = ""
        for x in range(width):
            r, g, b = img_resized.getpixel((x, y))
            # Convert RGB to grayscale
            gray = int(0.299 * r + 0.587 * g + 0.114 * b)
            # Map to ASCII character
            ascii_index = int((gray / 255.0) * (len(ascii_chars) - 1))
            line += ascii_chars[ascii_index]
        ascii_lines.append(line)
    
    return ascii_lines


def detect_bbox_format(bbox: List[float], img_width: int, img_height: int) -> tuple:
    """
    Auto-detect bbox format and convert to [left_x, top_y, right_x, bottom_y]
    
    Args:
        bbox: Bounding box in either format
        img_width: Image width
        img_height: Image height
        
    Returns:
        Tuple (left_x, top_y, right_x, bottom_y)
    """
    if len(bbox) == 4:
        # Check if it's [left_x, top_y, right_x, bottom_y] format
        if bbox[2] > bbox[0] and bbox[3] > bbox[1] and bbox[2] <= img_width and bbox[3] <= img_height:
            # Already in [left_x, top_y, right_x, bottom_y] format
            return tuple(bbox)
        else:
            # [x, y, width, height] format
            left_x, top_y, width, height = bbox
            return (left_x, top_y, left_x + width, top_y + height)
    return tuple(bbox[:4])


def draw_bbox_on_ascii(
    ascii_lines: List[str], 
    bbox: List[float], 
    label: str, 
    img_width: int, 
    img_height: int, 
    ascii_width: int, 
    ascii_height: int
) -> List[str]:
    """
    Draw bounding box on ASCII art
    
    Args:
        ascii_lines: List of ASCII art lines
        bbox: Bounding box in format [left_x, top_y, right_x, bottom_y] or [x, y, width, height]
        label: Label text to display
        img_width: Original image width
        img_height: Original image height
        ascii_width: ASCII art width
        ascii_height: ASCII art height
        
    Returns:
        Modified ASCII lines with bounding box drawn
    """
    # Detect and convert bbox format
    left_x, top_y, right_x, bottom_y = detect_bbox_format(bbox, img_width, img_height)
    
    # Scale coordinates to ASCII dimensions
    scale_x = ascii_width / img_width
    scale_y = ascii_height / img_height
    
    ascii_left = int(left_x * scale_x)
    ascii_top = int(top_y * scale_y)
    ascii_right = int(right_x * scale_x)
    ascii_bottom = int(bottom_y * scale_y)
    
    # Clamp to ASCII boundaries
    ascii_left = max(0, min(ascii_left, ascii_width - 1))
    ascii_top = max(0, min(ascii_top, ascii_height - 1))
    ascii_right = max(0, min(ascii_right, ascii_width - 1))
    ascii_bottom = max(0, min(ascii_bottom, ascii_height - 1))
    
    # Create a copy of ASCII lines
    result = [list(line) for line in ascii_lines]
    
    # Draw bounding box
    # Top and bottom edges
    for x in range(ascii_left, ascii_right + 1):
        if 0 <= ascii_top < ascii_height and 0 <= x < ascii_width:
            result[ascii_top][x] = '-'
        if 0 <= ascii_bottom < ascii_height and 0 <= x < ascii_width:
            result[ascii_bottom][x] = '-'
    
    # Left and right edges
    for y in range(ascii_top, ascii_bottom + 1):
        if 0 <= y < ascii_height and 0 <= ascii_left < ascii_width:
            result[y][ascii_left] = '|'
        if 0 <= y < ascii_height and 0 <= ascii_right < ascii_width:
            result[y][ascii_right] = '|'
    
    # Corners
    if 0 <= ascii_top < ascii_height and 0 <= ascii_left < ascii_width:
        result[ascii_top][ascii_left] = '+'
    if 0 <= ascii_top < ascii_height and 0 <= ascii_right < ascii_width:
        result[ascii_top][ascii_right] = '+'
    if 0 <= ascii_bottom < ascii_height and 0 <= ascii_left < ascii_width:
        result[ascii_bottom][ascii_left] = '+'
    if 0 <= ascii_bottom < ascii_height and 0 <= ascii_right < ascii_width:
        result[ascii_bottom][ascii_right] = '+'
    
    # Draw label at top-left corner (inside the box)
    if label:
        label_y = ascii_top
        if label_y < ascii_height:
            label_text = label[:min(len(label), ascii_right - ascii_left - 2)]  # Truncate if too long
            for i, char in enumerate(label_text):
                label_x = ascii_left + 1 + i
                if 0 <= label_x < ascii_width and label_x < ascii_right:
                    result[label_y][label_x] = char
    
    # Convert back to strings
    return [''.join(line) for line in result]


def display_ascii_image(ascii_lines: List[str], title: str = ""):
    """
    Display ASCII art on console
    
    Args:
        ascii_lines: List of ASCII art lines
        title: Optional title to display
    """
    if title:
        print(f"\n{'='*80}")
        print(f"{title:^80}")
        print(f"{'='*80}")
    
    for line in ascii_lines:
        print(line)
    
    print()


def visualize_coco_dataset_ascii(
    annotation_file: Path, 
    images_dir: Path, 
    num_images: int = 2, 
    dataset_name: str = "",
    ascii_width: int = 80, 
    ascii_height: int = 40,
    log_to_logger: bool = False
) -> bool:
    """
    Visualize COCO dataset images with bounding boxes in ASCII art
    
    Args:
        annotation_file: Path to COCO annotation JSON file
        images_dir: Path to images directory
        num_images: Number of images to visualize per dataset (default: 2)
        dataset_name: Name of the dataset
        ascii_width: ASCII art width in characters
        ascii_height: ASCII art height in characters
        log_to_logger: If True, also log to logger in addition to print
        
    Returns:
        True if visualization succeeded, False otherwise
    """
    if not annotation_file.exists():
        msg = f"❌ Annotation file not found: {annotation_file}"
        if log_to_logger:
            logger.warning(msg)
        print(msg)
        return False
    
    if not images_dir.exists():
        msg = f"❌ Images directory not found: {images_dir}"
        if log_to_logger:
            logger.warning(msg)
        print(msg)
        return False
    
    try:
        # Load COCO annotations
        with open(annotation_file, 'r') as f:
            coco_data = json.load(f)
        
        images = coco_data.get('images', [])
        annotations = coco_data.get('annotations', [])
        
        # Normalize category names (convert "class_X" to proper COCO names)
        from .converters import AdvancedCOCOtoYOLOMerger
        categories = {}
        for cat in coco_data.get('categories', []):
            cat_id = cat.get('id', 0)
            cat_name = cat.get('name', '')
            if cat_name:
                cat_name = AdvancedCOCOtoYOLOMerger._normalize_category_name(cat_name, cat_id)
            categories[cat_id] = cat_name
        
        # Group annotations by image_id
        annotations_by_image = {}
        for ann in annotations:
            img_id = ann['image_id']
            if img_id not in annotations_by_image:
                annotations_by_image[img_id] = []
            annotations_by_image[img_id].append(ann)
        
        # Filter images that have annotations
        images_with_annotations = [img for img in images if img['id'] in annotations_by_image]
        
        if not images_with_annotations:
            msg = f"❌ No images with annotations found in dataset"
            if log_to_logger:
                logger.warning(msg)
            print(msg)
            return False
        
        # Select images to visualize
        selected_images = random.sample(images_with_annotations, min(num_images, len(images_with_annotations)))
        
        print(f"\n{'='*80}")
        print(f"📦 Dataset: {dataset_name or annotation_file.parent.name}")
        print(f"📊 Total images: {len(images)}, Images with annotations: {len(images_with_annotations)}")
        print(f"📋 Categories: {len(categories)} ({', '.join(list(categories.values())[:5])}{'...' if len(categories) > 5 else ''})")
        print(f"{'='*80}")
        
        if log_to_logger:
            logger.info(f"Visualizing {len(selected_images)} images from dataset: {dataset_name}")
        
        for img_idx, image_data in enumerate(selected_images, 1):
            image_id = image_data['id']
            image_filename = image_data['file_name']
            image_width = image_data['width']
            image_height = image_data['height']
            
            image_path = images_dir / image_filename
            if not image_path.exists():
                msg = f"⚠️  Image not found: {image_path}"
                if log_to_logger:
                    logger.debug(msg)
                print(msg)
                continue
            
            # Load image
            try:
                img = Image.open(image_path)
            except Exception as e:
                msg = f"⚠️  Failed to load image {image_filename}: {e}"
                if log_to_logger:
                    logger.debug(msg)
                print(msg)
                continue
            
            # Convert to ASCII
            ascii_lines = image_to_ascii(img, width=ascii_width, height=ascii_height)
            
            # Get annotations for this image
            image_anns = annotations_by_image.get(image_id, [])
            
            # Draw all bounding boxes
            for ann in image_anns:
                if 'bbox' in ann:
                    bbox = ann['bbox']
                    category_id = ann['category_id']
                    category_name = categories.get(category_id, f"class_{category_id}")
                    
                    ascii_lines = draw_bbox_on_ascii(
                        ascii_lines, bbox, category_name,
                        img_width=image_width, img_height=image_height,
                        ascii_width=ascii_width, ascii_height=ascii_height
                    )
            
            # Display
            title = f"Image {img_idx}/{num_images}: {image_filename} ({image_width}x{image_height})"
            title += f" | {len(image_anns)} annotation(s)"
            display_ascii_image(ascii_lines, title)
        
        return True
        
    except Exception as e:
        msg = f"❌ Error visualizing dataset: {e}"
        if log_to_logger:
            logger.error(msg, exc_info=True)
        print(msg)
        return False

