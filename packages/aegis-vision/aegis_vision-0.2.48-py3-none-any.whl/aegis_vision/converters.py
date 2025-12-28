"""
Dataset converters for Aegis Vision
"""

import json
import random
import shutil
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class COCOConverter:
    """
    Convert COCO format annotations to YOLO format
    """
    
    def __init__(
        self,
        annotations_file: str,
        images_dir: str,
        output_dir: str,
        train_split: float = 0.8,
        dataset_name: Optional[str] = None
    ):
        """
        Initialize COCO to YOLO converter
        
        Args:
            annotations_file: Path to COCO JSON file
            images_dir: Path to images directory
            output_dir: Path to output directory
            train_split: Fraction of data for training (default: 0.8)
            dataset_name: Optional dataset name to determine bbox format. 
                         If 'detection-datasets-coco' or contains 'detection/coco detection-datasets-coco',
                         uses [left_x, top_y, right_x, bottom_y] format.
                         Otherwise defaults to standard COCO [x, y, width, height] format.
        """
        self.annotations_file = Path(annotations_file)
        self.images_dir = Path(images_dir)
        self.output_dir = Path(output_dir)
        self.train_split = train_split
        self.dataset_name = dataset_name or ""
        
        # Determine bbox format based on dataset name
        # If it's detection-datasets-coco, use [left_x, top_y, right_x, bottom_y]
        # Otherwise, default to standard COCO format [x, y, width, height]
        self.use_xyxy_format = self._should_use_xyxy_format()
        
        # Validate inputs
        if not self.annotations_file.exists():
            raise FileNotFoundError(f"Annotations file not found: {annotations_file}")
        if not self.images_dir.exists():
            raise FileNotFoundError(f"Images directory not found: {images_dir}")
    
    def _should_use_xyxy_format(self) -> bool:
        """
        Determine if dataset should use [left_x, top_y, right_x, bottom_y] format.
        
        Returns:
            True if dataset is detection-datasets-coco, False otherwise (defaults to standard COCO format)
        """
        if not self.dataset_name:
            return False
        
        name_lower = self.dataset_name.lower()
        # Check for detection-datasets-coco or detection/coco detection-datasets-coco
        return 'detection-datasets-coco' in name_lower or \
               ('detection' in name_lower and 'coco' in name_lower and 'detection-datasets-coco' in name_lower)
    
    def convert(self) -> Dict[str, Any]:
        """
        Convert COCO annotations to YOLO format
        
        Returns:
            Statistics dictionary
        """
        # Load COCO data
        with open(self.annotations_file, 'r') as f:
            coco_data = json.load(f)
        
        # Extract categories
        categories = {cat['id']: cat['name'] for cat in coco_data.get('categories', [])}
        labels = list(categories.values())
        label_to_id = {label: idx for idx, label in enumerate(labels)}
        
        # Create temporary output directory
        temp_output = self.output_dir / "temp"
        temp_labels_dir = temp_output / "labels"
        temp_images_dir = temp_output / "images"
        temp_labels_dir.mkdir(parents=True, exist_ok=True)
        temp_images_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert annotations
        images_processed = 0
        annotations_converted = 0
        
        for image_data in coco_data.get('images', []):
            image_id = image_data['id']
            image_filename = image_data['file_name']
            image_width = image_data['width']
            image_height = image_data['height']
            
            # Get annotations for this image
            image_annotations = [
                ann for ann in coco_data.get('annotations', [])
                if ann['image_id'] == image_id
            ]
            
            if not image_annotations:
                continue
            
            # Convert to YOLO format
            yolo_annotations = []
            for ann in image_annotations:
                category_id = ann['category_id']
                category_name = categories.get(category_id)
                
                if not category_name or category_name not in label_to_id:
                    continue
                
                # Convert bbox to YOLO format (normalized)
                bbox = ann['bbox']
                
                if self.use_xyxy_format:
                    # Format: [left_x, top_y, right_x, bottom_y]
                    left_x, top_y, right_x, bottom_y = bbox
                    width = right_x - left_x
                    height = bottom_y - top_y
                else:
                    # Standard COCO format: [x, y, width, height]
                    left_x, top_y, width, height = bbox
                    right_x = left_x + width
                    bottom_y = top_y + height
                
                # Convert to YOLO format (normalized center coordinates)
                x_center = (left_x + width / 2) / image_width
                y_center = (top_y + height / 2) / image_height
                width_norm = width / image_width
                height_norm = height / image_height
                
                class_id = label_to_id[category_name]
                
                yolo_annotations.append(
                    f"{class_id} {x_center:.6f} {y_center:.6f} {width_norm:.6f} {height_norm:.6f}"
                )
                annotations_converted += 1
            
            if yolo_annotations:
                # Copy image
                src_image = self.images_dir / image_filename
                dst_image = temp_images_dir / image_filename
                if src_image.exists():
                    shutil.copy2(src_image, dst_image)
                    
                    # Write YOLO annotation file
                    label_filename = Path(image_filename).stem + '.txt'
                    label_path = temp_labels_dir / label_filename
                    with open(label_path, 'w') as f:
                        f.write('\n'.join(yolo_annotations))
                    
                    images_processed += 1
        
        # Split dataset into train/val
        image_files = list(temp_images_dir.glob("*.jpg")) + \
                     list(temp_images_dir.glob("*.png")) + \
                     list(temp_images_dir.glob("*.jpeg"))
        
        random.shuffle(image_files)
        split_idx = int(len(image_files) * self.train_split)
        train_images = image_files[:split_idx]
        val_images = image_files[split_idx:]
        
        # Create final directory structure
        train_images_dir = self.output_dir / "images" / "train"
        val_images_dir = self.output_dir / "images" / "val"
        train_labels_dir = self.output_dir / "labels" / "train"
        val_labels_dir = self.output_dir / "labels" / "val"
        
        for directory in [train_images_dir, val_images_dir, train_labels_dir, val_labels_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Move files to train/val splits
        for img in train_images:
            shutil.move(str(img), str(train_images_dir / img.name))
            label_file = temp_labels_dir / (img.stem + '.txt')
            if label_file.exists():
                shutil.move(str(label_file), str(train_labels_dir / label_file.name))
        
        for img in val_images:
            shutil.move(str(img), str(val_images_dir / img.name))
            label_file = temp_labels_dir / (img.stem + '.txt')
            if label_file.exists():
                shutil.move(str(label_file), str(val_labels_dir / label_file.name))
        
        # Clean up temp directory
        shutil.rmtree(temp_output)
        
        # Create dataset.yaml
        self._create_dataset_yaml(labels)
        
        return {
            "images_processed": images_processed,
            "annotations_converted": annotations_converted,
            "train_count": len(train_images),
            "val_count": len(val_images),
            "num_classes": len(labels),
            "labels": labels,
        }
    
    def _create_dataset_yaml(self, labels: List[str]) -> Path:
        """
        Create dataset.yaml file for YOLO training
        
        Args:
            labels: List of class labels
            
        Returns:
            Path to created dataset.yaml
        """
        yaml_content = f"""# Aegis Vision Dataset Configuration
path: {self.output_dir.absolute()}
train: images/train
val: images/val

# Classes
nc: {len(labels)}
names: {labels}
"""
        
        yaml_path = self.output_dir / "dataset.yaml"
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)
        
        return yaml_path


