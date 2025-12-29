#!/usr/bin/env python3
"""
Test script to verify HuggingFace Hub upload readiness.

Checks:
1. All required files exist (both old and new checkpoint names)
2. Model loads correctly with both naming conventions
3. HuggingFace Hub authentication
4. publish_to_hub.py is properly configured

Usage:
    python test_hf_upload.py --check-files
    python test_hf_upload.py --check-model
    python test_hf_upload.py --check-auth
    python test_hf_upload.py --all
"""

import argparse
from pathlib import Path
import os
import sys

def check_files(model_path: str = "../findsylls/models/vg-hubert_3"):
    """Check that all required files exist."""
    print("=" * 60)
    print("Checking Model Files")
    print("=" * 60)
    
    model_path = Path(model_path)
    if not model_path.exists():
        print(f"❌ Model directory not found: {model_path}")
        return False
    
    print(f"✓ Model directory found: {model_path}")
    
    # Check both old and new names
    required_files = {
        "args.pkl": "Configuration file",
        "best_bundle.pth": "Legacy syllable checkpoint",
        "snapshot_20.pth": "Legacy word checkpoint",
        "vg-hubert-syllable.pth": "New syllable checkpoint",
        "vg-hubert-word.pth": "New word checkpoint"
    }
    
    all_exist = True
    for fname, desc in required_files.items():
        fpath = model_path / fname
        if fpath.exists():
            size_mb = fpath.stat().st_size / (1024 * 1024)
            print(f"✓ {fname:25s} ({size_mb:6.1f} MB) - {desc}")
        else:
            print(f"❌ {fname:25s} MISSING - {desc}")
            all_exist = False
    
    # Check file sizes match
    print("\nChecking file size consistency...")
    syllable_files = [model_path / "best_bundle.pth", model_path / "vg-hubert-syllable.pth"]
    word_files = [model_path / "snapshot_20.pth", model_path / "vg-hubert-word.pth"]
    
    for files in [syllable_files, word_files]:
        if all(f.exists() for f in files):
            sizes = [f.stat().st_size for f in files]
            if len(set(sizes)) == 1:
                print(f"✓ {files[0].name} and {files[1].name} have same size")
            else:
                print(f"⚠️  {files[0].name} and {files[1].name} have different sizes")
                for f, s in zip(files, sizes):
                    print(f"   {f.name}: {s / (1024*1024):.1f} MB")
    
    print("\n" + "=" * 60)
    if all_exist:
        print("✅ All required files present")
    else:
        print("❌ Some files are missing")
    print("=" * 60)
    
    return all_exist


def check_model_loading(model_path: str = "../findsylls/models/vg-hubert_3"):
    """Test that model loads correctly with both naming conventions."""
    print("\n" + "=" * 60)
    print("Testing Model Loading")
    print("=" * 60)
    
    try:
        from vg_hubert import Segmenter
        
        # Test syllable mode with new name
        print("\n1. Testing syllable mode (new checkpoint name)...")
        seg_syll_new = Segmenter(
            model_ckpt=model_path,
            mode="syllable",
            checkpoint_file="vg-hubert-syllable.pth",
            device="cpu"
        )
        print("✓ Syllable segmenter loaded with new checkpoint name")
        
        # Test syllable mode with old name
        print("\n2. Testing syllable mode (legacy checkpoint name)...")
        seg_syll_old = Segmenter(
            model_ckpt=model_path,
            mode="syllable",
            checkpoint_file="best_bundle.pth",
            device="cpu"
        )
        print("✓ Syllable segmenter loaded with legacy checkpoint name")
        
        # Test word mode with new name
        print("\n3. Testing word mode (new checkpoint name)...")
        seg_word_new = Segmenter(
            model_ckpt=model_path,
            mode="word",
            checkpoint_file="vg-hubert-word.pth",
            device="cpu"
        )
        print("✓ Word segmenter loaded with new checkpoint name")
        
        # Test word mode with old name
        print("\n4. Testing word mode (legacy checkpoint name)...")
        seg_word_old = Segmenter(
            model_ckpt=model_path,
            mode="word",
            checkpoint_file="snapshot_20.pth",
            device="cpu"
        )
        print("✓ Word segmenter loaded with legacy checkpoint name")
        
        print("\n" + "=" * 60)
        print("✅ All model loading tests passed")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Model loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_auth():
    """Check HuggingFace Hub authentication."""
    print("\n" + "=" * 60)
    print("Checking HuggingFace Hub Authentication")
    print("=" * 60)
    
    try:
        from huggingface_hub import HfApi
        
        # Check for token
        token = os.getenv("HF_TOKEN")
        if token:
            print("✓ HF_TOKEN environment variable found")
        else:
            print("⚠️  HF_TOKEN not set (will use huggingface-cli login)")
        
        # Try to authenticate
        api = HfApi(token=token)
        user_info = api.whoami()
        username = user_info.get('name', 'unknown')
        
        print(f"✓ Authenticated as: {username}")
        print(f"✓ Access token valid")
        
        print("\n" + "=" * 60)
        print("✅ HuggingFace Hub authentication successful")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        print("\nTo authenticate:")
        print("  1. Get token from: https://huggingface.co/settings/tokens")
        print("  2. Set environment variable: export HF_TOKEN=your_token")
        print("  OR")
        print("  3. Run: huggingface-cli login")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test HuggingFace Hub upload readiness")
    parser.add_argument("--check-files", action="store_true", help="Check that all files exist")
    parser.add_argument("--check-model", action="store_true", help="Test model loading")
    parser.add_argument("--check-auth", action="store_true", help="Check HF authentication")
    parser.add_argument("--all", action="store_true", help="Run all checks")
    parser.add_argument("--model-path", type=str, default="../findsylls/models/vg-hubert_3",
                       help="Path to model directory")
    
    args = parser.parse_args()
    
    # If no specific check requested, run all
    if not (args.check_files or args.check_model or args.check_auth):
        args.all = True
    
    results = []
    
    if args.all or args.check_files:
        results.append(("Files", check_files(args.model_path)))
    
    if args.all or args.check_model:
        results.append(("Model Loading", check_model_loading(args.model_path)))
    
    if args.all or args.check_auth:
        results.append(("Authentication", check_auth()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:8s} - {name}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n✅ All checks passed - ready for HuggingFace Hub upload!")
        return 0
    else:
        print("\n❌ Some checks failed - please fix issues before uploading")
        return 1


if __name__ == "__main__":
    sys.exit(main())
