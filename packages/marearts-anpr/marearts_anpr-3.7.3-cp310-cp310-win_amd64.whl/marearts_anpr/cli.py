#!/usr/bin/env python3
"""
MareArts ANPR CLI - Command Line Interface for License Plate Detection and Recognition
"""

import argparse
import json
import os
import sys
import re
import getpass
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

import cv2
import numpy as np
from . import (
    marearts_anpr_from_image_file,
    ma_anpr_detector,
    ma_anpr_detector_v14,
    ma_anpr_ocr_v14,
    validate_user_key,
    validate_user_key_with_signature
)
from ._version import __version__

# Environment variable names
ENV_USERNAME = 'MAREARTS_ANPR_USERNAME'
ENV_SERIAL_KEY = 'MAREARTS_ANPR_SERIAL_KEY'
ENV_SIGNATURE = 'MAREARTS_ANPR_SIGNATURE'

# Region mapping: user-facing names -> internal model config names
REGION_MAPPING = {
    # New canonical names (user-facing)
    'kr': 'kor',
    'eup': 'euplus',
    'na': 'na',
    'cn': 'china',
    'univ': 'univ',
    
    # Legacy support (backward compatibility, not documented)
    'kor': 'kor',
    'euplus': 'euplus',
    'china': 'china',
}

# Input validation patterns
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.@]+$')
SERIAL_KEY_PATTERN = re.compile(r'^[A-Za-z0-9\-_=+/:]+$')  # Added : for MAEV2: prefix
SIGNATURE_PATTERN = re.compile(r'^[a-f0-9]{16}$')  # 16 hex characters
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}

def load_credentials() -> Dict[str, str]:
    """Load credentials from environment variables or ~/.marearts/.marearts_env file"""
    # First check environment variables
    env_username = os.getenv(ENV_USERNAME)
    env_serial_key = os.getenv(ENV_SERIAL_KEY)
    env_signature = os.getenv(ENV_SIGNATURE)  # Optional for V2 keys

    if env_username and env_serial_key:
        credentials = {
            'user_name': env_username,
            'serial_key': env_serial_key,
            'source': 'environment'
        }
        # Add signature if present (for V2 keys)
        if env_signature:
            credentials['signature'] = env_signature
        return credentials

    # Check for ~/.marearts/.marearts_env file
    env_file = Path.home() / '.marearts' / '.marearts_env'
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                lines = f.readlines()
                username = None
                serial_key = None
                signature = None
                for line in lines:
                    if line.startswith(f'export {ENV_USERNAME}='):
                        username = line.split('=', 1)[1].strip().strip('"')
                    elif line.startswith(f'export {ENV_SERIAL_KEY}='):
                        serial_key = line.split('=', 1)[1].strip().strip('"')
                    elif line.startswith(f'export {ENV_SIGNATURE}='):
                        signature = line.split('=', 1)[1].strip().strip('"')

                if username and serial_key:
                    # Set them in environment for this session
                    os.environ[ENV_USERNAME] = username
                    os.environ[ENV_SERIAL_KEY] = serial_key
                    if signature:
                        os.environ[ENV_SIGNATURE] = signature

                    credentials = {
                        'user_name': username,
                        'serial_key': serial_key,
                        'source': '~/.marearts/.marearts_env file'
                    }
                    # Add signature if present (for V2 keys)
                    if signature:
                        credentials['signature'] = signature
                    return credentials
        except Exception:
            pass

    return {}
def mask_serial_key(serial_key: str) -> str:
    """Mask serial key for display purposes"""
    if len(serial_key) <= 8:
        return '*' * len(serial_key)
    return serial_key[:4] + '*' * (len(serial_key) - 8) + serial_key[-4:]
