"""
Aegis Agent CLI

Command-line interface for managing and running training agents.
"""

# CRITICAL: Set headless environment for OpenCV BEFORE any imports
# This prevents OpenCV from trying to load GUI libraries in headless environments
import os
from .headless_utils import setup_headless_environment
setup_headless_environment()

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Lazy imports to avoid requiring firebase_admin for all commands
def _import_agent_modules():
    """Lazy import of agent modules that require firebase_admin"""
    try:
        from .agent import TrainingAgent, AgentCapabilities
        from .agent_auth import AgentAuthenticator, AgentAuthenticationError
        return TrainingAgent, AgentCapabilities, AgentAuthenticator, AgentAuthenticationError
    except ImportError as e:
        if 'firebase_admin' in str(e) or 'google.cloud.firestore' in str(e):
            print("❌ Error: Required dependencies not found")
            print()
            print("Please reinstall aegis-vision:")
            print("  pip install --upgrade aegis-vision")
            print()
            print("If the error persists, try:")
            print("  pip install firebase-admin google-cloud-firestore")
            sys.exit(1)
        else:
            raise


def setup_logging(verbose: bool = False) -> None:
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def cmd_login(args) -> int:
    """Interactive login command (like huggingface-cli login)"""
    try:
        # Check for libGL before proceeding
        from .headless_utils import check_and_fix_libgl
        check_and_fix_libgl()
        
        _, _, AgentAuthenticator, _ = _import_agent_modules()
        
        print("🔐 Aegis AI Agent Login")
        print()
        print("To get your API key:")
        print("  1. Open Aegis AI application")
        print("  2. Go to: Model Training → Settings → Training Agents")
        print("  3. Click 'Add Agent' and copy the API key")
        print()
        
        # Get API key from user (visible input for easy verification)
        api_key = input("Enter your API key: ").strip()
        
        if not api_key:
            print("❌ API key is required")
            return 1
        
        # Validate API key format
        if not api_key.startswith('ak_'):
            print("❌ Invalid API key format. API keys should start with 'ak_'")
            return 1
        
        # Validate API key and retrieve owner info
        print()
        print("🔍 Validating API key...")
        import requests
        
        # Test API key by exchanging for token
        try:
            url = f"{args.cloud_function_url}/auth/agent/token"
            headers = {
                'Authorization': f"Bearer {api_key}",
                'Content-Type': 'application/json'
            }
            response = requests.post(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('success'):
                print(f"❌ API key validation failed: {data.get('message', 'Unknown error')}")
                return 1
            
            # Extract agent ID and owner info from response
            # IMPORTANT: Use the agent ID returned by the Cloud Function, not a generated one
            agent_id = data.get('agentId')
            if not agent_id:
                print("❌ API key validation failed: No agent ID returned")
                return 1
            
            owner_uid = data.get('ownerUid')
            owner_email = data.get('ownerEmail')
            owner_name = data.get('ownerName')
            
            print(f"✅ API key validated")
            print(f"   Agent ID: {agent_id}")
            if owner_uid:
                print(f"   Owner UID: {owner_uid}")
            if owner_email or owner_name:
                print(f"   Owner: {owner_name or ''} ({owner_email or 'no email'})")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to validate API key: {e}")
            return 1
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return 1
        
        # Get machine/host name for identification
        import socket
        default_hostname = socket.gethostname()
        print()
        machine_name = input(f"Enter machine name (press Enter for '{default_hostname}'): ").strip()
        if not machine_name:
            machine_name = default_hostname
        
        # Create config file with owner info
        config_path = AgentAuthenticator.create_config_file(
            agent_id=agent_id,
            api_key=api_key,
            config_path=Path(args.config) if args.config else None,
            agent_name=machine_name,
            cloud_function_url=args.cloud_function_url,
            firestore_project=args.firestore_project,
            owner_uid=owner_uid,
            owner_email=owner_email,
            owner_name=owner_name
        )
        
        print()
        print(f"✅ Login successful!")
        print(f"   Configuration saved to: {config_path}")
        print(f"   Agent ID: {agent_id}")
        print(f"   Machine Name: {machine_name}")
        print()
        print("Next steps:")
        print("  1. Start the agent: aegis-agent start")
        print("  2. The agent will appear online in the Aegis AI application")
        print("  3. Submit training tasks from the application")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n❌ Login cancelled")
        return 1
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return 1


def cmd_init(args) -> int:
    """Initialize agent configuration"""
    try:
        # Check for libGL before proceeding
        from .headless_utils import check_and_fix_libgl
        check_and_fix_libgl()
        
        _, _, AgentAuthenticator, _ = _import_agent_modules()
        
        if not args.api_key:
            print("Error: --api-key is required")
            print("Get your API key from the Aegis AI application:")
            print("  Model Training → Settings → Training Agents → Add Agent")
            print()
            print("Tip: Use 'aegis-agent login' for interactive setup")
            return 1
        
        # Generate agent ID if not provided
        if not args.agent_id:
            import uuid
            agent_id = f"agent-{uuid.uuid4().hex[:16]}"
        else:
            agent_id = args.agent_id
        
        # Create config file
        config_path = AgentAuthenticator.create_config_file(
            agent_id=agent_id,
            api_key=args.api_key,
            config_path=Path(args.config) if args.config else None,
            agent_name=args.name,
            cloud_function_url=args.cloud_function_url,
            firestore_project=args.firestore_project
        )
        
        print(f"✅ Agent configuration created: {config_path}")
        print(f"   Agent ID: {agent_id}")
        print(f"   Agent Name: {args.name or f'Agent {agent_id[:8]}'}")
        print()
        print("Next steps:")
        print("  1. Start the agent: aegis-agent start")
        print("  2. The agent will appear online in the Aegis AI application")
        print("  3. Submit training tasks from the application")
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return 1


def cmd_start(args) -> int:
    """Start the agent daemon"""
    try:
        TrainingAgent, _, AgentAuthenticator, AgentAuthenticationError = _import_agent_modules()
        setup_logging(args.verbose)
        
        # Check environment compatibility BEFORE starting agent
        if not args.skip_env_check:
            from .environment_check import check_environment_interactive
            
            print()
            env_ok = check_environment_interactive()
            print()
            
            if not env_ok:
                print("❌ Environment check failed. Please fix the issues above.")
                print()
                print("💡 You can skip this check with --skip-env-check (not recommended)")
                return 1
        
        # Load authenticator
        config_path = Path(args.config) if args.config else None
        authenticator = AgentAuthenticator(config_path)
        
        # Create and start agent
        work_dir = Path(args.work_dir) if args.work_dir else None
        agent = TrainingAgent(authenticator, work_dir)
        
        print(f"🚀 Starting Aegis AI Training Agent")
        print(f"   Agent ID: {agent.agent_id}")
        print(f"   Work Directory: {agent.work_dir}")
        print()
        
        # Show capabilities
        caps = agent.capabilities
        print("📊 System Capabilities:")
        print(f"   Platform: {caps['platform']}")
        print(f"   Memory: {caps['totalMemoryGB']}GB total, {caps['availableMemoryGB']}GB available")
        print(f"   Storage: {caps['availableStorageGB']}GB available")
        print(f"   CPU Cores: {caps['cpuCount']}")
        if caps['hasGPU']:
            print(f"   GPU: Yes ({caps.get('gpuDetectionMethod', 'Unknown')})")
            print(f"   CUDA: {caps['cudaVersion']}")
            for gpu in caps['gpuInfo']:
                print(f"     {gpu['name']} ({gpu['memory']}GB, Compute: {gpu.get('computeCapability', 'Unknown')})")
        else:
            print(f"   GPU: No")
        print()
        
        # Start agent
        agent.start()
        
        return 0
        
    except AgentAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print()
        print("Make sure you have run 'aegis-agent init' first.")
        return 1
    except KeyboardInterrupt:
        print("\n👋 Agent stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Agent error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_status(args) -> int:
    """Show agent status"""
    try:
        _, AgentCapabilities, AgentAuthenticator, _ = _import_agent_modules()
        
        config_path = Path(args.config) if args.config else None
        authenticator = AgentAuthenticator(config_path)
        
        print(f"📊 Agent Status")
        print(f"   Agent ID: {authenticator.get_agent_id()}")
        print(f"   Config: {authenticator.config_path}")
        print(f"   Firestore Project: {authenticator.get_firestore_project()}")
        print()
        
        # Show capabilities
        caps = AgentCapabilities.detect()
        print("💻 System Capabilities:")
        print(f"   Platform: {caps['platform']}")
        print(f"   Python: {caps['pythonVersion']}")
        print(f"   Memory: {caps['availableMemoryGB']}GB / {caps['totalMemoryGB']}GB")
        print(f"   Storage: {caps['availableStorageGB']}GB / {caps['totalStorageGB']}GB")
        print(f"   CPU: {caps['cpuCount']} cores")
        if caps['hasGPU']:
            print(f"   GPU: Yes ({caps.get('gpuDetectionMethod', 'Unknown')})")
            print(f"   CUDA: {caps['cudaVersion']}")
            for gpu in caps['gpuInfo']:
                print(f"     {gpu['name']} ({gpu['memory']}GB, Compute: {gpu.get('computeCapability', 'Unknown')})")
        else:
            print(f"   GPU: No")
        
        # Test authentication
        print()
        print("🔐 Testing authentication...")
        try:
            token = authenticator.authenticate()
            print("   ✅ Authentication successful")
        except Exception as e:
            print(f"   ❌ Authentication failed: {e}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def cmd_info(args) -> int:
    """Show system information"""
    _, AgentCapabilities, _, _ = _import_agent_modules()
    caps = AgentCapabilities.detect()
    
    print("📊 System Information")
    print()
    print(f"  💻 Platform: {caps['platform']}")
    print(f"  🐍 Python Version: {caps['pythonVersion']}")
    print()
    print("  🧠 Memory:")
    print(f"    Total: {caps['totalMemoryGB']:.2f} GB")
    print(f"    Available: {caps['availableMemoryGB']:.2f} GB")
    print()
    print("  💽 Storage:")
    print(f"    Total: {caps['totalStorageGB']:.2f} GB")
    print(f"    Available: {caps['availableStorageGB']:.2f} GB")
    print()
    print(f"  ⚙️ CPU Cores: {caps['cpuCount']}")
    print()
    
    # Display training capability
    print("🚀 Training Core:")
    if caps.get('hasTraining'):
        status = "✓ Ready"
        try:
            import ultralytics
            engine = f"Ultralytics {ultralytics.__version__}"
        except ImportError:
            engine = "Hardware accelerated"
        print(f"  ⚡ Status: {status}")
        print(f"  🛠️ Engine: {engine}")
    else:
        print("  ⚡ Status: ✗ Not Ready")
        print("  ⚠️ Reason: GPU acceleration or training dependencies missing")
    print()
    
    # Display acceleration information
    if caps['platform'] == 'Darwin':
        # macOS: Show MPS status instead of GPU
        print("🎯 ML Acceleration (macOS):")
        if caps['hasMPS']:
            print(f"  ✨ Metal Performance Shaders (MPS): ✓ Available")
            print(f"  🔍 Detection Method: {caps.get('gpuDetectionMethod', 'Unknown')}")
            for gpu in caps['gpuInfo']:
                print(f"  📟 Device: {gpu['name']}")
            print()
            print("  💡 Use torch.device('mps') for 3-5x acceleration")
        else:
            print(f"  ✨ Metal Performance Shaders (MPS): ✗ Not available")
            print(f"  ℹ️ Note: Requires Apple Silicon (M1/M2/M3/M4) + PyTorch 1.12+")
            print(f"  ⚠️ Falling back to CPU training (slower)")
    
    elif caps['hasGPU']:
        # Linux/Windows: Show CUDA/ROCm GPU info
        if caps.get('hasROCm'):
            print("🎮 ROCm GPU Information:")
            print(f"  🔍 Detection Method: {caps.get('gpuDetectionMethod', 'Unknown')}")
            print(f"  🆔 ROCm Version: {caps['rocmVersion'] or 'Not detected'}")
        else:
            print("🎮 CUDA GPU Information:")
            print(f"  🔍 Detection Method: {caps.get('gpuDetectionMethod', 'Unknown')}")
            print(f"  🆔 CUDA Version: {caps['cudaVersion'] or 'Not detected'}")
            if caps.get('nvidiaDriverVersion'):
                print(f"  🔌 Driver Version: {caps['nvidiaDriverVersion']}")
            if caps.get('cudaRuntimeVersion'):
                print(f"  ⚙️ CUDA Runtime: {caps['cudaRuntimeVersion']}")
        
        print()
        for i, gpu in enumerate(caps['gpuInfo']):
            print(f"  📟 GPU {gpu.get('index', i)}:")
            print(f"    🏷️ Name: {gpu['name']}")
            print(f"    💾 Memory: {gpu['memory']} GB")
            if gpu.get('computeCapability'):
                label = "🏗️ GCN Arch" if caps.get('hasROCm') else "🏗️ Compute Capability"
                print(f"    {label}: {gpu['computeCapability']}")
        print()
        if not caps.get('hasROCm'):
            print(f"  ✨ MPS Available: No (NVIDIA GPU detected)")
    
    else:
        # No GPU detected
        if caps['platform'] == 'Darwin':
            print("⚠️  ML Acceleration (macOS):")
            print(f"  ✨ Metal Performance Shaders (MPS): ✗ Not available")
            print(f"  ℹ️ Note: Requires Apple Silicon + PyTorch with MPS support")
            print(f"  🚨 Current setup: Intel Mac or MPS not available")
            print()
            print("  💡 Options:")
            print("     1. Use CPU training (slower)")
            print("     2. Upgrade to Apple Silicon Mac")
            print("     3. Use external GPU (eGPU) if available")
        else:
            print("⚠️  GPU Not Detected:")
            print(f"  💻 Platform: {caps['platform']}")
            print(f"  🚨 Status: No GPU acceleration available")
            print()
            print("  💡 Troubleshooting:")
            print("     1. Check if nvidia-smi works: nvidia-smi")
            print("     2. Verify PyTorch CUDA: python -c \"import torch; print(torch.cuda.is_available())\"")
            print("     3. Check Docker: docker run --gpus all (if in Docker)")
            print("     4. Run diagnostic: python test-scripts/integration/test_docker_gpu_detection.py")
    
    return 0


def cmd_check_env(args) -> int:
    """Check environment compatibility"""
    from .environment_check import check_environment_interactive
    
    print()
    env_ok = check_environment_interactive()
    print()
    
    if env_ok:
        print("✅ Environment is ready for Aegis AI training.")
        return 0
    else:
        print("❌ Environment has issues that need to be addressed.")
        return 1


def cmd_setup(args) -> int:
    """Initialize agent training environment and dependencies"""
    from .agent import PlatformResolver
    import subprocess
    import sys
    
    print("🛠️  Aegis AI Training Environment Setup")
    print("=" * 70)
    print("This command helps you set up hardware-accelerated training core.")
    print("Aegis-agent will SUGGEST the best commands for your hardware.")
    
    # 1. Hardware Detection
    print("\n🔍 Step 1: Detecting Hardware...")
    resolver = PlatformResolver()
    hw_info = resolver.detect_hardware()
    sys_type = hw_info.get("platform", "Unknown")
    
    print(f"   • Platform: {sys_type}")
    if hw_info.get("hasGPU"):
        method = hw_info.get('gpuDetectionMethod', 'Unknown')
        print(f"   • GPU Detected: {hw_info['gpuInfo'][0]['name']} (via {method})")
    else:
        print("   • GPU: Not detected (System will use CPU fallback)")

    # 2. PyTorch Setup (Hardware Aware)
    print("\n📦 Step 2: Suggested Installation Plan")
    pytorch_plan = resolver.resolve_pytorch_install()
    
    print(f"   Reason: {pytorch_plan['reason']}")
    
    # Explicitly list the commands for manual use
    torch_cmd = pytorch_plan['install_cmd']
    plugin_cmd = f"{sys.executable} -m pip install 'aegis-vision[training]'"
    
    print("\n   --- Suggested Commands ---")
    print(f"   1. {torch_cmd}")
    print(f"   2. {plugin_cmd}")
    print("   ---------------------------")
    
    print("\n💡 You can copy-paste these commands to run them manually,")
    print("   or let me handle the execution for you.")
    
    confirm = input("\nWould you like me to execute these commands now? [y/N]: ").strip().lower()
    if confirm in ['y', 'yes']:
        print("\n🚀 Executing Step 1: PyTorch & Hardware Drivers...")
        try:
            if torch_cmd:
                subprocess.run(torch_cmd, shell=True, check=True)
            
            if plugin_cmd:
                print("\n🚀 Executing Step 2: Training Plugins...")
                subprocess.run(plugin_cmd, shell=True, check=True)
            
            print("\n✅ Setup complete! Your environment is ready.")
            return 0
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Installation failed: {e}")
            print("Please try running the suggested commands manually to see detailed errors.")
            return 1
    else:
        print("\nℹ️  Advisory mode complete. No changes were made.")
        print("You can run the suggested commands above whenever you are ready.")
        return 0


def cmd_clear_cache(args) -> int:
    """Clear Firebase configuration cache"""
    from pathlib import Path
    
    cache_path = Path.home() / '.aegis-vision' / 'cache' / 'firebase_config.json'
    
    if cache_path.exists():
        cache_path.unlink()
        print(f"✅ Cleared Firebase config cache: {cache_path}")
        return 0
    else:
        print("ℹ️  No cache found")
        return 0


def cmd_show_cache(args) -> int:
    """Show cached Firebase configuration"""
    from pathlib import Path
    import json
    
    cache_path = Path.home() / '.aegis-vision' / 'cache' / 'firebase_config.json'
    
    if not cache_path.exists():
        print("ℹ️  No cache found")
        print(f"   Expected location: {cache_path}")
        print()
        print("Cache will be created automatically when agent starts.")
        return 0
    
    try:
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
        
        print("📦 Cached Firebase Configuration:")
        print(f"   Cache file: {cache_path}")
        print(f"   Cached at: {cache_data.get('cached_at', 'unknown')}")
        print(f"   Fetched from: {cache_data.get('fetched_from', 'unknown')}")
        print(f"   Cache version: {cache_data.get('version', 'unknown')}")
        print()
        
        firebase_config = cache_data.get('firebaseConfig', {})
        print("Firebase Config:")
        print(f"   API Key: {firebase_config.get('apiKey', 'unknown')[:20]}...")
        print(f"   Project ID: {firebase_config.get('projectId', 'unknown')}")
        print(f"   Auth Domain: {firebase_config.get('authDomain', 'unknown')}")
        print()
        
        agent_info = cache_data.get('agentInfo', {})
        if agent_info:
            print("Agent Info:")
            print(f"   Agent ID: {agent_info.get('agentId', 'unknown')}")
            print(f"   Owner UID: {agent_info.get('ownerUid', 'unknown')}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to read cache: {e}")
        return 1


def _create_synthetic_dataset(output_dir: Path, num_images: int, img_size: int, classes: str):
    """Internal helper to create a synthetic YOLO dataset"""
    import numpy as np
    from PIL import Image, ImageDraw
    import random
    import yaml
    
    output_dir = output_dir.expanduser().resolve()
    class_names = [c.strip() for c in classes.split(',')]
    num_classes = len(class_names)
    
    print(f"🎨 Creating synthetic dataset in: {output_dir}")
    print(f"   • Images: {num_images}")
    print(f"   • Size: {img_size}x{img_size}")
    print(f"   • Classes: {', '.join(class_names)}")
    
    # Create directory structure
    for split in ['train', 'val']:
        (output_dir / 'images' / split).mkdir(parents=True, exist_ok=True)
        (output_dir / 'labels' / split).mkdir(parents=True, exist_ok=True)
        
    # Generate images
    for split in ['train', 'val']:
        # 80/20 split or as requested
        count = int(num_images * 0.8) if split == 'train' else max(1, int(num_images * 0.2))
        
        for i in range(count):
            # Create a random background image
            color = tuple(np.random.randint(0, 256, 3))
            img = Image.new('RGB', (img_size, img_size), color=color)
            draw = ImageDraw.Draw(img)
            
            labels = []
            # Add 1-3 random objects
            for _ in range(random.randint(1, 3)):
                cls_id = random.randint(0, num_classes - 1)
                
                # Random box (normalized)
                w = random.uniform(0.1, 0.4)
                h = random.uniform(0.1, 0.4)
                x = random.uniform(w/2, 1 - w/2)
                y = random.uniform(h/2, 1 - h/2)
                
                labels.append(f"{cls_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}")
                
                # Draw the object for visual feedback
                obj_color = tuple(np.random.randint(0, 256, 3))
                left = (x - w/2) * img_size
                top = (y - h/2) * img_size
                right = (x + w/2) * img_size
                bottom = (y + h/2) * img_size
                draw.rectangle([left, top, right, bottom], outline=obj_color, width=3)
                
                # Try to draw text if possible
                try:
                    draw.text((left, top), class_names[cls_id], fill=obj_color)
                except Exception:
                    pass
                
            # Save image
            img_path = output_dir / 'images' / split / f"test_{i}.jpg"
            img.save(img_path)
            
            # Save label
            label_path = output_dir / 'labels' / split / f"test_{i}.txt"
            with open(label_path, 'w') as f:
                f.write('\n'.join(labels))
                
    # Create dataset.yaml
    dataset_yaml = {
        'path': str(output_dir),
        'train': 'images/train',
        'val': 'images/val',
        'names': {i: name for i, name in enumerate(class_names)}
    }
    
    with open(output_dir / 'dataset.yaml', 'w') as f:
        yaml.dump(dataset_yaml, f, default_flow_style=False)
    
    return output_dir


def cmd_create_test_dataset(args):
    """Create a synthetic YOLO dataset for testing"""
    try:
        output_dir = Path(args.output_dir)
        _create_synthetic_dataset(output_dir, args.num_images, args.img_size, args.classes)
        print(f"\n✅ Synthetic dataset created successfully at: {output_dir}")
        print(f"   You can now run test training with this dataset.")
        return 0
    except Exception as e:
        print(f"❌ Failed to create test dataset: {e}")
        return 1


def cmd_test_training(args):
    """Run a full synthetic training test to verify environment"""
    import tempfile
    import shutil
    
    print("🚀 Starting synthetic training test to verify environment...")
    
    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp(prefix="aegis-test-training-"))
    try:
        # 1. Create synthetic dataset
        print("\n📦 Step 1/3: Creating small synthetic dataset...")
        _create_synthetic_dataset(temp_dir, num_images=10, img_size=640, classes="cat,dog")
        
        # 2. Check for training engine
        try:
            from .agent import AgentCapabilities
            caps = AgentCapabilities.detect()
        except ImportError:
            print("\n❌ Error: Could not import AgentCapabilities.")
            return 1
            
        if not caps.get('hasTraining'):
             print("\n❌ Error: Training core is NOT ready.")
             print("   Please run 'aegis-agent setup' first.")
             return 1
             
        # 3. Running test training
        print("\n🚀 Step 2/3: Initializing test training (1 epoch)...")
        try:
            from .trainer import YOLOTrainer
        except ImportError:
            print("\n❌ Error: Could not import YOLOTrainer. Ensure 'ultralytics' is installed.")
            return 1
        
        trainer = YOLOTrainer(
            model_variant="yolov8n", # Use lightest model for speed
            dataset_path=str(temp_dir / "dataset.yaml"),
            epochs=1,
            batch_size=2,
            img_size=640,
            output_dir=str(temp_dir / "output")
        )
        
        print("\n🔥 Step 3/3: Running training (this may take a minute)...")
        results = trainer.train()
        
        if results.get('success'):
            print("\n" + " ✨ ENVIRONMENT TEST PASSED! ✨ ".center(60, "="))
            print("✅ Synthetic dataset created and training completed successfully.")
            print(f"✅ Your environment is correctly configured for {caps.get('platform')} training.")
            return 0
        else:
            print("\n❌ Training initialization succeeded but training itself failed.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test training failed: {e}")
        return 1
    finally:
        # Clean up
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Aegis AI Training Agent - Distributed model training',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive login (recommended)
  aegis-agent login
  
  # Initialize training environment (installs hardware-aware PyTorch)
  aegis-agent setup
  
  # Or initialize with API key directly
  aegis-agent init --api-key ak_xxxxxxxxxxxxx --name "My Training Server"
  
  # Start agent daemon
  aegis-agent start
  
  # Check agent status
  aegis-agent status
  
  # Show system capabilities
  aegis-agent info
  
  # Cache management
  aegis-agent show-cache     # Show cached Firebase config
  aegis-agent clear-cache    # Clear cache (force refetch)
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # login command
    login_parser = subparsers.add_parser('login', help='Interactive login (like huggingface-cli login)')
    login_parser.add_argument('--config', help='Config file path (default: ~/.aegis-ai/agent-config.json)')
    login_parser.add_argument(
        '--cloud-function-url',
        default='https://us-central1-aegis-vision-464501.cloudfunctions.net/aegis-vision-admin-api',
        help='Cloud Function URL'
    )
    login_parser.add_argument(
        '--firestore-project',
        default='aegis-vision-464501',
        help='Firestore project ID'
    )
    
    # init command
    init_parser = subparsers.add_parser('init', help='Initialize agent configuration (non-interactive)')
    init_parser.add_argument('--api-key', required=True, help='API key from Aegis AI')
    init_parser.add_argument('--agent-id', help='Agent ID (auto-generated if not provided)')
    init_parser.add_argument('--name', help='Human-readable agent name')
    init_parser.add_argument('--config', help='Config file path (default: ~/.aegis-ai/agent-config.json)')
    init_parser.add_argument(
        '--cloud-function-url',
        default='https://us-central1-aegis-vision-464501.cloudfunctions.net/aegis-vision-admin-api',
        help='Cloud Function URL'
    )
    init_parser.add_argument(
        '--firestore-project',
        default='aegis-vision-464501',
        help='Firestore project ID'
    )
    
    # start command
    start_parser = subparsers.add_parser('start', help='Start agent daemon')
    start_parser.add_argument('--config', help='Config file path')
    start_parser.add_argument('--work-dir', help='Working directory for training')
    start_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    start_parser.add_argument(
        '--skip-env-check',
        action='store_true',
        help='Skip environment compatibility check (not recommended)'
    )
    
    # status command
    status_parser = subparsers.add_parser('status', help='Show agent status')
    status_parser.add_argument('--config', help='Config file path')
    
    # info command
    info_parser = subparsers.add_parser('info', help='Show system information')
    
    # check-env command
    check_env_parser = subparsers.add_parser(
        'check-env',
        help='Check environment compatibility and suggest fixes'
    )
    
    # setup command
    setup_parser = subparsers.add_parser(
        'setup',
        help='Interactive environment setup (installs PyTorch and training plugins)'
    )
    
    # clear-cache command
    clear_cache_parser = subparsers.add_parser(
        'clear-cache',
        help='Clear cached Firebase configuration'
    )
    
    # show-cache command
    show_cache_parser = subparsers.add_parser(
        'show-cache',
        help='Show cached Firebase configuration'
    )
    
    # create-test-dataset command
    dataset_parser = subparsers.add_parser(
        'create-test-dataset',
        help='Create a synthetic YOLO dataset for testing'
    )
    dataset_parser.add_argument(
        '--output-dir',
        default=str(Path.home() / '.aegis-vision' / 'test-dataset'),
        help='Output directory (default: ~/.aegis-vision/test-dataset)'
    )
    dataset_parser.add_argument(
        '--num-images',
        type=int,
        default=20,
        help='Number of images to generate (default: 20)'
    )
    dataset_parser.add_argument(
        '--img-size',
        type=int,
        default=640,
        help='Image size (default: 640)'
    )
    dataset_parser.add_argument(
        '--classes',
        default='cat,dog',
        help='Comma-separated class names (default: cat,dog)'
    )
    
    # test-training command
    subparsers.add_parser(
        'test-training',
        help='Run a full synthetic training test to verify environment functionality'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to command handler
    if args.command == 'login':
        return cmd_login(args)
    elif args.command == 'init':
        return cmd_init(args)
    elif args.command == 'start':
        return cmd_start(args)
    elif args.command == 'status':
        return cmd_status(args)
    elif args.command == 'info':
        return cmd_info(args)
    elif args.command == 'check-env':
        return cmd_check_env(args)
    elif args.command == 'setup':
        return cmd_setup(args)
    elif args.command == 'clear-cache':
        return cmd_clear_cache(args)
    elif args.command == 'show-cache':
        return cmd_show_cache(args)
    elif args.command == 'create-test-dataset':
        return cmd_create_test_dataset(args)
    elif args.command == 'test-training':
        return cmd_test_training(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

