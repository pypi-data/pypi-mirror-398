"""
Dataset Discovery and Preprocessing Utilities

Handles automatic dataset discovery, format detection, and preprocessing
for Kaggle and other cloud environments.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


def discover_datasets(input_dir: Path) -> List[Dict[str, Any]]:
    """
    Discover and identify datasets in a directory
    
    Supports:
    - COCO flat format (annotations.json in root)
    - COCO standard format (annotations/ subdirectory)
    - YOLO format (dataset.yaml)
    - Nested datasets in subdirectories
    
    Args:
        input_dir: Directory to search for datasets
        
    Returns:
        List of dataset info dictionaries with keys:
        - path: Path to dataset
        - name: Dataset name
        - format: Dataset format ('coco', 'coco_standard', or 'yolo')
    """
    datasets_found = []
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return datasets_found
    
    logger.info(f"📂 Scanning {input_dir} for datasets...")
    input_dirs = list(input_dir.iterdir())
    logger.info(f"📋 Found {len(input_dirs)} items in {input_dir.name}")
    
    for item in input_dirs:
        logger.info(f"   • {item.name} ({'dir' if item.is_dir() else 'file'})")
    
    for potential_dataset in input_dirs:
        if not potential_dataset.is_dir():
            continue
            
        logger.info(f"🔍 Checking directory: {potential_dataset.name}")
        
        # Check if it's a COCO dataset (flat structure: annotations.json in root)
        if (potential_dataset / "annotations.json").exists():
            logger.info(f"   ✅ Has annotations.json → COCO flat format")
            datasets_found.append({
                "path": potential_dataset,
                "name": potential_dataset.name,
                "format": "coco"
            })
            continue
        
        # Check if it's a standard COCO dataset (annotations in subdirectory)
        if (potential_dataset / "annotations").exists():
            is_dir = (potential_dataset / "annotations").is_dir()
            logger.info(f"   📁 Has 'annotations' ({'directory' if is_dir else 'file'})")
            
            if is_dir:
                anno_contents = list((potential_dataset / "annotations").iterdir())[:5]
                logger.info(f"   📋 annotations/ contains: {[f.name for f in anno_contents]}")
                logger.info(f"   ✅ COCO standard format detected")
                datasets_found.append({
                    "path": potential_dataset,
                    "name": potential_dataset.name,
                    "format": "coco_standard"
                })
                continue
            else:
                logger.info(f"   ⚠️  'annotations' is a file, not a directory - skipping")
        
        # Check if it's a YOLO dataset
        if (potential_dataset / "dataset.yaml").exists():
            logger.info(f"   ✅ Has dataset.yaml → YOLO format")
            datasets_found.append({
                "path": potential_dataset,
                "name": potential_dataset.name,
                "format": "yolo"
            })
            continue
        
        # Check if dataset is nested in a subdirectory (common for Kaggle public datasets)
        logger.info(f"   🔍 Not in root, checking subdirectories...")
        try:
            subdirs = [d for d in potential_dataset.iterdir() if d.is_dir()]
            found_in_subdir = False
            
            for subdir in subdirs:
                # Check if subdirectory has COCO flat format
                if (subdir / "annotations.json").exists():
                    logger.info(f"   ✅ Found COCO dataset in subdirectory: {subdir.name}/")
                    datasets_found.append({
                        "path": subdir,
                        "name": f"{potential_dataset.name}/{subdir.name}",
                        "format": "coco"
                    })
                    found_in_subdir = True
                    break
                    
                # Check if subdirectory has COCO standard format
                elif (subdir / "annotations").exists() and (subdir / "annotations").is_dir():
                    logger.info(f"   ✅ Found COCO standard format in subdirectory: {subdir.name}/")
                    anno_contents = list((subdir / "annotations").iterdir())[:5]
                    logger.info(f"      annotations/ contains: {[f.name for f in anno_contents]}")
                    datasets_found.append({
                        "path": subdir,
                        "name": f"{potential_dataset.name}/{subdir.name}",
                        "format": "coco_standard"
                    })
                    found_in_subdir = True
                    break
            
            if not found_in_subdir:
                contents = list(potential_dataset.iterdir())[:10]
                content_info = [f"{c.name}/" if c.is_dir() else c.name for c in contents]
                logger.info(f"   ⚠️  Not a recognized format")
                logger.info(f"   📂 Contains: {', '.join(content_info)}")
                
        except Exception as e:
            logger.error(f"   ❌ Could not read directory contents: {e}")
    
    logger.info(f"📊 Discovered {len(datasets_found)} dataset(s)")
    for ds in datasets_found:
        logger.info(f"   • {ds['name']} ({ds['format']})")
    
    return datasets_found


def preprocess_coco_standard(coco_dir: Path, output_dir: Path) -> Path:
    """
    Convert COCO standard format to flat format for easier processing
    
    COCO standard format:
    - train2017/, val2017/, test2017/ directories with images
    - annotations/ directory with instances_train2017.json, instances_val2017.json, etc.
    
    Flat format:
    - images/ directory with all images (symlinked, not copied)
    - annotations.json with merged annotations
    
    Args:
        coco_dir: Path to COCO standard format dataset
        output_dir: Path to output directory for flat format
        
    Returns:
        Path to the flat format directory
    """
    logger.info(f"Converting standard COCO format: {coco_dir.name}")
    
    flat_dir = output_dir / f"flat_{coco_dir.name}"
    flat_dir.mkdir(parents=True, exist_ok=True)
    
    # Create flat structure with all images in one directory
    images_out = flat_dir / "images"
    images_out.mkdir(exist_ok=True)
    
    # Copy/link images from train2017, val2017, test2017, or directly from images/
    image_count = 0
    
    # First, check if images are in standard COCO subdirectories (train2017, val2017, etc.)
    found_in_subdirs = False
    for subdir in ["train2017", "val2017", "test2017"]:
        img_subdir = coco_dir / subdir
        if img_subdir.exists():
            found_in_subdirs = True
            for img_file in img_subdir.glob("*.*"):
                # Create symlink instead of copying to save space
                try:
                    (images_out / img_file.name).symlink_to(img_file)
                    image_count += 1
                except FileExistsError:
                    pass  # Already linked
    
    # If no subdirectories found, check if images are directly in images/ directory
    # (common for HuggingFace datasets or custom COCO datasets)
    if not found_in_subdirs:
        img_dir = coco_dir / "images"
        if img_dir.exists() and img_dir.is_dir():
            for img_file in img_dir.glob("*.*"):
                # Create symlink instead of copying to save space
                try:
                    (images_out / img_file.name).symlink_to(img_file)
                    image_count += 1
                except FileExistsError:
                    pass  # Already linked
    
    logger.info(f"  Linked {image_count} images")
    
    # Merge annotation files into single annotations.json
    annotations_dir = coco_dir / "annotations"
    merged_annotations = {
        "images": [],
        "annotations": [],
        "categories": []
    }
    
    # Process each annotation file (instances_train2017.json, instances_val2017.json)
    # Priority: instances > person_keypoints > captions
    annotation_files = (
        list(annotations_dir.glob("instances_*.json")) or
        list(annotations_dir.glob("person_keypoints_*.json")) or
        list(annotations_dir.glob("*_*.json"))
    )
    
    if annotation_files:
        logger.info(f"  Found {len(annotation_files)} annotation file(s) to merge")
        
        # Import normalization function
        from .converters import AdvancedCOCOtoYOLOMerger
        
        # Use the first annotation file as base
        logger.info(f"  Processing: {annotation_files[0].name}")
        with open(annotation_files[0], 'r') as f:
            base_anno = json.load(f)
            # Normalize category names (convert "class_X" to proper COCO names)
            normalized_categories = []
            for cat in base_anno.get("categories", []):
                cat_id = cat.get('id', 0)
                cat_name = cat.get('name', '')
                if cat_name:
                    cat_name = AdvancedCOCOtoYOLOMerger._normalize_category_name(cat_name, cat_id)
                normalized_cat = cat.copy()
                normalized_cat['name'] = cat_name
                normalized_categories.append(normalized_cat)
            merged_annotations["categories"] = normalized_categories
            merged_annotations["images"].extend(base_anno.get("images", []))
            merged_annotations["annotations"].extend(base_anno.get("annotations", []))
        
        # Merge remaining annotation files
        for anno_file in annotation_files[1:]:
            logger.info(f"  Processing: {anno_file.name}")
            with open(anno_file, 'r') as f:
                anno_data = json.load(f)
                merged_annotations["images"].extend(anno_data.get("images", []))
                merged_annotations["annotations"].extend(anno_data.get("annotations", []))
        
        # Save merged annotations
        with open(flat_dir / "annotations.json", 'w') as f:
            json.dump(merged_annotations, f)
        
        logger.info(
            f"  ✅ Merged {len(merged_annotations['images'])} images, "
            f"{len(merged_annotations['annotations'])} annotations, "
            f"{len(merged_annotations['categories'])} categories"
        )
    else:
        logger.warning(f"  ⚠️ No annotation files found in {annotations_dir}")
    
    return flat_dir


def preprocess_datasets(datasets: List[Dict[str, Any]], working_dir: Path) -> List[Tuple[str, str]]:
    """
    Preprocess datasets to convert to consistent formats
    
    Converts COCO standard format to flat format.
    Other formats are passed through unchanged.
    
    Args:
        datasets: List of dataset info dicts from discover_datasets()
        working_dir: Working directory for temporary files
        
    Returns:
        List of tuples (dataset_path, format) ready for merging
    """
    logger.info("🔧 Preprocessing datasets...")
    preprocessed = []
    
    for ds_info in datasets:
        if ds_info["format"] == "coco_standard":
            flat_dir = preprocess_coco_standard(ds_info["path"], working_dir)
            preprocessed.append((str(flat_dir), "coco"))
        else:
            # Keep original format
            preprocessed.append((str(ds_info["path"]), ds_info["format"]))
    
    return preprocessed