def cmd_gpu_info(args):
    """Display GPU/CUDA information and V14 backend support"""
    print("MareArts ANPR System Information")
    print("=" * 50)

    # Display package version
    print(f"\n📦 Package Version: {__version__}")

    # Check OpenCV build info for legacy models
    print("\n📊 Legacy Model Support (V13 and earlier):")
    print("-" * 40)
    build_info = cv2.getBuildInformation()
    cuda_enabled = "CUDA" in build_info and "YES" in build_info

    print(f"OpenCV: {cv2.__version__} | CUDA: {'✅ Yes' if cuda_enabled else '❌ No'}")
    
    if cuda_enabled:
        cuda_lines = [line for line in build_info.split('\n') if 'CUDA' in line]
        if cuda_lines:
            print(f"CUDA Details: {cuda_lines[0].strip()}")
    
    try:
        gpu_count = cv2.cuda.getCudaEnabledDeviceCount()
        if gpu_count > 0:
            print(f"GPU Devices: {gpu_count}")
    except:
        pass
    
    # Check V14 backend support
    print("\n🚀 V14 Model Backend Support:")
    print("-" * 40)
    
    backends = {
        'cpu': False,
        'cuda': False,
        'directml': False,
        'tensorrt': False
    }
    
    # Check CPU (ONNX Runtime) - always available
    try:
        import onnxruntime
        backends['cpu'] = True
        ort_version = ""
        try:
            ort_version = f" {onnxruntime.__version__}"
        except:
            # Some versions don't have __version__
            pass
        print(f"✅ CPU (ONNX Runtime{ort_version})")
    except ImportError:
        print("❌ CPU (ONNX Runtime not installed)")
    
    # Check CUDA support
    try:
        import onnxruntime
        if 'CUDAExecutionProvider' in onnxruntime.get_available_providers():
            backends['cuda'] = True
            # Try to get CUDA version
            cuda_version = ""
            try:
                import torch
                if torch.cuda.is_available():
                    cuda_version = f" (CUDA {torch.version.cuda})"
            except:
                try:
                    # Alternative: check through ctypes
                    import ctypes
                    libcudart = ctypes.CDLL('libcudart.so')
                    cuda_ver = ctypes.c_int()
                    libcudart.cudaRuntimeGetVersion(ctypes.byref(cuda_ver))
                    major = cuda_ver.value // 1000
                    minor = (cuda_ver.value % 1000) // 10
                    cuda_version = f" (CUDA {major}.{minor})"
                except:
                    pass
            print(f"✅ CUDA{cuda_version} (GPU acceleration available)")
        else:
            print("❌ CUDA (Not available)")
    except:
        print("❌ CUDA (Cannot check)")
    
    # Check DirectML support (Windows)
    try:
        import platform
        if platform.system() == 'Windows':
            import onnxruntime
            if 'DmlExecutionProvider' in onnxruntime.get_available_providers():
                backends['directml'] = True
                print("✅ DirectML (Windows GPU acceleration)")
            else:
                print("❌ DirectML (Not available on Windows)")
        else:
            print("⚠️  DirectML (Windows only)")
    except:
        print("❌ DirectML (Cannot check)")
    
    # Check TensorRT support
    try:
        import onnxruntime
        if 'TensorrtExecutionProvider' in onnxruntime.get_available_providers():
            backends['tensorrt'] = True
            # Try to get TensorRT version
            try:
                import sys
                # Force import from current Python environment
                import tensorrt
                trt_version = tensorrt.__version__
                # Also show which TensorRT library is being used
                trt_location = tensorrt.__file__ if hasattr(tensorrt, '__file__') else 'unknown'
                print(f"✅ TensorRT {trt_version} (NVIDIA optimization)")
                # Debug info (can be removed later)
                # print(f"   Debug: TensorRT from {trt_location}")
            except Exception as e:
                print("✅ TensorRT (NVIDIA optimization)")
                # print(f"   Debug: Could not get version: {e}")
        else:
            print("❌ TensorRT (Not available)")
            # Try to check if TensorRT is installed but not in ONNX Runtime
            try:
                import tensorrt
                print(f"   ⚠️  TensorRT {tensorrt.__version__} installed but not in ONNX Runtime")
                print(f"   💡 Install: pip install onnxruntime-gpu")
            except:
                pass
    except:
        print("❌ TensorRT (Cannot check)")
    
    # Summary
    print("\n📋 Summary:")
    print("-" * 40)
    
    # Check license type to determine available models
    config = load_credentials()
    if config and config.get('serial_key'):
        if config.get('serial_key', '').startswith('MAEV2:'):
            print("License: V2 (Full access)")
            print("Available models: V13 (legacy) + V14 (all backends)")

            available_backends = [k for k, v in backends.items() if v]
            if available_backends:
                print(f"V14 backends ready: {', '.join(available_backends)}")
            else:
                print("⚠️  No V14 backends available - install onnxruntime")
        else:
            print("License: V1 (Legacy only)")
            print("Available models: V13 and earlier")
    else:
        print("License: No credentials found")
        print("Available models: Limited functionality")
        if cuda_enabled:
            print("GPU acceleration: Available for legacy models")
    
    print("\n💡 Tips:")
    if not backends['cpu']:
        print("• Install onnxruntime: pip install onnxruntime")
    if not backends['cuda'] and cuda_enabled:
        print("• For GPU: pip install onnxruntime-gpu")
    if platform.system() == 'Windows' and not backends['directml']:
        print("• For DirectML: pip install onnxruntime-directml")
