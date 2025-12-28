"""
YOLO Training Script for Kaggle and Training Agents (Simplified with aegis-vision)

This script uses the aegis-vision package for simplified training.
Includes automatic dataset discovery, merging, and Wandb integration.

Works on:
- Kaggle notebooks
- Training agents (local/remote machines)
"""

import sys
import json
import subprocess
import os
from pathlib import Path
from datetime import datetime

# Detect environment
IS_KAGGLE = Path("/kaggle").exists()
IS_AGENT = os.environ.get("AEGIS_AGENT_MODE") == "1"

if IS_KAGGLE:
    # CRITICAL: Fix NumPy compatibility BEFORE any other imports (Kaggle only)
    print("📦 Checking NumPy compatibility...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "--force-reinstall", "numpy<2.0"])
        print("✅ NumPy 1.x installed")
        
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "--force-reinstall", "--no-deps", "matplotlib"])
        print("✅ Matplotlib reinstalled for NumPy 1.x")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Failed to reinstall packages: {e}")

# Install aegis-vision if not already installed (Kaggle only)
if IS_KAGGLE:
    try:
        import aegis_vision
        print(f"✅ aegis-vision {aegis_vision.__version__} already installed")
    except ImportError:
        print("📦 Installing aegis-vision...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "aegis-vision>=0.2.3"])
        import aegis_vision
        print(f"✅ aegis-vision {aegis_vision.__version__} installed")
else:
    import aegis_vision

from aegis_vision import (
    YOLOTrainer,
    AdvancedCOCOtoYOLOMerger,
    discover_datasets,
    preprocess_datasets,
    setup_logging,
    detect_environment
)
from aegis_vision.environment_check import EnvironmentChecker

# Environment-specific paths
if IS_KAGGLE:
    INPUT_DIR = Path("/kaggle/input")
    WORKING_DIR = Path("/kaggle/working")
else:
    # For agents, paths will be passed via config
    INPUT_DIR = Path(os.environ.get("AEGIS_INPUT_DIR", "."))
    WORKING_DIR = Path(os.environ.get("AEGIS_WORKING_DIR", "."))

# Output directory for models (consistent storage location)
if IS_KAGGLE:
    OUTPUT_DIR = Path("/kaggle/working")
else:
    # For agent mode, use working directory; otherwise use ~/.aegis-vision
    if os.environ.get("AEGIS_AGENT_MODE"):
        OUTPUT_DIR = WORKING_DIR / "trained_models"
    else:
        OUTPUT_DIR = Path.home() / ".aegis-vision" / "models"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# EMBEDDED_CONFIG_PLACEHOLDER
EMBEDDED_CONFIG = """{{TRAINING_CONFIG_JSON}}"""

# Setup logging
setup_logging(level="INFO")

import logging
logger = logging.getLogger(__name__)


def log_progress(message: str, **kwargs):
    """Log training progress directly for real-time visibility"""
    print(message)
    logger.info(message)


def main():
    """Main training function"""
    try:
        env_name = "Kaggle" if IS_KAGGLE else "Training Agent"
        log_progress(f"🚀 Starting Aegis Vision training on {env_name}")
        log_progress(f"📦 aegis-vision version: {aegis_vision.__version__}")
        log_progress(f"📂 Input directory: {INPUT_DIR}")
        log_progress(f"📂 Working directory: {WORKING_DIR}")
        
        # Detect environment
        env = detect_environment()
        log_progress(f"🌍 Environment detected: {env}")
        
        # Check CUDA compatibility BEFORE training starts
        # This catches "no kernel image is available for execution on the device" errors early
        log_progress("🔍 Checking CUDA compatibility...")
        cuda_issue = EnvironmentChecker.check_pytorch_cuda_compatibility()
        if cuda_issue and cuda_issue.severity == 'error':
            error_msg = (
                f"\n❌ {cuda_issue.title}\n"
                f"{'='*70}\n"
                f"{cuda_issue.description}\n"
                f"{'='*70}\n"
            )
            if cuda_issue.alternative_solution:
                error_msg += f"\n💡 Recommended Solution:\n{cuda_issue.alternative_solution}\n"
            if cuda_issue.fix_command:
                error_msg += f"\n🔧 Or try automatic fix:\n{cuda_issue.fix_command}\n"
            log_progress(error_msg, status="error")
            sys.exit(1)
        elif cuda_issue and cuda_issue.severity == 'warning':
            log_progress(f"⚠️  {cuda_issue.title}: {cuda_issue.description}", status="warning")
        
        # Load configuration
        log_progress("📋 Loading training configuration...")
        
        config = {}
        config_source = None
        
        # Priority 1: Environment variable (for remote agents)
        env_config = os.environ.get('AEGIS_TRAINING_CONFIG')
        if env_config:
            try:
                config = json.loads(env_config)
                config_source = "environment variable (AEGIS_TRAINING_CONFIG)"
                log_progress("✅ Loaded training config from environment variable")
            except json.JSONDecodeError as e:
                log_progress(f"⚠️  Failed to parse config from environment: {e}", status="warning")
        
        # Priority 2: Embedded config (for Kaggle notebooks)
        if not config:
            try:
                if EMBEDDED_CONFIG and not EMBEDDED_CONFIG.startswith("{{"):
                    config = json.loads(EMBEDDED_CONFIG)
                    config_source = "embedded"
                    log_progress("✅ Loaded training config from embedded source")
            except json.JSONDecodeError as e:
                log_progress(f"⚠️  Failed to parse embedded config: {e}", status="warning")
        
        # Priority 3: File-based config (fallback for local agents)
        if not config:
            # First, try the input directory root (agent training)
            config_file = INPUT_DIR / "training_config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    config_source = f"file ({config_file})"
                    log_progress("✅ Loaded training config from file")
            else:
                # Then try inside dataset subdirectories (Kaggle)
                for dataset_dir in INPUT_DIR.iterdir():
                    if dataset_dir.is_dir():
                        config_file = dataset_dir / "training_config.json"
                        if config_file.exists():
                            with open(config_file, 'r') as f:
                                config = json.load(f)
                                config_source = f"file ({config_file})"
                                log_progress("✅ Loaded training config from file")
                            break
        
        # Use defaults if no config found
        if not config:
            log_progress("⚠️  No config found, using defaults", status="warning")
            config = {
                "model_variant": "yolov8n",
                "epochs": 10,
                "batch_size": 16,
                "img_size": 640,
                "output_formats": ["onnx"],
            }
        
        log_progress(f"📋 Config loaded from: {config_source}")
        
        # DEBUG: Log the raw config to see what we received
        log_progress(f"🔍 DEBUG: Raw config keys: {list(config.keys())}")
        log_progress(f"🔍 DEBUG: epochs in config = {config.get('epochs', 'NOT FOUND')}")
        
        # Extract config parameters
        model_variant = config.get('model_variant', 'yolov8n')
        epochs = config.get('epochs', 10)
        batch_size = config.get('batch_size', 0.8)  # 0.8 = auto 80% GPU memory
        img_size = config.get('img_size', 640)
        output_formats = config.get('output_formats', ['onnx'])
        training_mode = config.get('training_mode', 'fine_tune')  # NEW: "fine_tune" or "from_scratch"
        resume_checkpoint = config.get('resume_checkpoint', None)  # Path to checkpoint for resuming
        # Label management strategy
        label_strategy = config.get('labelStrategy', 'merge_all')  # 'merge_all' or 'base_dataset'
        
        log_progress(f"🔍 DEBUG: After extraction, epochs = {epochs}")
        log_progress(f"🔍 DEBUG: training_mode = {training_mode}")
        log_progress(f"🔍 DEBUG: label_strategy = {label_strategy}")
        
        if resume_checkpoint:
            log_progress(f"🔄 Resume mode: Will continue training from checkpoint: {resume_checkpoint}")
        
        # Wandb configuration
        wandb_enabled = config.get('wandb_enabled', False)
        wandb_project = config.get('wandb_project', '')
        wandb_entity = config.get('wandb_entity', None)
        
        # Extract all training hyperparameters from config
        learning_rate = config.get('learning_rate', 0.01)
        momentum = config.get('momentum', 0.937)
        weight_decay = config.get('weight_decay', 0.0005)
        warmup_epochs = config.get('warmup_epochs', 3)
        
        # Early stopping configuration
        early_stopping_config = config.get('early_stopping', {})
        patience = early_stopping_config.get('patience', 50) if isinstance(early_stopping_config, dict) else 50
        
        # Additional hyperparameters
        hsv_h = config.get('hsv_h', 0.015)  # HSV-Hue augmentation
        hsv_s = config.get('hsv_s', 0.7)    # HSV-Saturation augmentation
        hsv_v = config.get('hsv_v', 0.4)    # HSV-Value augmentation
        degrees = config.get('degrees', 0.0)  # Rotation degrees
        translate = config.get('translate', 0.1)  # Translation
        scale = config.get('scale', 0.5)  # Scale augmentation
        flipud = config.get('flipud', 0.0)  # Flip up-down
        fliplr = config.get('fliplr', 0.5)  # Flip left-right
        mosaic = config.get('mosaic', 1.0)  # Mosaic augmentation
        mixup = config.get('mixup', 0.0)  # Mixup augmentation
        
        batch_display = 'Auto (60%)' if batch_size == 0.6 else 'Auto (80%)' if batch_size == 0.8 else batch_size
        log_progress("📊 Training configuration summary",
                    model=model_variant,
                    epochs=epochs,
                    batch_size=batch_display,
                    img_size=img_size,
                    learning_rate=learning_rate,
                    patience=patience,
                    training_mode=training_mode,
                    wandb_enabled=wandb_enabled)
        
        # Discover datasets using aegis-vision
        log_progress("🔍 Discovering datasets...")
        datasets_found = discover_datasets(INPUT_DIR)
        
        if not datasets_found:
            log_progress(f"❌ No datasets found in {INPUT_DIR}", status="error")
            sys.exit(1)
        
        log_progress(f"📊 Found {len(datasets_found)} dataset(s)")
        
        if len(datasets_found) == 1:
            log_progress("🎯 Single dataset detected - will convert if needed")
        else:
            log_progress(f"🔀 Multiple datasets detected ({len(datasets_found)}) - will merge")
        
        # Preprocess datasets (convert COCO standard to flat format)
        preprocessed_datasets = preprocess_datasets(datasets_found, WORKING_DIR)
        
        # For base_dataset strategy, find the base dataset by name
        actual_base_index = None
        if label_strategy == 'base_dataset':
            base_dataset_name = config.get('baseDatasetName', None)
            
            if not base_dataset_name:
                error_msg = (
                    f"❌ Configuration error: label_strategy='base_dataset' but baseDatasetName is missing. "
                    f"Training cannot proceed without knowing which dataset to use as the base."
                )
                log_progress(error_msg, status="error")
                raise ValueError(error_msg)
            
            log_progress(f"🔍 DEBUG: Label strategy is 'base_dataset', looking for: {base_dataset_name}")
            log_progress(f"🔍 DEBUG: Found {len(datasets_found)} datasets, preprocessed {len(preprocessed_datasets)} datasets")
            
            # Sanitize name to match folder naming (same as agent does)
            safe_name = base_dataset_name.replace('/', '-').replace(' ', '-').lower()
            log_progress(f"🔍 DEBUG: Sanitized base dataset name: {safe_name}")
            
            # Try to find matching dataset in discovered datasets
            for i, ds_info in enumerate(datasets_found):
                ds_name = ds_info.get('name', '')
                ds_path_name = Path(ds_info.get('path', '')).name.lower()
                if safe_name in ds_name.lower() or safe_name in ds_path_name:
                    actual_base_index = i
                    log_progress(f"🔍 DEBUG: Found base dataset at index {i}: {ds_name} (path: {ds_path_name})")
                    break
            
            # If not found in discovered datasets, try matching against preprocessed dataset paths
            if actual_base_index is None:
                for i, (ds_path, ds_format) in enumerate(preprocessed_datasets):
                    ds_path_name = Path(ds_path).name.lower()
                    if safe_name in ds_path_name:
                        actual_base_index = i
                        log_progress(f"🔍 DEBUG: Found base dataset at preprocessed index {i}: {ds_path_name}")
                        break
            
            # Validate we found the base dataset
            if actual_base_index is None:
                available_names = [ds.get('name', Path(ds.get('path', '')).name) for ds in datasets_found]
                error_msg = (
                    f"❌ Configuration error: Could not find base dataset '{base_dataset_name}' (sanitized: '{safe_name}'). "
                    f"Found {len(datasets_found)} discovered datasets. "
                    f"Available dataset names: {available_names}. "
                    f"Training cannot proceed without identifying the base dataset."
                )
                log_progress(error_msg, status="error")
                raise ValueError(error_msg)
            
            # Log all datasets for debugging
            for i, (ds_path, ds_format) in enumerate(preprocessed_datasets):
                marker = " <-- BASE" if i == actual_base_index else ""
                log_progress(f"🔍 DEBUG: Preprocessed dataset {i}: {Path(ds_path).name} ({ds_format}){marker}")
        
        # Merge and convert datasets to YOLO format
        if label_strategy == 'base_dataset' and actual_base_index is not None:
            log_progress(f"⚡ Merging datasets with base dataset strategy (using dataset at index {actual_base_index})...")
        else:
            log_progress("⚡ Merging datasets and converting to YOLO format...")
        output_dir = WORKING_DIR / "yolo_dataset"
        merger = AdvancedCOCOtoYOLOMerger(output_dir=output_dir)
        
        # Enable ASCII visualization for agent mode (helps verify bounding box handling)
        # Can be disabled via config: "enable_ascii_visualization": false
        enable_ascii_viz = config.get('enable_ascii_visualization', IS_AGENT)
        if enable_ascii_viz:
            log_progress("🎨 ASCII visualization enabled - will show 2 sample images per dataset with bounding boxes")
        
        merge_result = merger.merge_and_convert(
            preprocessed_datasets,
            enable_ascii_visualization=enable_ascii_viz,
            label_strategy=label_strategy,
            base_dataset_index=actual_base_index if label_strategy == 'base_dataset' else None
        )
        
        dataset_yaml = merge_result['dataset_yaml']
        log_progress(f"✅ Dataset ready: {dataset_yaml}")
        log_progress(f"   • Train: {merge_result['train_images']} images, {merge_result['train_labels']} labels")
        log_progress(f"   • Val: {merge_result['val_images']} images, {merge_result['val_labels']} labels")
        log_progress(f"   • Classes: {merge_result['classes']}")
        
        # Setup Wandb if enabled
        wandb_api_key = None
        if wandb_enabled:
            log_progress("🔧 Setting up Wandb integration...")
            
            wandb_api_key = os.environ.get('WANDB_API_KEY')
            
            if not wandb_api_key:
                log_progress("⚠️  WANDB_API_KEY not found in environment", status="warning")
                log_progress("    Wandb tracking disabled. Set WANDB_API_KEY env var to enable.", status="warning")
                wandb_enabled = False
            else:
                log_progress(f"✅ Found WANDB_API_KEY in environment")
                log_progress(f"📊 Wandb Project: {wandb_project}")
                if wandb_entity:
                    log_progress(f"📊 Wandb Entity: {wandb_entity}")
        
        # Initialize trainer
        log_progress(f"🤖 Initializing YOLOTrainer with {model_variant}...")
        
        trainer = YOLOTrainer(
            model_variant=model_variant,
            dataset_path=str(dataset_yaml),
            epochs=epochs,
            batch_size=batch_size,
            img_size=img_size,
            output_formats=output_formats,
            learning_rate=learning_rate,
            momentum=momentum,
            weight_decay=weight_decay,
            warmup_epochs=warmup_epochs,
            patience=patience,
            training_mode=training_mode,  # NEW: Pass training mode to control pretrained weights
            resume_checkpoint=resume_checkpoint,  # NEW: Path to checkpoint for resuming training
            hsv_h=hsv_h,
            hsv_s=hsv_s,
            hsv_v=hsv_v,
            degrees=degrees,
            translate=translate,
            scale=scale,
            flipud=flipud,
            fliplr=fliplr,
            mosaic=mosaic,
            mixup=mixup,
            output_dir=str(OUTPUT_DIR),  # Pass the configured output directory
        )
        
        # Setup Wandb with API key and config
        if wandb_enabled and wandb_api_key:
            log_progress("📊 Configuring Wandb tracking...")
            primary_dataset_name = datasets_found[0]["name"] if datasets_found else "merged"
            run_name = f"{model_variant}_{primary_dataset_name}"
            if len(datasets_found) > 1:
                run_name += f"_plus{len(datasets_found)-1}"
            
            try:
                trainer.setup_wandb(
                    project=wandb_project or 'aegis-ai',
                    entity=wandb_entity,
                    api_key=wandb_api_key,
                    run_name=run_name
                )
                log_progress(f"✅ Wandb run initialized: {run_name}")
            except Exception as e:
                log_progress(f"⚠️  Failed to setup Wandb: {str(e)}", status="warning")
                log_progress("   Training will continue without Wandb tracking", status="warning")
        elif not wandb_enabled:
            log_progress("📊 Wandb tracking disabled for this training run")
        
        # Train
        log_progress(f"🚀 Starting training for {epochs} epochs...")
        results = trainer.train()
        
        # Extract metrics from training results
        training_metrics = results.get('metrics', {})
        if training_metrics:
            log_progress(f"📊 Training Metrics:")
            log_progress(f"   • mAP50: {training_metrics.get('mAP50', 'N/A')}")
            log_progress(f"   • mAP50-95: {training_metrics.get('mAP50_95', 'N/A')}")
            log_progress(f"   • Precision: {training_metrics.get('precision', 'N/A')}")
            log_progress(f"   • Recall: {training_metrics.get('recall', 'N/A')}")
        
        log_progress("✅ Training completed successfully!")
        log_progress(f"📊 Results saved to: {WORKING_DIR / 'runs'}")
        
        # Finish Wandb run (sync all metrics)
        if wandb_enabled:
            log_progress("📊 Finishing Wandb run and syncing metrics...")
            trainer.finish_wandb()
        
        # Export models
        export_results = None
        if output_formats:
            log_progress(f"\n{'='*70}")
            log_progress(f"📤 MODEL EXPORT CONFIGURATION")
            log_progress(f"{'='*70}")
            log_progress(f"🎯 Target formats: {output_formats}")
            log_progress(f"📍 Format count: {len(output_formats)}")
            log_progress(f"📂 Output directory: {OUTPUT_DIR}")
            log_progress(f"\n🚀 Starting model export process...")
            log_progress(f"{'='*70}\n")
            
            export_results = trainer.export(formats=output_formats)
            
            log_progress(f"\n{'='*70}")
            log_progress(f"📊 EXPORT RESULTS SUMMARY")
            log_progress(f"{'='*70}")
            log_progress(f"✅ Successfully exported: {export_results.get('exported', [])}")
            log_progress(f"❌ Failed to export: {export_results.get('failed', [])}")
            log_progress(f"📊 Total formats attempted: {export_results.get('total', 0)}")
            
            if export_results.get('details'):
                log_progress(f"\n📝 Detailed Results:")
                for fmt, details in export_results.get('details', {}).items():
                    status_emoji = "✅" if details['status'] == 'success' else "❌"
                    log_progress(f"  {status_emoji} {fmt.upper()}: {details['status']}")
                    if details.get('error'):
                        log_progress(f"       Error: {details['error']}")
            
            log_progress(f"{'='*70}\n")
        else:
            log_progress("⚠️  No export formats specified, skipping model export")
        
        # Copy models to output directory
        log_progress("📦 Preparing models for download...")
        trainer.prepare_kaggle_output(output_dir=OUTPUT_DIR)
        
        # Upload to Kaggle Model Hub if enabled
        kaggle_upload_enabled = config.get('kaggle_upload_enabled', False)
        
        # DEBUG: Log Kaggle upload configuration
        log_progress(f"🔍 DEBUG: Kaggle upload enabled: {kaggle_upload_enabled}")
        log_progress(f"🔍 DEBUG: Config keys: {list(config.keys())}")
        
        # ✅ Prepare training results JSON
        # Use ACTUAL exported formats from export_results, not requested formats
        actually_exported = export_results.get('exported', []) if export_results else []
        training_results = {
            "success": True,
            "model_variant": model_variant,
            "epochs_trained": epochs,
            "output_dir": str(OUTPUT_DIR),
            "model_files": [],
            "exported_formats": actually_exported,  # ✅ Use actual successful exports
            "wandb_url": None,
            "kaggle_model_url": None,
            "metrics": training_metrics,  # ✅ Include training metrics
            "dataset_info": {
                "name": datasets_found[0]['name'] if datasets_found else 'Custom Dataset',
                "num_classes": merge_result.get('classes', 'N/A'),
                "train_images": merge_result.get('train_images', 'N/A'),
                "val_images": merge_result.get('val_images', 'N/A'),
            },
            "completed_at": datetime.now().isoformat(),
        }
        
        # List model files that were created
        if OUTPUT_DIR.exists():
            for file_path in OUTPUT_DIR.iterdir():
                if file_path.is_file() and file_path.suffix in ['.pt', '.pth', '.onnx', '.engine', '.tflite', '.pb', '.xml', '.bin']:
                    training_results["model_files"].append({
                        "name": file_path.name,
                        "size_mb": file_path.stat().st_size / (1024 * 1024),
                        "format": file_path.suffix[1:],  # Remove the dot
                    })
                elif file_path.is_dir() and file_path.suffix == '.mlpackage':
                    # CoreML package
                    dir_size = sum(f.stat().st_size for f in file_path.rglob('*') if f.is_file())
                    training_results["model_files"].append({
                        "name": file_path.name,
                        "size_mb": dir_size / (1024 * 1024),
                        "format": "coreml",
                        "is_directory": True,
                    })
        
        # Get Wandb run URL if enabled
        if wandb_enabled and hasattr(trainer, 'wandb_run') and trainer.wandb_run:
            try:
                wandb_url = trainer.wandb_run.get_url()
                training_results["wandb_url"] = wandb_url
                log_progress(f"📊 Wandb run URL: {wandb_url}")
            except Exception as e:
                log_progress(f"⚠️  Could not get Wandb URL: {e}", status="warning")
        
        if kaggle_upload_enabled:
            log_progress("🚀 Uploading model to Kaggle Model Hub...")
            
            kaggle_username = os.environ.get('KAGGLE_USERNAME')
            kaggle_api_key = os.environ.get('KAGGLE_KEY')
            kaggle_model_slug = config.get('kaggle_model_slug')
            
            log_progress(f"🔍 DEBUG: Kaggle username from env: {'SET' if kaggle_username else 'NOT SET'}")
            log_progress(f"🔍 DEBUG: Kaggle API key from env: {'SET' if kaggle_api_key else 'NOT SET'}")
            log_progress(f"🔍 DEBUG: Kaggle model slug from config: {kaggle_model_slug}")
            
            if kaggle_username and kaggle_api_key and kaggle_model_slug:
                try:
                    from aegis_vision.kaggle_uploader import upload_trained_model
                    
                    log_progress(f"📦 Uploading from directory: {OUTPUT_DIR}")
                    log_progress(f"📦 Model slug: {kaggle_model_slug}")
                    log_progress(f"📦 Model variant: {model_variant}")
                    
                    # Prepare dataset info
                    dataset_info = {
                        'name': datasets_found[0]['name'] if datasets_found else 'Custom Dataset',
                        'num_classes': merge_result.get('classes', 'N/A'),
                        'train_images': merge_result.get('train_images', 'N/A'),
                        'val_images': merge_result.get('val_images', 'N/A')
                    }
                    
                    # Upload model
                    upload_result = upload_trained_model(
                        model_dir=str(OUTPUT_DIR),
                        model_slug=kaggle_model_slug,
                        model_variant=model_variant,
                        training_config=config,
                        kaggle_username=kaggle_username,
                        kaggle_api_key=kaggle_api_key,
                        metrics=training_metrics,  # ✅ Pass training metrics
                        dataset_info=dataset_info
                    )
                    
                    if upload_result.get('success'):
                        log_progress(f"✅ Model uploaded successfully!")
                        log_progress(f"   URL: {upload_result.get('model_url')}")
                        log_progress(f"   Files: {upload_result.get('files_uploaded')} uploaded")
                        # ✅ Add Kaggle model URL to results
                        training_results["kaggle_model_url"] = upload_result.get('model_url')
                        training_results["kaggle_files_uploaded"] = upload_result.get('files_uploaded')
                    else:
                        log_progress(f"⚠️  Model upload failed: {upload_result.get('error')}", status="warning")
                        log_progress(f"   Help: {upload_result.get('help', 'N/A')}", status="warning")
                        log_progress("   Training completed successfully, but upload failed", status="warning")
                        # ✅ Include error in results
                        training_results["kaggle_upload_error"] = upload_result.get('error')
                        
                except Exception as e:
                    log_progress(f"⚠️  Failed to upload model to Kaggle: {str(e)}", status="warning")
                    import traceback
                    log_progress(f"   Traceback: {traceback.format_exc()}", status="warning")
                    log_progress("   Training completed successfully, but upload failed", status="warning")
            else:
                missing = []
                if not kaggle_username:
                    missing.append("KAGGLE_USERNAME environment variable")
                if not kaggle_api_key:
                    missing.append("KAGGLE_KEY environment variable")
                if not kaggle_model_slug:
                    missing.append("kaggle_model_slug in config")
                
                log_progress(f"⚠️  Kaggle upload skipped - missing: {', '.join(missing)}", status="warning")
                log_progress("   To enable Kaggle upload:", status="warning")
                log_progress("   1. Set kaggleUploadEnabled=true in training config", status="warning")
                log_progress("   2. Provide Kaggle username and API key", status="warning")
                log_progress("   3. Provide kaggle_model_slug", status="warning")
        else:
            log_progress("ℹ️  Kaggle upload disabled in configuration")
        
        log_progress("🎉 All tasks completed successfully!")
        
        # ✅ Save training results to JSON file (for agent to read)
        results_file = WORKING_DIR / "training_results.json"
        with open(results_file, 'w') as f:
            json.dump(training_results, f, indent=2)
        log_progress(f"📄 Training results saved to: {results_file}")
        
        # ✅ Also output to stdout for backwards compatibility
        results_json = json.dumps(training_results, indent=2)
        print("=== TRAINING_RESULTS_JSON ===")
        print(results_json)
        print("=== END_TRAINING_RESULTS ===")
        
    except Exception as e:
        error_msg = str(e)
        error_lower = error_msg.lower()
        
        # Check for CUDA kernel compatibility errors
        if 'no kernel image' in error_lower or 'cudaerrornokernelimagefordevice' in error_lower:
            log_progress("❌ Training failed: CUDA kernel compatibility error", status="error")
            log_progress("="*70, status="error")
            log_progress(f"Error: {error_msg}", status="error")
            log_progress("="*70, status="error")
            log_progress("", status="error")
            log_progress("💡 This error means PyTorch was compiled for a different GPU architecture.", status="error")
            log_progress("", status="error")
            log_progress("🔧 Solutions:", status="error")
            log_progress("  1. Use NVIDIA NGC Docker container (RECOMMENDED):", status="error")
            log_progress("     docker pull nvcr.io/nvidia/pytorch:24.12-py3", status="error")
            log_progress("", status="error")
            log_progress("  2. Reinstall PyTorch with correct CUDA version:", status="error")
            try:
                import torch
                import subprocess
                import re
                
                # Try to get system CUDA version from nvcc
                system_cuda = None
                try:
                    result = subprocess.run(
                        ['nvcc', '--version'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        match = re.search(r'release\s+([\d.]+)', result.stdout)
                        if match:
                            system_cuda = match.group(1)
                except:
                    pass
                
                pytorch_cuda = torch.version.cuda
                
                if system_cuda:
                    # Map system CUDA to PyTorch wheel version
                    major, minor = map(int, system_cuda.split('.')[:2])
                    if major == 11:
                        pytorch_wheel = "cu118"
                    elif major == 12:
                        if minor >= 8:
                            pytorch_wheel = "cu128"  # CUDA 12.8+
                        elif minor >= 6:
                            pytorch_wheel = "cu126"  # CUDA 12.6-12.7
                        elif minor >= 4:
                            pytorch_wheel = "cu124"  # CUDA 12.4-12.5
                        else:
                            pytorch_wheel = "cu121"  # CUDA 12.1-12.3
                    elif major >= 13:
                        pytorch_wheel = "cu126"  # CUDA 13+ (or cu128 if available)
                    else:
                        pytorch_wheel = "cu118"
                    
                    log_progress(f"     System CUDA: {system_cuda} -> PyTorch wheel: {pytorch_wheel}", status="error")
                    log_progress(f"     pip uninstall -y torch torchvision torchaudio", status="error")
                    log_progress(f"     pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/{pytorch_wheel}", status="error")
                else:
                    # Fallback to PyTorch's CUDA version
                    cuda_major_minor = pytorch_cuda.replace('.', '')[:2]
                    log_progress(f"     PyTorch CUDA: {pytorch_cuda} -> cu{cuda_major_minor}", status="error")
                    log_progress(f"     pip uninstall -y torch torchvision torchaudio", status="error")
                    log_progress(f"     pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu{cuda_major_minor}", status="error")
            except:
                log_progress("     pip uninstall -y torch torchvision torchaudio", status="error")
                log_progress("     pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118", status="error")
            log_progress("", status="error")
            log_progress("  3. For newer GPUs (H100, H200, Blackwell), use PyTorch nightly:", status="error")
            log_progress("     pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu126", status="error")
            log_progress("", status="error")
            log_progress("📖 See: https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__TYPES.html", status="error")
        else:
            log_progress(f"❌ Training failed: {error_msg}", status="error")
            import traceback
            log_progress(f"Traceback: {traceback.format_exc()}", status="error")
        
        sys.exit(1)


if __name__ == "__main__":
    main()