class DatasetMerger:
    """
    Merge multiple datasets (COCO or YOLO format) into a single unified dataset
    """
    
    def __init__(self, output_dir: str, train_split: float = 0.8):
        """
        Initialize dataset merger
        
        Args:
            output_dir: Path to output directory for merged dataset
            train_split: Fraction of data for training (default: 0.8)
        """
        self.output_dir = Path(output_dir)
        self.train_split = train_split
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def merge(self, dataset_paths: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        Merge multiple datasets into one
        
        Args:
            dataset_paths: List of tuples (dataset_path, format) where format is 'coco' or 'yolo'
            
        Returns:
            Statistics dictionary with merge results
        """
        all_images = []
        all_labels_data = []  # Store (image_path, label_path, dataset_name, dataset_labels)
        unified_label_set = set()
        
        # Temporary directory for converted datasets
        temp_dir = self.output_dir / "temp_converted"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each dataset
        for idx, (dataset_path, dataset_format) in enumerate(dataset_paths):
            ds_path = Path(dataset_path)
            ds_name = ds_path.name
            
            print(f"📁 Processing {ds_name} ({dataset_format} format)...")
            
            if dataset_format.lower() == "coco":
                # Convert COCO to YOLO format first
                converted_dir = temp_dir / f"converted_{idx}_{ds_name}"
                converter = COCOConverter(
                    annotations_file=str(ds_path / "annotations.json"),
                    images_dir=str(ds_path / "images"),
                    output_dir=str(converted_dir),
                    train_split=1.0,  # Don't split yet
                    dataset_name=ds_name
                )
                stats = converter.convert()
                print(f"  ✅ Converted: {stats['images_processed']} images")
                
                # Get labels
                ds_labels = stats['labels']
                unified_label_set.update(ds_labels)
                
                # Collect images and labels
                img_dir = converted_dir / "images" / "train"
                lbl_dir = converted_dir / "labels" / "train"
                
                for img_file in img_dir.glob("*.*"):
                    lbl_file = lbl_dir / (img_file.stem + ".txt")
                    if lbl_file.exists():
                        all_images.append(img_file)
                        all_labels_data.append((img_file, lbl_file, ds_name, ds_labels))
            
            elif dataset_format.lower() == "yolo":
                # Load YOLO dataset configuration
                yolo_yaml_path = ds_path / "dataset.yaml"
                if not yolo_yaml_path.exists():
                    print(f"  ⚠️  Warning: dataset.yaml not found in {ds_path}")
                    continue
                
                with open(yolo_yaml_path, 'r') as f:
                    ds_config = yaml.safe_load(f)
                    ds_labels = ds_config.get('names', [])
                    unified_label_set.update(ds_labels)
                
                # Collect images and labels from train/val
                for split in ['train', 'val']:
                    img_dir = ds_path / "images" / split
                    lbl_dir = ds_path / "labels" / split
                    
                    if img_dir.exists() and lbl_dir.exists():
                        for img_file in img_dir.glob("*.*"):
                            lbl_file = lbl_dir / (img_file.stem + ".txt")
                            if lbl_file.exists():
                                all_images.append(img_file)
                                all_labels_data.append((img_file, lbl_file, ds_name, ds_labels))
        
        print(f"📊 Found {len(all_images)} images from {len(dataset_paths)} datasets")
        
        # Create unified label list (sorted for consistency)
        unified_labels = sorted(list(unified_label_set))
        unified_label_map = {label: idx for idx, label in enumerate(unified_labels)}
        
        print(f"🏷️  Unified labels ({len(unified_labels)}): {unified_labels}")
        
        # Copy images and remap labels
        print("📋 Copying images and remapping labels...")
        temp_merged_images = self.output_dir / "temp_merged_images"
        temp_merged_labels = self.output_dir / "temp_merged_labels"
        temp_merged_images.mkdir(parents=True, exist_ok=True)
        temp_merged_labels.mkdir(parents=True, exist_ok=True)
        
        for img_file, lbl_file, ds_name, ds_labels in all_labels_data:
            # Create unique filename with dataset prefix
            new_img_name = f"{ds_name}_{img_file.name}"
            new_lbl_name = f"{ds_name}_{img_file.stem}.txt"
            
            # Copy image
            shutil.copy2(img_file, temp_merged_images / new_img_name)
            
            # Remap and copy labels
            with open(lbl_file, 'r') as f:
                lines = f.readlines()
            
            remapped_lines = []
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 5:
                    old_class_id = int(parts[0])
                    # Get the label name from old dataset
                    if old_class_id < len(ds_labels):
                        old_label = ds_labels[old_class_id]
                        # Map to new unified class ID
                        new_class_id = unified_label_map.get(old_label)
                        if new_class_id is not None:
                            parts[0] = str(new_class_id)
                            remapped_lines.append(' '.join(parts))
            
            with open(temp_merged_labels / new_lbl_name, 'w') as f:
                f.write('\n'.join(remapped_lines))
        
        print(f"✅ Copied and remapped {len(all_labels_data)} images")
        
        # Split into train/val
        print("🔀 Splitting merged dataset into train/val...")
        all_merged_images = list(temp_merged_images.glob("*.*"))
        random.shuffle(all_merged_images)
        
        split_idx = int(len(all_merged_images) * self.train_split)
        train_images = all_merged_images[:split_idx]
        val_images = all_merged_images[split_idx:]
        
        # Create train/val directories
        train_img_dir = self.output_dir / "images" / "train"
        val_img_dir = self.output_dir / "images" / "val"
        train_lbl_dir = self.output_dir / "labels" / "train"
        val_lbl_dir = self.output_dir / "labels" / "val"
        
        for directory in [train_img_dir, val_img_dir, train_lbl_dir, val_lbl_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Move files to train/val
        for img in train_images:
            lbl = temp_merged_labels / (img.stem + ".txt")
            shutil.move(str(img), str(train_img_dir / img.name))
            if lbl.exists():
                shutil.move(str(lbl), str(train_lbl_dir / lbl.name))
        
        for img in val_images:
            lbl = temp_merged_labels / (img.stem + ".txt")
            shutil.move(str(img), str(val_img_dir / img.name))
            if lbl.exists():
                shutil.move(str(lbl), str(val_lbl_dir / lbl.name))
        
        print(f"✅ Split complete: {len(train_images)} train, {len(val_images)} val")
        
        # Clean up temporary directories
        shutil.rmtree(temp_dir, ignore_errors=True)
        shutil.rmtree(temp_merged_images, ignore_errors=True)
        shutil.rmtree(temp_merged_labels, ignore_errors=True)
        
        # Create dataset.yaml for merged dataset
        self._create_dataset_yaml(unified_labels)
        
        print(f"✅ Created merged dataset.yaml")
        
        return {
            "total_images": len(all_merged_images),
            "train_count": len(train_images),
            "val_count": len(val_images),
            "num_classes": len(unified_labels),
            "labels": unified_labels,
            "datasets_merged": len(dataset_paths)
        }
    
    def _create_dataset_yaml(self, labels: List[str]) -> Path:
        """
        Create dataset.yaml file for YOLO training
        
        Args:
            labels: List of class labels
            
        Returns:
            Path to created dataset.yaml
        """
        yaml_content = f"""# Merged Aegis Vision Dataset
path: {self.output_dir.absolute()}
train: images/train
val: images/val

# Classes
nc: {len(labels)}
names: {labels}
"""
        
        yaml_path = self.output_dir / "dataset.yaml"
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)
        
        return yaml_path


class AdvancedCOCOtoYOLOMerger:
    """
    Advanced COCO to YOLO converter with multi-dataset merging support
    
    Features:
    - Handles multiple COCO datasets with different class mappings
    - Creates unified class mapping across all datasets
    - Uses symlinks instead of copying images (efficient)
    - Proper class ID remapping for consistent training
    """
    
    # Standard COCO category names (80 classes)
    # These correspond to category IDs 1-80 in COCO (ID 0 is not used)
    COCO_CATEGORY_NAMES = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
        'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
        'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
        'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
        'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
        'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
        'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake',
        'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
        'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
        'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
    ]
    
    @staticmethod
    def _normalize_category_name(cat_name: str, cat_id: int) -> str:
        """
        Normalize category name from various formats to proper COCO category name.
        
        Handles:
        - "class_X" format -> maps to COCO category name
        - Numeric IDs -> maps to COCO category name
        - Already proper names -> returns as-is
        
        Args:
            cat_name: Category name from dataset
            cat_id: Category ID from dataset
            
        Returns:
            Normalized COCO category name
        """
        # If it's already a proper name (not class_X), return as-is
        if not cat_name.startswith('class_'):
            return cat_name
        
        # Try to extract numeric ID from "class_X" format
        try:
            # Extract number from "class_45" -> 45
            class_num = int(cat_name.replace('class_', ''))
            # Map to COCO category name (COCO IDs are 1-80, but HuggingFace uses 0-79)
            if 0 <= class_num < len(AdvancedCOCOtoYOLOMerger.COCO_CATEGORY_NAMES):
                return AdvancedCOCOtoYOLOMerger.COCO_CATEGORY_NAMES[class_num]
        except (ValueError, IndexError):
            pass
        
        # Try using category ID directly (COCO IDs are 1-80)
        if 1 <= cat_id <= 80:
            # COCO IDs are 1-indexed, array is 0-indexed
            return AdvancedCOCOtoYOLOMerger.COCO_CATEGORY_NAMES[cat_id - 1]
        
        # Fallback: return original name
        return cat_name
    
    def __init__(self, output_dir: Path):
        """
        Initialize converter
        
        Args:
            output_dir: Output directory for merged YOLO dataset
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def convert_bbox_to_yolo(
        img_width: int, 
        img_height: int, 
        bbox: List[float],
        use_xyxy_format: bool = False
    ) -> Tuple[float, float, float, float]:
        """
        Convert COCO bbox to YOLO format [x_center, y_center, w, h] (normalized)
        
        Args:
            img_width: Image width
            img_height: Image height
            bbox: Bounding box in COCO format
            use_xyxy_format: If True, bbox is [left_x, top_y, right_x, bottom_y].
                           If False (default), bbox is standard COCO [x, y, width, height]
        
        Returns:
            Tuple of (x_center, y_center, w_norm, h_norm) in normalized YOLO format
        """
        if use_xyxy_format:
            # Format: [left_x, top_y, right_x, bottom_y]
            left_x, top_y, right_x, bottom_y = bbox
            width = right_x - left_x
            height = bottom_y - top_y
        else:
            # Standard COCO format: [x, y, width, height]
            left_x, top_y, width, height = bbox
            right_x = left_x + width
            bottom_y = top_y + height
        
        # Convert to YOLO format (normalized center coordinates)
        x_center = (left_x + width / 2) / img_width
        y_center = (top_y + height / 2) / img_height
        w_norm = width / img_width
        h_norm = height / img_height
        
        return x_center, y_center, w_norm, h_norm
    
    def process_coco_annotations(
        self,
        anno_path: Path,
        images_source_dir: Path,
        output_labels_dir: Path,
        output_images_dir: Path,
        class_id_map: Dict[int, int],
        dataset_name: Optional[str] = None,
        label_strategy: str = 'merge_all'
    ) -> Tuple[int, int]:
        """
        Process COCO annotations and create YOLO labels + image symlinks
        
        Args:
            anno_path: Path to COCO annotation JSON
            images_source_dir: Source directory for images
            output_labels_dir: Output directory for YOLO label files
            output_images_dir: Output directory for image symlinks
            class_id_map: Dict mapping COCO category_id -> sequential YOLO class_id
            dataset_name: Optional dataset name to determine bbox format
            
        Returns:
            Tuple of (image_count, label_count)
        """
        # Determine bbox format based on dataset name
        use_xyxy_format = self._should_use_xyxy_format(dataset_name)
        if not anno_path or not anno_path.exists():
            return 0, 0
        
        try:
            from pycocotools.coco import COCO
        except ImportError:
            raise ImportError("pycocotools is required. Install with: pip install pycocotools")
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"   Processing {anno_path.name}...")
        
        coco = COCO(str(anno_path))
        
        img_count = 0
        label_count = 0
        
        for img_id in coco.getImgIds():
            img_info = coco.loadImgs([img_id])[0]
            img_filename = img_info['file_name']
            img_source_path = images_source_dir / img_filename
            
            if not img_source_path.exists():
                continue
            
            # Get annotations first to check if image will have valid labels after filtering
            img_width, img_height = img_info['width'], img_info['height']
            annotations = coco.loadAnns(coco.getAnnIds(imgIds=[img_id]))
            
            # Filter annotations and count valid ones
            filtered_count = 0
            valid_annotations = []
            
            for ann in annotations:
                if 'bbox' in ann:
                    coco_cat_id = ann['category_id']
                    
                    # Map COCO category_id to sequential YOLO class_id
                    if coco_cat_id not in class_id_map:
                        filtered_count += 1
                        continue  # Skip unknown classes (filtered by label strategy)
                    
                    yolo_class_id = class_id_map[coco_cat_id]
                    bbox = self.convert_bbox_to_yolo(img_width, img_height, ann['bbox'], use_xyxy_format=use_xyxy_format)
                    label_str = f"{yolo_class_id} {' '.join(f'{v:.6f}' for v in bbox)}\n"
                    valid_annotations.append(label_str)
            
            # For base_dataset strategy: if image has no valid annotations after filtering, exclude it
            if label_strategy == 'base_dataset' and len(valid_annotations) == 0:
                if filtered_count > 0:
                    logger.debug(f"   ⏭️  Excluding image {img_filename} (no valid labels after filtering)")
                continue  # Skip this image entirely
            
            # Symlink image (no copying!)
            img_dest_path = output_images_dir / img_filename
            try:
                if not img_dest_path.exists():
                    img_dest_path.symlink_to(img_source_path)
                img_count += 1
            except Exception as e:
                logger.warning(f"   ⚠️ Could not link {img_filename}: {e}")
                continue
            
            # Create YOLO label file
            label_file = output_labels_dir / f"{img_filename.rsplit('.', 1)[0]}.txt"
            with open(label_file, 'w') as f:
                seen_labels = set()
                for label_str in valid_annotations:
                    if label_str not in seen_labels:
                        f.write(label_str)
                        seen_labels.add(label_str)
                        label_count += 1
            
            if filtered_count > 0 and label_strategy == 'base_dataset':
                logger.debug(f"   ⏭️  Filtered {filtered_count} annotations (labels not in base dataset)")
        
        return img_count, label_count
    
    @staticmethod
    def _should_use_xyxy_format(dataset_name: Optional[str]) -> bool:
        """
        Determine if dataset should use [left_x, top_y, right_x, bottom_y] format.
        
        Args:
            dataset_name: Dataset name to check
            
        Returns:
            True if dataset is detection-datasets-coco, False otherwise (defaults to standard COCO format)
        """
        if not dataset_name:
            return False
        
        name_lower = dataset_name.lower()
        # Check for detection-datasets-coco or detection/coco detection-datasets-coco
        return 'detection-datasets-coco' in name_lower or \
               ('detection' in name_lower and 'coco' in name_lower and 'detection-datasets-coco' in name_lower)
    
    def merge_and_convert(
        self,
        preprocessed_datasets: List[Tuple[str, str]],
        enable_ascii_visualization: bool = False,
        label_strategy: str = 'merge_all',
        base_dataset_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Merge multiple COCO datasets and convert to YOLO format
        
        Args:
            preprocessed_datasets: List of (dataset_path, format) tuples
            enable_ascii_visualization: If True, display 2 sample images per dataset with bounding boxes in ASCII art
            label_strategy: 'merge_all' (default) or 'base_dataset'
            base_dataset_index: Index of dataset to use as label source (for base_dataset strategy, 0-based)
            
        Returns:
            Dictionary with merge results containing dataset_yaml path and statistics
        """
        try:
            from pycocotools.coco import COCO
        except ImportError:
            raise ImportError("pycocotools is required. Install with: pip install pycocotools")
        
        import logging
        logger = logging.getLogger(__name__)
        
        # Create output directories
        output_labels_train = self.output_dir / "labels" / "train"
        output_labels_val = self.output_dir / "labels" / "val"
        output_images_train = self.output_dir / "images" / "train"
        output_images_val = self.output_dir / "images" / "val"
        
        for d in [output_labels_train, output_labels_val, output_images_train, output_images_val]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Build unified class mapping
        if label_strategy == 'base_dataset' and base_dataset_index is not None:
            logger.info(f"📋 Building class mapping from base dataset (index {base_dataset_index})...")
        else:
            logger.info("📋 Building unified class mapping...")
        
        all_categories = {}
        duplicate_categories = []  # Track duplicates for reporting
        base_dataset_labels = set()  # For base_dataset strategy
        
        # If base_dataset strategy, first collect labels from base dataset only
        if label_strategy == 'base_dataset' and base_dataset_index is not None:
            if base_dataset_index < 0 or base_dataset_index >= len(preprocessed_datasets):
                raise ValueError(f"base_dataset_index {base_dataset_index} is out of range (0-{len(preprocessed_datasets)-1})")
            
            ds_path, ds_format = preprocessed_datasets[base_dataset_index]
            ds_path = Path(ds_path)
            
            if ds_format in ["coco", "coco_standard"]:
                if ds_format == "coco_standard":
                    anno_dir = ds_path / "annotations"
                    anno_files = list(anno_dir.glob("instances_*.json"))
                    if not anno_files:
                        anno_files = list(anno_dir.glob("*.json"))
                else:
                    anno_files = [ds_path / "annotations.json"]
                
                if anno_files and anno_files[0].exists():
                    try:
                        coco = COCO(str(anno_files[0]))
                        cat_ids = coco.getCatIds()
                        categories = coco.loadCats(cat_ids) if cat_ids else []
                        
                        # Fallback: if pycocotools returns 0 categories, try reading directly from JSON
                        if len(categories) == 0:
                            logger.warning(f"   ⚠️  No categories found via pycocotools, trying direct JSON read...")
                            import json
                            with open(anno_files[0], 'r') as f:
                                anno_data = json.load(f)
                                categories_data = anno_data.get('categories', [])
                                if categories_data:
                                    logger.info(f"   ✅ Found {len(categories_data)} categories in JSON")
                                    categories = categories_data
                        
                        for cat in categories:
                            if isinstance(cat, dict):
                                cat_name = cat.get('name') or cat.get('category_name', '')
                                cat_id = cat.get('id') or cat.get('category_id', 0)
                                
                                # Normalize category name (convert "class_X" to proper COCO name)
                                if cat_name:
                                    cat_name = AdvancedCOCOtoYOLOMerger._normalize_category_name(cat_name, cat_id)
                                
                                if cat_name:
                                    cat_name_normalized = ' '.join(cat_name.lower().strip().split())
                                    all_categories[cat_name] = (cat_id, base_dataset_index)
                                    base_dataset_labels.add(cat_name_normalized)
                        
                        logger.info(f"   ✅ Base dataset ({ds_path.name}): {len(base_dataset_labels)} classes")
                    except Exception as e:
                        logger.error(f"   ❌ Error loading base dataset categories: {e}")
                        raise
                else:
                    raise ValueError(f"Base dataset annotation file not found: {ds_path}")
            else:
                raise ValueError(f"Base dataset format '{ds_format}' not supported for base_dataset strategy")
        
        # Now process all datasets
        # For base_dataset strategy, skip the base dataset in the loop since we already processed it
        for idx, (ds_path, ds_format) in enumerate(preprocessed_datasets):
            # Skip base dataset if we already processed it (for base_dataset strategy)
            if label_strategy == 'base_dataset' and base_dataset_index is not None and idx == base_dataset_index:
                logger.info(f"   ⏭️  Skipping base dataset {idx + 1} ({Path(ds_path).name}) - already processed")
                continue
            ds_path = Path(ds_path)
            
            if ds_format in ["coco", "coco_standard"]:
                if ds_format == "coco_standard":
                    anno_dir = ds_path / "annotations"
                    anno_files = list(anno_dir.glob("instances_*.json"))
                    if not anno_files:
                        anno_files = list(anno_dir.glob("*.json"))
                else:
                    anno_files = [ds_path / "annotations.json"]
                
                if anno_files and anno_files[0].exists():
                    try:
                        coco = COCO(str(anno_files[0]))
                        cat_ids = coco.getCatIds()
                        categories = coco.loadCats(cat_ids) if cat_ids else []
                        
                        # Fallback: if pycocotools returns 0 categories, try reading directly from JSON
                        if len(categories) == 0:
                            logger.warning(f"   ⚠️  No categories found via pycocotools, trying direct JSON read...")
                            import json
                            with open(anno_files[0], 'r') as f:
                                anno_data = json.load(f)
                                categories_data = anno_data.get('categories', [])
                                if categories_data:
                                    logger.info(f"   ✅ Found {len(categories_data)} categories in JSON")
                                    categories = categories_data
                        
                        categories_found_in_dataset = 0
                        categories_duplicated = 0
                        categories_seen_names = {}  # Track normalized names to detect duplicates within dataset
                        
                        for cat in categories:
                            # Handle both dict format (from JSON) and pycocotools format
                            if isinstance(cat, dict):
                                cat_name = cat.get('name') or cat.get('category_name', '')
                                cat_id = cat.get('id') or cat.get('category_id', 0)
                                
                                # Normalize category name (convert "class_X" to proper COCO name)
                                if cat_name:
                                    cat_name = AdvancedCOCOtoYOLOMerger._normalize_category_name(cat_name, cat_id)
                                
                                if cat_name:
                                    # Normalize name for case-insensitive comparison (remove extra whitespace)
                                    cat_name_normalized = ' '.join(cat_name.lower().strip().split())
                                    
                                    # First check: within this dataset, have we seen this normalized name?
                                    if cat_name_normalized in categories_seen_names:
                                        # Duplicate within same dataset - use the first occurrence's case
                                        existing_name_in_dataset = categories_seen_names[cat_name_normalized]
                                        if cat_name != existing_name_in_dataset:
                                            categories_duplicated += 1
                                            duplicate_categories.append((cat_name, existing_name_in_dataset))
                                            logger.debug(f"   🔄 Duplicate within dataset: '{cat_name}' (matches '{existing_name_in_dataset}')")
                                        continue
                                    
                                    # For base_dataset strategy, check if category is in base dataset FIRST
                                    if label_strategy == 'base_dataset' and base_dataset_index is not None:
                                        # Only process categories that are in the base dataset
                                        if cat_name_normalized not in base_dataset_labels:
                                            # Skip this category - not in base dataset
                                            logger.debug(f"   ⏭️  Skipping '{cat_name}' (not in base dataset labels)")
                                            continue
                                    
                                    # Second check: across all datasets, does this normalized name exist?
                                    existing_name = None
                                    for existing_cat_name in all_categories.keys():
                                        existing_normalized = ' '.join(existing_cat_name.lower().strip().split())
                                        if existing_normalized == cat_name_normalized:
                                            existing_name = existing_cat_name
                                            break
                                    
                                    if existing_name:
                                        # Duplicate found across datasets - use the existing name
                                        # For base_dataset strategy, this is expected (category from base dataset)
                                        categories_duplicated += 1
                                        duplicate_categories.append((cat_name, existing_name))
                                        logger.debug(f"   🔄 Duplicate across datasets: '{cat_name}' (matches existing '{existing_name}')")
                                        # Track this normalization for this dataset too
                                        categories_seen_names[cat_name_normalized] = existing_name
                                    else:
                                        # New unique class name - store with original case
                                        all_categories[cat_name] = (cat_id, idx)
                                        categories_found_in_dataset += 1
                                        categories_seen_names[cat_name_normalized] = cat_name
                        
                        if categories_duplicated > 0:
                            logger.info(f"   • Dataset {idx + 1}: {ds_path.name} - {categories_found_in_dataset} new classes, {categories_duplicated} duplicates skipped")
                        else:
                            logger.info(f"   • Dataset {idx + 1}: {ds_path.name} - {categories_found_in_dataset} classes")
                        
                        if len(categories) == 0:
                            logger.warning(f"   ⚠️  Warning: No categories found in {anno_files[0].name}")
                    except Exception as e:
                        logger.error(f"   ❌ Error loading categories from {anno_files[0].name}: {e}")
                else:
                    logger.warning(f"   ⚠️  No annotation file found for dataset {ds_path.name}")
        
        # Create sequential YOLO class IDs
        unified_class_names = {}
        for yolo_id, (cat_name, _) in enumerate(sorted(all_categories.items())):
            unified_class_names[yolo_id] = cat_name
        
        # Report duplicates summary
        if duplicate_categories:
            logger.info(f"🔄 Duplicate class names detected: {len(duplicate_categories)} duplicates merged")
            # Group duplicates by existing name for better reporting
            duplicates_by_existing = {}
            for dup_name, existing_name in duplicate_categories:
                if existing_name not in duplicates_by_existing:
                    duplicates_by_existing[existing_name] = []
                duplicates_by_existing[existing_name].append(dup_name)
            
            # Show first few duplicates
            shown = 0
            for existing_name, dup_names in list(duplicates_by_existing.items())[:5]:
                if shown < 5:
                    # Get unique duplicate names and limit to first 3
                    unique_dup_names = list(set(dup_names))[:3]
                    dup_names_str = ', '.join(unique_dup_names)
                    if len(set(dup_names)) > 3:
                        dup_names_str += '...'
                    logger.info(f"   • '{existing_name}' matched with: {dup_names_str}")
                    shown += 1
            if len(duplicates_by_existing) > 5:
                logger.info(f"   ... and {len(duplicates_by_existing) - 5} more duplicate groups")
        
        logger.info(f"✅ Unified mapping: {len(unified_class_names)} unique classes")
        
        # Log all unified class names for debugging (first 20, then count)
        class_list = [unified_class_names[i] for i in sorted(unified_class_names.keys())]
        if len(class_list) <= 20:
            logger.info(f"📋 Unified classes: {', '.join(class_list)}")
        else:
            logger.info(f"📋 Unified classes (first 20): {', '.join(class_list[:20])}...")
            logger.info(f"📋 Total: {len(class_list)} classes (showing first 20)")
        
        if len(unified_class_names) == 0:
            logger.error("❌ No classes found in any dataset! Cannot create training dataset.")
            raise ValueError("No classes found in dataset annotations. Please ensure annotation files contain category definitions.")
        
        # Step 2: Create per-dataset mappings
        dataset_mappings = []
        
        for idx, (ds_path, ds_format) in enumerate(preprocessed_datasets):
            ds_path = Path(ds_path)
            
            if ds_format in ["coco", "coco_standard"]:
                if ds_format == "coco_standard":
                    anno_dir = ds_path / "annotations"
                    anno_files = list(anno_dir.glob("instances_*.json"))
                    if not anno_files:
                        anno_files = list(anno_dir.glob("*.json"))
                else:
                    anno_files = [ds_path / "annotations.json"]
                
                if anno_files and anno_files[0].exists():
                    coco = COCO(str(anno_files[0]))
                    categories = coco.loadCats(coco.getCatIds())
                    
                    coco_to_yolo = {}
                    categories_mapped = 0
                    categories_not_found = []
                    
                    for cat in categories:
                        cat_name = cat['name']
                        cat_id = cat.get('id', 0)
                        # Normalize category name (convert "class_X" to proper COCO name)
                        cat_name = AdvancedCOCOtoYOLOMerger._normalize_category_name(cat_name, cat_id)
                        cat_name_normalized = cat_name.lower().strip()
                        
                        # Case-insensitive matching for mapping
                        matched = False
                        for yolo_id, unified_name in unified_class_names.items():
                            if unified_name.lower().strip() == cat_name_normalized:
                                coco_to_yolo[cat['id']] = yolo_id
                                categories_mapped += 1
                                matched = True
                                break
                        
                        if not matched:
                            categories_not_found.append(cat_name)
                    
                    if categories_not_found:
                        if label_strategy == 'base_dataset' and base_dataset_index is not None and idx != base_dataset_index:
                            logger.info(f"   ⏭️  Dataset {idx + 1} ({ds_path.name}): {len(categories_not_found)} categories filtered out (not in base dataset): {categories_not_found[:5]}{'...' if len(categories_not_found) > 5 else ''}")
                        else:
                            logger.warning(f"   ⚠️  Dataset {idx + 1}: {len(categories_not_found)} categories not found in unified mapping: {categories_not_found[:5]}{'...' if len(categories_not_found) > 5 else ''}")
                    else:
                        logger.debug(f"   ✅ Dataset {idx + 1}: All {categories_mapped} categories mapped successfully")
                    
                    dataset_mappings.append((ds_path, ds_format, coco_to_yolo))
        
        # Step 3: Process all datasets
        logger.info("⚡ Converting datasets to YOLO format...")
        
        total_train_imgs = 0
        total_train_labels = 0
        total_val_imgs = 0
        total_val_labels = 0
        
        for idx, (ds_path, ds_format, class_id_map) in enumerate(dataset_mappings):
            dataset_name = ds_path.name
            
            logger.info(f"📦 Processing dataset {idx + 1}/{len(dataset_mappings)}: {dataset_name}")
            
            if ds_format == "coco_standard":
                anno_dir = ds_path / "annotations"
                train_anno = list(anno_dir.glob("instances_train*.json"))
                val_anno = list(anno_dir.glob("instances_val*.json"))
                
                train_images = ds_path / "train2017" if (ds_path / "train2017").exists() else None
                val_images = ds_path / "val2017" if (ds_path / "val2017").exists() else None
                
                if not train_anno:
                    train_anno = list(anno_dir.glob("*train*.json")) or list(anno_dir.glob("*.json"))
            else:
                train_anno = [ds_path / "annotations.json"]
                val_anno = []
                train_images = ds_path / "images"
                val_images = None
            
            # Extract dataset name from path
            dataset_name = ds_path.name
            
            if train_anno and train_anno[0].exists() and train_images:
                train_imgs, train_labels = self.process_coco_annotations(
                    train_anno[0], train_images, output_labels_train, output_images_train, class_id_map, dataset_name=dataset_name, label_strategy=label_strategy
                )
                total_train_imgs += train_imgs
                total_train_labels += train_labels
            
            if val_anno and val_anno[0].exists() and val_images:
                val_imgs, val_labels = self.process_coco_annotations(
                    val_anno[0], val_images, output_labels_val, output_images_val, class_id_map, dataset_name=dataset_name, label_strategy=label_strategy
                )
                total_val_imgs += val_imgs
                total_val_labels += val_labels
            
            # ASCII visualization for bounding box verification (if enabled)
            if enable_ascii_visualization:
                try:
                    from .ascii_visualizer import visualize_coco_dataset_ascii
                    
                    # Visualize from train set if available, otherwise skip
                    if train_anno and train_anno[0].exists() and train_images:
                        logger.info(f"🎨 Visualizing dataset samples (ASCII art with bounding boxes)...")
                        visualize_coco_dataset_ascii(
                            annotation_file=train_anno[0],
                            images_dir=train_images,
                            num_images=2,
                            dataset_name=dataset_name,
                            ascii_width=80,
                            ascii_height=40,
                            log_to_logger=True
                        )
                except Exception as e:
                    # Don't fail conversion if visualization fails
                    logger.debug(f"ASCII visualization failed: {e}")
        
        # Create dataset.yaml
        logger.info(f"📝 Creating merged dataset.yaml...")
        dataset_yaml = self.output_dir / "dataset.yaml"
        
        # Convert unified_class_names dict to sorted list for YOLO format
        class_names_list = [unified_class_names[i] for i in sorted(unified_class_names.keys())] if unified_class_names else []
        
        with open(dataset_yaml, 'w') as f:
            f.write(f"# YOLO Merged Dataset Configuration\n")
            f.write(f"# Generated from {len(preprocessed_datasets)} dataset(s)\n\n")
            f.write(f"path: {self.output_dir}\n")
            f.write(f"train: images/train\n")
            f.write(f"val: images/{'val' if total_val_imgs > 0 else 'train'}\n\n")
            f.write(f"nc: {len(unified_class_names)}\n")
            f.write(f"names: {class_names_list}\n")
        
        logger.info(f"✅ Dataset merging complete!")
        logger.info(f"   • Total train: {total_train_imgs} images, {total_train_labels} labels")
        logger.info(f"   • Total val: {total_val_imgs} images, {total_val_labels} labels")
        logger.info(f"   • Total classes: {len(unified_class_names)}")
        
        return {
            'dataset_yaml': dataset_yaml,
            'train_images': total_train_imgs,
            'train_labels': total_train_labels,
            'val_images': total_val_imgs,
            'val_labels': total_val_labels,
            'classes': len(unified_class_names),
            'class_names': list(unified_class_names.values())
        }