def cmd_models(args):
    """List available V14 models"""

    # Check license type
    config = load_credentials()
    is_v2 = config and config.get('serial_key', '').startswith('MAEV2:')
    has_signature = config and config.get('signature')

    print("\nMareArts ANPR V14 Models")
    print("=" * 50)

    if not is_v2 or not has_signature:
        print("❌ V14 models require V2 license with signature")
        print("\n💡 To upgrade:")
        print("   1. Contact support for V2 license")
        print("   2. Run: ma-anpr config")
        print("   3. Enter your V2 credentials with signature")
        return

    print("License: V2 (Full Access)\n")

    print("🚀 V14 DETECTOR MODELS")
    print("-" * 50)
    print("Backends: CPU, CUDA, DirectML\n")

    v14_detector = [
        "pico_640p_fp32",
        "pico_640p_fp16",
        "micro_640p_fp32",
        "micro_640p_fp16",
        "small_640p_fp32",
        "small_640p_fp16",
        "medium_640p_fp32",
        "medium_640p_fp16",
        "large_640p_fp32",
        "large_640p_fp16",
    ]
    for model in v14_detector:
        print(f"    • {model}")

    print("\n\n🔤 V14 OCR MODELS")
    print("-" * 50)
    print("Regional Models (Single universal model + runtime filtering)\n")

    print("  Model Sizes:")
    v14_ocr = [
        "pico_fp32",
        "micro_fp32",
        "small_fp32",
        "medium_fp32",
        "large_fp32",
    ]
    for model in v14_ocr:
        print(f"    • {model}")

    print("\n  Supported Regions:")
    regions = ["kr", "eup", "na", "cn", "univ"]
    for region in regions:
        print(f"    • {region}")

    print("\n💡 Usage Examples:")
    print("   ma-anpr read image.jpg")
    print("   ma-anpr read image.jpg --detector v14_medium_640p_fp32")
    print("   ma-anpr read image.jpg --ocr small_fp32 --region univ")
def cmd_validate(args):
    """Validate license and show details"""
    config = load_credentials()
    if not config:
        print("No credentials. Run: ma-anpr config")
        sys.exit(1)
    
    user_name = config.get('user_name')
    serial_key = config.get('serial_key')
    signature = config.get('signature')
    source = config.get('source', 'environment')
    
    print("\nMareArts ANPR License Validation")
    print("=" * 50)
    print(f"User: {user_name}")
    print(f"Key: {mask_serial_key(serial_key)}")
    print(f"Source: {source}")
    
    # Determine license type
    is_v2 = serial_key.startswith("MAEV2:")
    
    if is_v2:
        print(f"Type: V2 License")
        if signature:
            print(f"Signature: {signature[:4]}...{signature[-4:]}")
        else:
            print("⚠️  Warning: V2 key without signature")
    else:
        print(f"Type: V1 License")
    
    print("\nValidating...", end=' ')
    
    # Validate based on key type
    if is_v2 and signature:
        # V2 with signature
        is_valid = validate_user_key_with_signature(user_name, serial_key, signature)
    else:
        # V1 or V2 without signature (backward compatibility)
        is_valid = validate_user_key(user_name, serial_key)
    
    if is_valid:
        print("✅ Valid")

        if is_v2:
            print("✅ V2 License - Full access including V14 models")
            if not signature:
                print("\n⚠️  Note: Add signature for V14 model access")
                print(f"   Set: {ENV_SIGNATURE} environment variable")
        else:
            print("✅ V1 License - Legacy models (V10, V11, V13)")
            print("\n💡 Upgrade to V2 license for V14 models")

        print("✅ Ready to use: ma-anpr image.jpg")
    else:
        print("❌ Invalid")
        print("\n⚠️  Troubleshooting:")
        if is_v2 and not signature:
            print(f"• V2 key requires signature")
            print(f"• Set: {ENV_SIGNATURE} environment variable")
        print(f"• Check credentials in {source}")
        print(f"• Ensure correct username/email")
        print(f"• Contact support if issue persists")
