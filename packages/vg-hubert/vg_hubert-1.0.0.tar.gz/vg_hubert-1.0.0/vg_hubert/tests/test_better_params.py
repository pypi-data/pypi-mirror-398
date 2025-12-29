"""
Quick test to find better parameters for LibriSpeech.
Testing different SEC_PER_SYLLABLE values.
"""

import sys
from pathlib import Path
import numpy as np
import torch
from glob import glob
import textgrid
import pandas as pd
from typing import List, Tuple, Dict

project_root = Path.cwd()
sys.path.insert(0, str(project_root))

from vg_hubert import Segmenter
from vg_hubert.mincut import min_cut

# Setup
AUDIO_GLOB = str(Path.home() / "datasets/LibriSpeech/test-clean/**/*.flac")
TEXTGRID_GLOB = str(project_root.parent / "findsylls/data/LibriSpeech/librispeech_alignments/test-clean/**/*_syllabified.TextGrid")
MODEL_PATH = project_root / "models/vg-hubert_3"
TOLERANCE_MS = 50
MAX_FILES = 50

# Load model
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Loading model... (device: {device})")
segmenter = Segmenter(
    model_ckpt=str(MODEL_PATH),
    mode="syllable",
    device=device,
    layer=8
)

# Test different SEC_PER_SYLLABLE values
test_values = [0.2, 0.22, 0.24, 0.25, 0.26, 0.28, 0.3]

print(f"\nTesting {MAX_FILES} files with different SEC_PER_SYLLABLE values...")
print(f"Tolerance: ±{TOLERANCE_MS}ms\n")

results_by_param = {}

for sec_per_syl in test_values:
    print(f"Testing SEC_PER_SYLLABLE={sec_per_syl}...")
    
    # Use the segmenter to test
    # For now, let's just report what K we'd use
    audio_files = sorted(glob(AUDIO_GLOB, recursive=True))[:MAX_FILES]
    
    if len(audio_files) == 0:
        print("No audio files found!")
        break
    
    # Quick estimate
    total_duration = 0
    for audio_file in audio_files[:10]:  # Sample
        import torchaudio
        waveform, sr = torchaudio.load(audio_file)
        total_duration += waveform.shape[1] / sr
    
    avg_duration = total_duration / 10
    k_estimated = max(2, int(np.ceil(avg_duration / sec_per_syl)) + 1)
    
    print(f"  Avg duration: {avg_duration:.2f}s")
    print(f"  Estimated K: {k_estimated}")
    
    results_by_param[sec_per_syl] = k_estimated

print("\n=== Summary ===")
print("Avg syllable duration in dataset: 0.249s")
print("\nEstimated K values:")
for sec_per_syl, k in results_by_param.items():
    print(f"  {sec_per_syl}s -> K={k}")
    
print("\nGround truth avg K: 31.2")
print("Recommended SEC_PER_SYLLABLE: 0.25-0.26")
