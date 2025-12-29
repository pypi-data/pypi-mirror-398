"""
Simple validation test for new implementation only.

Since the original implementation has fairseq compatibility issues,
we validate the new implementation produces:
1. Reasonable output shapes
2. Consistent results across runs
3. Valid segmentation outputs
"""

import torch
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_model_consistency():
    """Test that model produces consistent outputs."""
    print("=" * 80)
    print("TEST 1: Model Output Consistency")
    print("=" * 80)
    
    from transformers import HubertModel
    
    model_path = Path("../findsylls/models/vg-hubert_3")
    if not model_path.exists():
        print("❌ Model not found at ../findsylls/models/vg-hubert_3")
        return False
    
    # Load model
    print("\nLoading model...")
    model = HubertModel.from_pretrained(
        "facebook/hubert-base-ls960",
        attn_implementation='sdpa'
    )
    
    # Try new name first, fallback to legacy
    ckpt_path = model_path / "vg-hubert-syllable.pth"
    if not ckpt_path.exists():
        ckpt_path = model_path / "best_bundle.pth"
    
    checkpoint = torch.load(ckpt_path, map_location='cpu')
    if "dual_encoder" in checkpoint:
        state_dict = checkpoint['dual_encoder']
    else:
        state_dict = checkpoint
    
    result = model.load_state_dict(state_dict, strict=False)
    print(f"Missing keys: {len(result.missing_keys)}")
    print(f"Unexpected keys: {len(result.unexpected_keys)}")
    
    model.eval()
    
    # Test consistency across multiple runs
    print("\nTesting consistency across 3 runs...")
    audio = torch.randn(1, 16000)
    
    outputs = []
    with torch.no_grad():
        for i in range(3):
            out = model(audio, output_hidden_states=True)
            # Get layer 8 features
            features = out.hidden_states[8]
            outputs.append(features)
    
    # Compare outputs
    diff_12 = (outputs[0] - outputs[1]).abs().max().item()
    diff_23 = (outputs[1] - outputs[2]).abs().max().item()
    
    print(f"   Run 1 vs Run 2 diff: {diff_12:.2e}")
    print(f"   Run 2 vs Run 3 diff: {diff_23:.2e}")
    
    if diff_12 < 1e-6 and diff_23 < 1e-6:
        print("✅ PASS: Model outputs are consistent")
        return True
    else:
        print("❌ FAIL: Model outputs vary across runs")
        return False


def test_segmenter_interface():
    """Test the Segmenter interface works correctly."""
    print("\n" + "=" * 80)
    print("TEST 2: Segmenter Interface")
    print("=" * 80)
    
    from vg_hubert import Segmenter
    
    # Create synthetic audio (1 second of sine wave)
    sr = 16000
    t = np.linspace(0, 1, sr)
    audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)  # 440 Hz tone
    
    print("\nTesting syllable mode...")
    try:
        segmenter = Segmenter(mode="syllable", device="cpu")
        outputs = segmenter(wav=audio)
        
        print(f"   Segments: {len(outputs['segments'])}")
        print(f"   Features shape: {outputs['segment_features'].shape}")
        print(f"   Hidden states shape: {outputs['hidden_states'].shape}")
        
        # Validate output structure
        assert 'segments' in outputs
        assert 'segment_features' in outputs
        assert 'hidden_states' in outputs
        assert len(outputs['segments']) > 0
        assert outputs['segment_features'].shape[0] == len(outputs['segments'])
        
        print("✅ PASS: Syllable segmentation works")
        syllable_ok = True
    except Exception as e:
        print(f"❌ FAIL: Syllable segmentation failed: {e}")
        syllable_ok = False
    
    print("\nTesting word mode...")
    try:
        segmenter = Segmenter(mode="word", device="cpu")
        outputs = segmenter(wav=audio)
        
        print(f"   Word segments: {len(outputs['segments'])}")
        if 'cls_attention' in outputs:
            print(f"   CLS attention shape: {outputs['cls_attention'].shape}")
        
        # Validate output structure
        assert 'segments' in outputs
        assert 'segment_features' in outputs
        
        print("✅ PASS: Word segmentation works")
        word_ok = True
    except Exception as e:
        print(f"❌ FAIL: Word segmentation failed: {e}")
        import traceback
        traceback.print_exc()
        word_ok = False
    
    return syllable_ok and word_ok


def test_attention_extraction():
    """Test attention weight extraction."""
    print("\n" + "=" * 80)
    print("TEST 3: Attention Weight Extraction")
    print("=" * 80)
    
    from transformers import HubertModel
    
    model_path = Path("../findsylls/models/vg-hubert_3")
    if not model_path.exists():
        print("❌ Model not found")
        return False
    
    # Load with eager attention
    print("\nLoading model with eager attention...")
    model = HubertModel.from_pretrained(
        "facebook/hubert-base-ls960",
        attn_implementation='eager'
    )
    
    # Try word checkpoint, fallback to syllable
    word_ckpt = model_path / "vg-hubert-word.pth"
    if not word_ckpt.exists():
        word_ckpt = model_path / "snapshot_20.pth"
    if not word_ckpt.exists():
        word_ckpt = model_path / "vg-hubert-syllable.pth"
    
    checkpoint = torch.load(word_ckpt, map_location='cpu')
    if "dual_encoder" in checkpoint:
        state_dict = checkpoint['dual_encoder']
    else:
        state_dict = checkpoint
    
    model.load_state_dict(state_dict, strict=False)
    model.eval()
    
    # Test attention extraction
    audio = torch.randn(1, 16000)
    
    with torch.no_grad():
        outputs = model(
            audio,
            output_attentions=True,
            output_hidden_states=True
        )
    
    if outputs.attentions is not None and len(outputs.attentions) > 0:
        attn = outputs.attentions[8]  # Layer 9 (0-indexed as 8)
        print(f"\n✅ Attention weights extracted")
        print(f"   Shape: {attn.shape}")
        print(f"   Expected: [batch=1, heads=12, seq_len, seq_len]")
        
        # Test CLS attention
        cls_attn = attn[:, :, 0, 1:]
        print(f"   CLS attention shape: {cls_attn.shape}")
        print(f"   CLS attention range: [{cls_attn.min():.4f}, {cls_attn.max():.4f}]")
        
        return True
    else:
        print("\n❌ FAIL: Could not extract attention weights")
        return False


def main():
    print("\n" + "=" * 80)
    print("VG-HuBERT Validation Test Suite")
    print("(New Implementation Only)")
    print("=" * 80)
    
    results = {}
    
    try:
        results['consistency'] = test_model_consistency()
    except Exception as e:
        print(f"\n❌ Consistency test failed: {e}")
        import traceback
        traceback.print_exc()
        results['consistency'] = False
    
    try:
        results['segmenter'] = test_segmenter_interface()
    except Exception as e:
        print(f"\n❌ Segmenter test failed: {e}")
        import traceback
        traceback.print_exc()
        results['segmenter'] = False
    
    try:
        results['attention'] = test_attention_extraction()
    except Exception as e:
        print(f"\n❌ Attention test failed: {e}")
        import traceback
        traceback.print_exc()
        results['attention'] = False
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20s}: {status}")
    
    print("\n" + "=" * 80)
    
    if all(results.values()):
        print("✅ ALL TESTS PASSED - Implementation is valid!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