def validate_file_path(path: str) -> Optional[Path]:
    """Validate and sanitize file paths"""
    try:
        # Resolve to absolute path
        abs_path = Path(path).resolve()
        
        # Check if path exists
        if not abs_path.exists():
            return None
        
        # For files, check extension
        if abs_path.is_file():
            if abs_path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
                return None
        
        return abs_path
    except Exception:
        return None
def draw_results(image: np.ndarray, results: List[Dict[str, Any]]) -> np.ndarray:
    """Draw detection results on image"""
    output = image.copy()
    
    for result in results:
        bbox = result['bbox']
        x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
        
        # Draw bounding box
        cv2.rectangle(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Prepare label
        ocr_text = result.get('ocr_text', 'N/A')
        ocr_conf = result.get('ocr_conf', 0.0)
        label = f"{ocr_text} ({ocr_conf:.2f})"
        
        # Draw label background
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        label_y = y1 - 10 if y1 - 10 > label_size[1] else y1 + label_size[1] + 10
        cv2.rectangle(output, 
                     (x1, label_y - label_size[1] - 5),
                     (x1 + label_size[0], label_y + 5),
                     (0, 255, 0), -1)
        
        # Draw label text
        cv2.putText(output, label,
                   (x1, label_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    
    return output
def process_image(image_path: str, args) -> List[Dict[str, Any]]:
    """Process single image with V14 models only"""
    config = load_credentials()
    if not config:
        raise ValueError("No configuration found. Run 'marearts-anpr config' first.")
    
    user_name = config.get('user_name')
    serial_key = config.get('serial_key')
    signature = config.get('signature')
    
    if not user_name or not serial_key:
        raise ValueError("Invalid credentials found. Please reconfigure.")
    
    try:
        # Get model versions from args with available fallbacks
        detector_model = getattr(args, 'detector_model', 'medium_640p_fp32')  # Default to V14
        ocr_model = getattr(args, 'ocr_model', 'small_fp32')  # Default to V14 OCR
        region = getattr(args, 'region', 'kr')  # Default region for V14 OCR
        backend = getattr(args, 'backend', 'cpu')  # Backend for V14 models

        # Map user-facing region name to internal model config name
        internal_region = REGION_MAPPING.get(region, region)

        # CLI only supports V14 models (both detector and OCR)
        # V14 models require V2 key with signature
        if not serial_key.startswith('MAEV2:'):
            raise ValueError("CLI requires V2 license key (MAEV2:). Run 'ma-anpr config' to update.")
        if not signature:
            raise ValueError("CLI requires signature. Run 'ma-anpr config' to add signature.")

        # Create V14 detector with backend support
        detector = ma_anpr_detector_v14(
            detector_model,
            user_name,
            serial_key,
            signature,
            backend=backend
        )

        # Create V14 OCR object with backend parameter (use mapped internal region)
        ocr = ma_anpr_ocr_v14(ocr_model, internal_region, user_name, serial_key, signature, backend=backend)
        
        # Use the correct API with initialized objects
        api_result = marearts_anpr_from_image_file(detector, ocr, image_path)
        
        # Convert API format to expected CLI format
        if api_result and 'results' in api_result:
            results = []
            for result in api_result['results']:
                # Convert to expected format
                plate_result = {
                    'ocr_text': result.get('ocr', ''),
                    'ocr_conf': result.get('ocr_conf', 0) / 100.0 if result.get('ocr_conf', 0) > 1 else result.get('ocr_conf', 0),  # Convert percentage to decimal
                    'bbox': result.get('ltrb', []),
                    'bbox_conf': result.get('ltrb_conf', 0) / 100.0 if result.get('ltrb_conf', 0) > 1 else result.get('ltrb_conf', 0)
                }
                results.append(plate_result)
            return results
        else:
            return []
        
    except Exception as e:
        # Check for specific V14 errors
        error_msg = str(e)
        if "V14 models require" in error_msg:
            raise ValueError(error_msg)
        # Check for download/model availability errors
        if "Download failed" in error_msg or "dadmv14" in error_msg or "daomv14" in error_msg:
            raise ValueError("Model download failed.")
        # Generic error message to avoid credential leakage
        raise ValueError("Failed to process image. Please check your configuration and license.")
    finally:
        # Clear sensitive variables from memory
        user_name = None
        serial_key = None
        signature = None
def cmd_read(args):
    """Read license plates from images"""
    # Check configuration
    config = load_credentials()
    if not config:
        print("No configuration. Run: ma-anpr config")
        sys.exit(1)
    
    # Get list of input files with validation
    input_files = []
    for input_path in args.input:
        path = validate_file_path(input_path)
        if path is None:
            print(f"Skip: {input_path}")
            continue
            
        if path.is_file():
            input_files.append(path)
        elif path.is_dir():
            # Find all image files in directory
            for ext in ALLOWED_IMAGE_EXTENSIONS:
                input_files.extend(path.glob(f'*{ext}'))
                input_files.extend(path.glob(f'*{ext.upper()}'))
    
    if not input_files:
        print("No valid files")
        sys.exit(1)
    
    # Display processing info with backend for V14
    if args.detector_model.startswith('v14_'):
        print(f"Processing {len(input_files)} images | {args.detector_model} ({args.backend})/{args.ocr_model} | Conf: {args.confidence}")
    else:
        print(f"Processing {len(input_files)} images | {args.detector_model}/{args.ocr_model} | Conf: {args.confidence}")
    
    all_results = []
    
    for img_path in input_files:
        try:
            print(f"{img_path.name}:", end=' ')
            
            # Process image
            results = process_image(str(img_path), args)
            
            # Filter by confidence
            filtered_results = [r for r in results if r.get('ocr_conf', 0) >= args.confidence]
            
            # Store results with filename
            for result in filtered_results:
                result['filename'] = str(img_path)
            
            all_results.extend(filtered_results)
            
            # Display results
            if filtered_results:
                plates = ', '.join([f"{r.get('ocr_text', 'N/A')} ({r.get('ocr_conf', 0):.2f})" for r in filtered_results])
                print(f"{len(filtered_results)} plates: {plates}")
            else:
                print("No plates")
            
            # Save annotated image if requested
            if args.output:
                image = cv2.imread(str(img_path))
                annotated = draw_results(image, filtered_results)
                
                if len(input_files) == 1:
                    output_path = args.output
                else:
                    # Multiple files - create unique output names
                    output_path = Path(args.output)
                    if output_path.is_dir():
                        output_path = output_path / f"detected_{img_path.name}"
                    else:
                        output_path = output_path.parent / f"detected_{img_path.stem}{output_path.suffix}"
                
                cv2.imwrite(str(output_path), annotated)
                print(f"  → Saved: {output_path.name}")
                
        except Exception as e:
            print(f"Error: {str(e)}")
            continue
    
    # Save results to JSON if requested
    if args.json:
        try:
            json_path = Path(args.json).resolve()
            with open(json_path, 'w') as f:
                json.dump(all_results, f, indent=2)
            print(f"\nResults saved to: {json_path}")
        except Exception:
            print("\nError: Failed to save JSON results")
    
    print(f"\nTotal: {len(all_results)} plates from {len(input_files)} images")
def cmd_test_api(args):
    """Test API functionality using public credentials"""
    # Public test credentials
    PUBLIC_API_KEY = "J4K9L2Wory34@G7T1Y8rt-PP83uSSvkV3Z6ioSTR!"
    PUBLIC_USER_ID = "marearts@public"
    API_URL = "https://we303v9ck8.execute-api.eu-west-1.amazonaws.com/Prod/marearts_anpr"
    
    # List models option
    if hasattr(args, 'list_models') and args.list_models:
        print("Available Test API Models (Public Cloud Service):")
        print("=" * 50)
        
        print("\n📍 DETECTOR MODELS (Legacy only - no V14 on public API):")
        print("-" * 40)
        print("  v10 Series:")
        print("    - v10_nano, v10_small, v10_middle, v10_large, v10_xlarge")
        print("  v11 Series:")
        print("    - v11_nano, v11_small, v11_middle, v11_large")
        print("  v13 Series (Recommended):")
        print("    - v13_nano, v13_small, v13_middle, v13_large")
        
        print("\n🔤 OCR MODELS:")
        print("-" * 40)
        print("  Base Models:")
        print("    - eu, euplus, kr, cn, univ")
        print("  v11 Series:")
        print("    - v11_eu, v11_euplus, v11_kr, v11_cn, v11_univ")
        print("  v13 Series (Recommended):")
        print("    - v13_eu, v13_euplus, v13_kr, v13_cn, v13_univ")
        
        print("\n📝 NOTES:")
        print("-" * 40)
        print("• Daily limit: 1000 requests")
        print("• No authentication required")
        print("• V14 models NOT available on public API")
        print("• For V14 models, use local processing with V2 license")
        print("\n💡 Recommended: v13_middle + v13_euplus")
        return
    
    # Check if input files are provided
    if not args.input:
        print("Error: No input files specified.")
        print("Usage: ma-anpr test-api image.jpg [--detector MODEL] [--ocr MODEL]")
        print("       ma-anpr test-api --list-models")
        return
    
    # Collect all results for JSON output
    all_json_results = []
    
    # Process images
    for input_file in args.input:
        file_path = validate_file_path(input_file)
        if file_path is None or not file_path.is_file():
            print(f"Error: {input_file} is not a valid image file")
            continue
        
        print(f"{file_path.name}:", end=' ')
        
        try:
            # Read image file with size validation
            file_size = file_path.stat().st_size
            if file_size > 5 * 1024 * 1024:  # 5MB limit
                print(f"Error: File {file_path.name} is too large ({file_size/1024/1024:.1f}MB). Maximum size is 5MB.")
                continue
                
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            # Prepare headers
            headers = {
                'Content-Type': 'image/jpeg',
                'x-api-key': PUBLIC_API_KEY,
                'user-id': PUBLIC_USER_ID,
                'detector_model_version': args.detector,
                'ocr_model_version': args.ocr
            }
            
            # Make API request with security settings
            response = requests.post(
                API_URL,
                headers=headers,
                data=image_data,
                timeout=60,  # Increased timeout to 1 minute for large images or cold starts
                verify=True,  # Always verify SSL certificates
                allow_redirects=False  # Don't follow redirects for security
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Format output similar to local processing
                if 'results' in result:
                    for plate in result['results']:
                        ocr_text = plate.get('ocr', 'N/A')
                        ocr_conf = plate.get('ocr_conf', 0)
                        ltrb = plate.get('ltrb', [])
                        ltrb_conf = plate.get('ltrb_conf', 0)
                        
                        print(f"{ocr_text} ({ocr_conf}%)", end=' ')
                
                if not result.get('results'):
                    print("")
                # Show processing times if available
                if 'ltrb_proc_sec' in result and 'ocr_proc_sec' in result:
                    total_time = result['ltrb_proc_sec'] + result['ocr_proc_sec']
                    print(f"[{total_time:.2f}s]")
                
                # Show usage information if available
                if 'usage' in result and 'day_max' in result:
                    usage = int(result['usage']) + 1
                    day_max = int(result['day_max'])
                    print(f"  API: {usage}/{day_max}")
                    
                # Collect results for JSON output
                if args.json:
                    all_json_results.append({
                        'file': str(file_path),
                        'detector_model': args.detector,
                        'ocr_model': args.ocr,
                        'result': result
                    })
                    
            else:
                print(f"Error: {response.status_code}")
                
                if response.status_code == 403 and "Usage limit exceeded" in response.text:
                    print(" (Daily limit reached)")
                
                # Try to show usage info even for error responses (if available)
                try:
                    error_result = response.json()
                    if isinstance(error_result, dict) and 'usage' in error_result and 'day_max' in error_result:
                        usage = int(error_result['usage'])
                        day_max = int(error_result['day_max'])
                        remaining = day_max - usage
                        print(f"\nAPI Usage: {usage}/{day_max} requests today ({remaining} remaining)")
                except:
                    # If we can't parse JSON or extract usage info, just continue
                    pass
                
        except requests.exceptions.Timeout:
            print("Error: Request timed out")
        except requests.exceptions.ConnectionError:
            print("Error: Failed to connect to API")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    # Save all results to JSON if requested
    if args.json and all_json_results:
        json_path = Path(args.json).resolve()
        with open(json_path, 'w') as f:
            json.dump(all_json_results, f, indent=2)
        print(f"\nResults saved to: {json_path}")

def cmd_version(args):
    """Show version information"""
    print(f"MareArts ANPR CLI v{__version__}")
def cmd_config(args):
    """Interactive credential configuration"""
    print("🔧 Configure MareArts ANPR")
    
    # Get username with validation
    while True:
        username = input("Enter your MareArts username/email: ").strip()
        if not username:
            print("❌ Empty username")
            continue
        
        if not USERNAME_PATTERN.match(username):
            print("❌ Invalid format")
            continue
            
        break
    
    # Get serial key securely with validation
    while True:
        serial_key = getpass.getpass("Enter your serial key: ").strip()
        if not serial_key:
            print("❌ Empty key")
            continue
            
        if not SERIAL_KEY_PATTERN.match(serial_key):
            print("❌ Invalid format")
            continue
            
        break
    
    # Check if V2 key and ask for signature
    signature = None
    if serial_key.startswith("MAEV2:"):
        print("📝 V2 key detected - signature required")
        while True:
            signature = input("Enter your signature (16 hex characters): ").strip()
            if not signature:
                print("❌ Empty signature")
                continue
                
            if not SIGNATURE_PATTERN.match(signature):
                print("❌ Invalid signature format (must be 16 hex characters)")
                continue
                
            break
    
    # Set the credentials in the current process environment
    os.environ[ENV_USERNAME] = username
    os.environ[ENV_SERIAL_KEY] = serial_key
    if signature:
        os.environ[ENV_SIGNATURE] = signature

    # Save to ~/.marearts/.marearts_env for persistence
    marearts_dir = Path.home() / '.marearts'
    marearts_dir.mkdir(exist_ok=True)
    env_file = marearts_dir / '.marearts_env'

    try:
        with open(env_file, 'w') as f:
            f.write(f'# MareArts ANPR Credentials\n')
            f.write(f'# Source this file: source ~/.marearts/.marearts_env\n')
            f.write(f'export {ENV_USERNAME}="{username}"\n')
            f.write(f'export {ENV_SERIAL_KEY}="{serial_key}"\n')
            if signature:
                f.write(f'export {ENV_SIGNATURE}="{signature}"\n')
        os.chmod(env_file, 0o600)  # Secure permissions

        print(f"✅ Saved to ~/.marearts/.marearts_env")
        print("Run: source ~/.marearts/.marearts_env")
    except Exception as e:
        print("✅ Session configured")
        if signature:
            print(f"Export: {ENV_USERNAME}, {ENV_SERIAL_KEY}, and {ENV_SIGNATURE}")
        else:
            print(f"Export: {ENV_USERNAME} and {ENV_SERIAL_KEY}")
    
    print("Testing...", end=' ')
    
    # Test the credentials based on key type
    if signature:
        # V2 key validation with signature
        is_valid = validate_user_key_with_signature(username, serial_key, signature)
    else:
        # V1 key validation
        is_valid = validate_user_key(username, serial_key)
    
    if is_valid:
        print("✅ Valid")
        if signature:
            print("✅ V2 License - Full access including V14 models")
        else:
            print("✅ V1 License - Access to V13 and legacy models")
        print("Ready to use: ma-anpr image.jpg")
    else:
        print("❌ Invalid")
        return 1
    
    return 0
def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog='marearts-anpr',
        description='MareArts ANPR CLI - License Plate Detection and Recognition'
    )
    
    # Add --version flag support
    parser.add_argument('--version', action='version', version=f'MareArts ANPR CLI v{__version__}')
    
    # Add direct file support - if first arg looks like a file, treat as read command
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-') and sys.argv[1] not in ['config', 'gpu-info', 'models', 'validate', 'read', 'version']:
        # Check if it could be a file path, glob pattern, or directory
        potential_file = sys.argv[1]
        # Accept any path-like argument (files, directories, glob patterns)
        if '.' in potential_file or '/' in potential_file or '\\' in potential_file or '*' in potential_file or Path(potential_file).exists():
            # Insert 'read' command
            sys.argv.insert(1, 'read')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Interactive credential configuration')
    
    # GPU info command
    gpu_parser = subparsers.add_parser('gpu-info', help='Display GPU/CUDA information')
    
    # Models command
    models_parser = subparsers.add_parser('models', help='List available models')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate license')
    
    # Version command
    version_parser = subparsers.add_parser('version', help='Show version information')
    
    # Test API command
    test_api_parser = subparsers.add_parser('test-api', help='Test ANPR using public API (no credentials required)')
    test_api_parser.add_argument('input', nargs='*', help='Input image file(s)')
    test_api_parser.add_argument('--detector', default='v13_middle',
                                 help='Detector model (default: v13_middle)')
    test_api_parser.add_argument('--ocr', default='v13_euplus',
                                 help='OCR model (default: v13_euplus)')
    test_api_parser.add_argument('--list-models', action='store_true',
                                 help='List available models for test API')
    test_api_parser.add_argument('--json', help='Save results to JSON file')
    
    # Read command
    read_parser = subparsers.add_parser('read', help='Read license plates from images')
    read_parser.add_argument('input', nargs='+', help='Input image file(s) or directory')
    read_parser.add_argument('--detector-model', default='medium_640p_fp32',
                              choices=['pico_640p_fp32', 'pico_640p_fp16',
                                       'micro_640p_fp32', 'micro_640p_fp16',
                                       'small_640p_fp32', 'small_640p_fp16',
                                       'medium_640p_fp32', 'medium_640p_fp16',
                                       'large_640p_fp32', 'large_640p_fp16'],
                              help='Detector model (default: medium_640p_fp32)')
    read_parser.add_argument('--ocr-model', default='small_fp32',
                              choices=['pico_fp32', 'micro_fp32', 'small_fp32', 'medium_fp32', 'large_fp32'],
                              help='OCR model (default: small_fp32)')
    read_parser.add_argument('--region', default='kr',
                              choices=['kr', 'eup', 'na', 'cn', 'univ'],
                              help='Region for V14 OCR (default: kr)')
    read_parser.add_argument('--backend', default='cpu',
                              choices=['cpu', 'cuda', 'directml'],
                              help='Backend for V14 models (default: cpu)')
    read_parser.add_argument('--confidence', type=float, default=0.5,
                              help='Minimum confidence threshold (default: 0.5)')
    read_parser.add_argument('--output', help='Output path for annotated image(s)')
    read_parser.add_argument('--json', help='Save results to JSON file')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    try:
        if args.command == 'config':
            cmd_config(args)
        elif args.command == 'gpu-info':
            cmd_gpu_info(args)
        elif args.command == 'models':
            cmd_models(args)
        elif args.command == 'validate':
            cmd_validate(args)
        elif args.command == 'version':
            cmd_version(args)
        elif args.command == 'test-api':
            cmd_test_api(args)
        elif args.command == 'read':
            # Set defaults for direct invocation if not set
            if not hasattr(args, 'detector_model'):
                args.detector_model = 'v13_middle'
            if not hasattr(args, 'ocr_model'):
                args.ocr_model = 'v13_euplus'
            if not hasattr(args, 'confidence'):
                args.confidence = 0.5
            if not hasattr(args, 'output'):
                args.output = None
            if not hasattr(args, 'json'):
                args.json = None
            if not hasattr(args, 'backend'):
                args.backend = 'cpu'
            cmd_read(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()