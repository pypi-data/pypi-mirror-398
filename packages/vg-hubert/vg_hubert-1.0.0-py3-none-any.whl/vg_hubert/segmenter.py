"""
VG-HuBERT Segmenter - Simplified Interface

This module provides a Sylber-like interface for VG-HuBERT:
    from vg_hubert import Segmenter
    segmenter = Segmenter()  # That's it!

Interface design inspired by Sylber (Cho et al., 2024):
    https://github.com/Berkeley-Speech-Group/sylber
    
Handles all complexity internally:
- Model download from HuggingFace Hub
- Both word and syllable segmentation
- MinCut algorithm integration
- Native PyTorch attention (no patching required)
"""

import torch
import numpy as np
import soundfile as sf
from typing import Dict, Union, Optional, List, Tuple
from pathlib import Path
import logging
import os
import pickle

logger = logging.getLogger(__name__)


class Segmenter:
    """
    VG-HuBERT Segmenter with Sylber-like interface.
    
    Usage (as simple as Sylber):
        >>> from vg_hubert import Segmenter
        >>> segmenter = Segmenter()  # Downloads model automatically
        >>> outputs = segmenter("audio.wav")
        >>> # outputs contains 'segments', 'features', 'hidden_states'
    
    Args:
        model_ckpt: Model checkpoint. Options:
                   - "vg-hubert" (default): Downloads from HuggingFace Hub
                   - Local path to model directory
        mode: Segmentation mode:
             - "syllable": MinCut-based syllable segmentation (default)
             - "word": Attention-based word segmentation
        layer: Which HuBERT layer to use (default: 8 for syllables, 9 for words)
        device: 'cuda', 'mps', or 'cpu' (default: 'cuda', auto-falls back to mps/cpu)
        sec_per_syllable: Target syllable duration for MinCut (default: 0.2)
        merge_threshold: Similarity threshold for merging segments (default: 0.3)
                        Set to None to disable MinCutMerge post-processing
        min_segment_frames: Filter segments with ≤ this many frames (default: 2)
        attn_threshold: Attention threshold for word segmentation (default: 0.7)
    
    Examples:
        >>> # Syllable segmentation (like Sylber)
        >>> segmenter = Segmenter()
        >>> outputs = segmenter("audio.wav")
        >>> for start, end in outputs['segments']:
        ...     print(f"Syllable: {start:.2f}s - {end:.2f}s")
        
        >>> # Word segmentation
        >>> segmenter = Segmenter(mode="word")
        >>> outputs = segmenter("audio.wav")
        >>> for start, end in outputs['segments']:
        ...     print(f"Word: {start:.2f}s - {end:.2f}s")
    """
    
    def __init__(
        self,
        model_ckpt: Optional[str] = None,
        mode: str = "syllable",
        layer: Optional[int] = None,
        device: str = "cuda",
        sec_per_syllable: Optional[float] = None,
        merge_threshold: Optional[float] = None,
        min_segment_frames: int = 2,
        attn_threshold: float = 0.25,
        checkpoint_file: Optional[str] = None,  # Override which .pth file to use
        segmentation_method: Optional[str] = None,  # "featSSM" or "CLS" (None = auto based on mode)
        use_optimized_mincut: bool = True,  # Use optimized MinCut (SyllableLM) vs original
        **kwargs
    ):
        """
        Initialize VG-HuBERT Segmenter.
        
        Following syllable-discovery repo recommendations:
        - Syllable mode: best_bundle.pth, layer 8, sec_per_syllable=0.2, merge_threshold=0.3
        - Word mode: snapshot_20.pth, layer 9, attention-based
        """
        self.mode = mode
        
        # Set defaults based on mode (from syllable-discovery repo)
        if mode == "syllable":
            self.layer = layer if layer is not None else 8
            self.sec_per_syllable = sec_per_syllable if sec_per_syllable is not None else 0.2
            self.merge_threshold = merge_threshold if merge_threshold is not None else 0.3
            self.checkpoint_file = checkpoint_file if checkpoint_file is not None else "vg-hubert-syllable.pth"
            # Default: featSSM (MinCut) for syllables
            self.segmentation_method = segmentation_method if segmentation_method is not None else "featSSM"
        elif mode == "word":
            self.layer = layer if layer is not None else 9
            self.sec_per_syllable = sec_per_syllable if sec_per_syllable is not None else 0.2
            self.merge_threshold = merge_threshold if merge_threshold is not None else 0.3
            self.checkpoint_file = checkpoint_file if checkpoint_file is not None else "vg-hubert-word.pth"
            # Default: CLS attention for words
            self.segmentation_method = segmentation_method if segmentation_method is not None else "CLS"
        else:
            raise ValueError(f"mode must be 'syllable' or 'word', got {mode}")
        
        if self.segmentation_method not in ["featSSM", "CLS"]:
            raise ValueError(f"segmentation_method must be 'featSSM' or 'CLS', got {self.segmentation_method}")
        
        self.min_segment_frames = min_segment_frames
        self.attn_threshold = attn_threshold
        self.use_optimized_mincut = use_optimized_mincut
        
        # Device setup: try CUDA -> MPS -> CPU
        if device == "cuda":
            if torch.cuda.is_available():
                self.device = "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                logger.info("CUDA not available, using MPS (Apple Silicon GPU)")
                self.device = "mps"
            else:
                logger.warning("CUDA not available, using CPU")
                self.device = "cpu"
        else:
            self.device = device
        
        # Auto-detect model path if not provided
        if model_ckpt is None:
            model_ckpt = "hjvm/VG-HuBERT" # Will try to download from Hub
        
        # Load model
        self._load_model(model_ckpt)
    
    def _load_model(self, model_ckpt: str):
        """Load VG-HuBERT model."""
        from transformers import HubertModel
        
        # Check if it's a HuggingFace model or local path
        if os.path.isdir(model_ckpt):
            model_path = Path(model_ckpt)
            logger.info(f"Loading model from local path: {model_path}")
            
            # Load from legacy format - use appropriate checkpoint for mode
            checkpoint_path = model_path / self.checkpoint_file
            if not checkpoint_path.exists():
                # Fallback to old names for backward compatibility
                old_name = "best_bundle.pth" if self.mode == "syllable" else "snapshot_20.pth"
                logger.warning(f"{self.checkpoint_file} not found, trying legacy name {old_name}")
                checkpoint_path = model_path / old_name
                
            if not checkpoint_path.exists():
                raise FileNotFoundError(f"Model checkpoint not found: {checkpoint_path}")
            
            logger.info(f"Loading checkpoint: {checkpoint_path.name}")
            
            args_path = model_path / "args.pkl"
            if not args_path.exists():
                raise FileNotFoundError(f"Model args not found: {args_path}")
            
            # Load args
            with open(args_path, "rb") as f:
                args = pickle.load(f)
            
            # Initialize model using transformers HuBERT (avoids fairseq dependency)
            # Use eager attention only for word mode (needs attention weights)
            # SDPA is faster but can't output attention weights
            attn_impl = 'eager' if self.mode == 'word' else 'sdpa'
            self.model = HubertModel.from_pretrained(
                "facebook/hubert-base-ls960",
                attn_implementation=attn_impl
            )
            logger.info(f"Using {attn_impl} attention implementation for {self.mode} mode")
            
            # Load VG-HuBERT weights
            checkpoint = torch.load(checkpoint_path, map_location=self.device)
            if "dual_encoder" in checkpoint:
                state_dict = checkpoint["dual_encoder"]
            else:
                state_dict = checkpoint
            
            # Extract audio_encoder weights with key mapping for HuBERT compatibility
            # VG-HuBERT audio_encoder weights are compatible with HuBERT but use different key names
            audio_encoder_state = {}
            for key, value in state_dict.items():
                if key.startswith('audio_encoder.'):
                    # Strip 'audio_encoder.' prefix
                    new_key = key.replace('audio_encoder.', '', 1)
                    # Map VG-HuBERT keys to HuBERT keys
                    new_key = new_key.replace('self_attn.', 'attention.')
                    new_key = new_key.replace('.fc1.', '.feed_forward.intermediate_dense.')
                    new_key = new_key.replace('.fc2.', '.feed_forward.output_dense.')
                    audio_encoder_state[new_key] = value
            
            # Load weights with key mapping
            missing_keys, unexpected_keys = self.model.load_state_dict(audio_encoder_state, strict=False)
            logger.info(f"Loaded VG-HuBERT weights from {checkpoint_path.name}")
            if missing_keys:
                logger.debug(f"Missing keys (using HuBERT defaults): {len(missing_keys)}")
            if unexpected_keys:
                logger.debug(f"Unexpected keys (VG-HuBERT specific): {len(unexpected_keys)}")
        
        else:
            # Download from HuggingFace Hub
            from huggingface_hub import hf_hub_download
            
            logger.info(f"Downloading VG-HuBERT from HuggingFace Hub: {model_ckpt}")
            
            # Download checkpoint and args
            try:
                # Use appropriate checkpoint for mode
                checkpoint_path = hf_hub_download(
                    repo_id=model_ckpt,
                    filename=self.checkpoint_file
                )
                args_path = hf_hub_download(
                    repo_id=model_ckpt,
                    filename="args.pkl"
                )
                
                logger.info(f"Downloaded {self.checkpoint_file} and args.pkl")
                
                # Load model
                with open(args_path, "rb") as f:
                    args = pickle.load(f)
                
                attn_impl = 'eager' if self.mode == 'word' else 'sdpa'
                logger.info(f"Using {attn_impl} attention implementation for {self.mode} mode")
                self.model = HubertModel.from_pretrained(
                    "facebook/hubert-base-ls960",
                    attn_implementation=attn_impl
                )
                logger.info(f"Using {attn_impl} attention for {self.mode} mode")
                checkpoint = torch.load(checkpoint_path, map_location=self.device)
                if "dual_encoder" in checkpoint:
                    state_dict = checkpoint["dual_encoder"]
                else:
                    state_dict = checkpoint
                
                # Extract audio_encoder weights with key mapping for HuBERT compatibility
                audio_encoder_state = {}
                for key, value in state_dict.items():
                    if key.startswith('audio_encoder.'):
                        # Strip 'audio_encoder.' prefix
                        new_key = key.replace('audio_encoder.', '', 1)
                        # Map VG-HuBERT keys to HuBERT keys
                        new_key = new_key.replace('self_attn.', 'attention.')
                        new_key = new_key.replace('.fc1.', '.feed_forward.intermediate_dense.')
                        new_key = new_key.replace('.fc2.', '.feed_forward.output_dense.')
                        audio_encoder_state[new_key] = value
                
                # Load weights with key mapping
                missing_keys, unexpected_keys = self.model.load_state_dict(audio_encoder_state, strict=False)
                logger.info("Model loaded from HuggingFace Hub")
                if missing_keys:
                    logger.debug(f"Missing keys (using HuBERT defaults): {len(missing_keys)}")
                if unexpected_keys:
                    logger.debug(f"Unexpected keys (VG-HuBERT specific): {len(unexpected_keys)}")
                
            except Exception as e:
                logger.warning(
                    f"Could not download VG-HuBERT from Hub: {e}\n"
                    f"Falling back to base HuBERT model (facebook/hubert-base-ls960).\n"
                    f"For full VG-HuBERT functionality, download the model from:\n"
                    f"https://www.cs.utexas.edu/~harwath/model_checkpoints/vg_hubert/vg-hubert_3.tar"
                )
                # Use base HuBERT as fallback for demonstration
                attn_impl = 'eager' if self.mode == 'word' else 'sdpa'
                self.model = HubertModel.from_pretrained(
                    "facebook/hubert-base-ls960",
                    attn_implementation=attn_impl
                )
                logger.info(f"Using base HuBERT model ({attn_impl} attention) as fallback")
        
        self.model = self.model.to(self.device)
        self.model.eval()
    
    def __call__(
        self,
        wav_file: Optional[str] = None,
        wav: Optional[np.ndarray] = None,
        in_second: bool = True
    ) -> Dict:
        """
        Segment audio (Sylber-compatible interface).
        
        Args:
            wav_file: Path to audio file
            wav: Audio waveform array (16kHz, mono)
            in_second: If True, return times in seconds; if False, in frames
        
        Returns:
            Dictionary containing:
            - 'segments': List of (start, end) tuples (syllables or words)
            - 'segment_features': Segment-level features
            - 'hidden_states': Frame-level hidden states
            - 'cls_attention': CLS attention scores (word mode only)
        """
        # Load audio
        if wav_file is not None:
            audio, sr = sf.read(wav_file, dtype='float32')
        elif wav is not None:
            audio = wav
            sr = 16000
        else:
            raise ValueError("Must provide either wav_file or wav")
        
        # Ensure 16kHz mono
        if sr != 16000:
            import librosa
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            sr = 16000
        
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)
        
        # Convert to tensor
        audio_tensor = torch.from_numpy(audio).float().unsqueeze(0).to(self.device)
        audio_len_sec = len(audio) / sr
        
        # Extract features
        with torch.no_grad():
            outputs = self.model(
                input_values=audio_tensor,
                output_hidden_states=True,
                return_dict=True
            )
            
            # Get features from specified layer
            features = outputs.hidden_states[self.layer][0].cpu().float().numpy()
            
            # Remove CLS token if present
            if features.shape[0] > len(audio) / 320:  # HuBERT downsamples by 320
                features = features[1:]
        
        # Calculate seconds per frame
        spf = audio_len_sec / features.shape[0]
        
        # Segment based on segmentation_method (not mode)
        if self.segmentation_method == "featSSM":
            result = self._segment_featssm(features, spf, audio_len_sec, in_second)
        elif self.segmentation_method == "CLS":
            result = self._segment_cls(audio_tensor, features, spf, audio_len_sec, in_second)
        else:
            raise ValueError(f"Unknown segmentation_method: {self.segmentation_method}")
        
        # Add hidden states
        result['hidden_states'] = features
        
        return result
    
    def _segment_featssm(
        self,
        features: np.ndarray,
        spf: float,
        audio_len_sec: float,
        in_second: bool
    ) -> Dict:
        """Segment using featSSM (MinCut) algorithm with optional MinCutMerge post-processing."""
        # Estimate number of segments
        num_segments = max(1, int(np.ceil(audio_len_sec / self.sec_per_syllable)))
        K = num_segments + 1  # Number of boundaries
        
        # Apply MinCut with optional merging
        try:
            from .mincut import segment_with_mincut
            seg_boundary_frames, ssm = segment_with_mincut(
                features=features,
                K=K,
                merge_threshold=self.merge_threshold,  # None = no merging
                min_segment_frames=self.min_segment_frames,
                use_optimized=self.use_optimized_mincut  # Choose algorithm version
            )
        except Exception as e:
            # Fallback: uniform segmentation
            logger.warning(f"MinCut failed ({e}), using uniform segmentation")
            seg_boundary_frames = np.linspace(0, features.shape[0], K).astype(int)
        
        # Create segments
        seg_pairs = [[l, r] for l, r in zip(seg_boundary_frames[:-1], seg_boundary_frames[1:])]
        
        # Convert to time
        if in_second:
            segments = [[l * spf, r * spf] for l, r in seg_pairs]
        else:
            segments = seg_pairs
        
        # Extract segment features
        segment_features = torch.stack([
            torch.from_numpy(features[l:r].mean(0)) for l, r in seg_pairs
        ])
        
        return {
            'segments': segments,
            'segment_features': segment_features
        }
    
    def _segment_cls(
        self,
        audio_tensor: torch.Tensor,
        features: np.ndarray,
        spf: float,
        audio_len_sec: float,
        in_second: bool
    ) -> Dict:
        """
        Segment using CLS token attention weights.
        
        Following VG-HuBERT word-discovery paper: use attention from CLS token
        to identify boundaries. Peaks in CLS attention indicate segment onsets.
        """
        try:
            # Extract attention weights from the target layer
            with torch.no_grad():
                outputs = self.model(
                    input_values=audio_tensor,
                    output_attentions=True,
                    return_dict=True
                )
                
                # Get attention from target layer
                # Shape: (batch_size, num_heads, seq_len, seq_len)
                attn = outputs.attentions[self.layer]
                
                # Extract CLS token attention (first token attends to all positions)
                # Shape: (batch_size, num_heads, seq_len)
                cls_attn = attn[0, :, 0, :]
                
                # Remove CLS position itself
                if cls_attn.shape[1] > features.shape[0]:
                    cls_attn = cls_attn[:, 1:]
                
                # Average over heads or use max/specific heads
                # Paper uses different strategies - here we use max across heads
                cls_attn_score = cls_attn.max(dim=0)[0].cpu().numpy()
                
                # Ensure alignment with features
                if len(cls_attn_score) > features.shape[0]:
                    cls_attn_score = cls_attn_score[:features.shape[0]]
            
            # Find peaks in CLS attention (word onsets)
            from scipy.signal import find_peaks
            
            # Normalize attention scores
            cls_attn_score = (cls_attn_score - cls_attn_score.min()) / (cls_attn_score.max() - cls_attn_score.min() + 1e-8)
            
            # Find peaks above threshold
            peaks, _ = find_peaks(cls_attn_score, height=self.attn_threshold, distance=int(0.1 / spf))
            
            # Create segments between peaks
            if len(peaks) == 0:
                # No peaks found, return whole utterance
                seg_pairs = [[0, features.shape[0]]]
            else:
                # Add boundaries at start and end
                boundaries = [0] + peaks.tolist() + [features.shape[0]]
                seg_pairs = [[l, r] for l, r in zip(boundaries[:-1], boundaries[1:])]
                seg_pairs = [item for item in seg_pairs if item[1] - item[0] > 2]
            
            # Convert to time
            if in_second:
                segments = [[l * spf, r * spf] for l, r in seg_pairs]
            else:
                segments = seg_pairs
            
            # Extract segment features
            segment_features = torch.stack([
                torch.from_numpy(features[l:r].mean(0)) for l, r in seg_pairs
            ])
            
            logger.info(f"CLS attention-based segmentation: {len(segments)} segments")
            
            return {
                'segments': segments,
                'segment_features': segment_features,
                'cls_attention': cls_attn_score  # Include attention scores for analysis
            }
            
        except Exception as e:
            logger.warning(f"CLS attention segmentation failed ({e}), falling back to featSSM")
            return self._segment_featssm(features, spf, audio_len_sec, in_second)
        
    def save_pretrained(self, save_directory: str):
        """Save model (for compatibility)."""
        raise NotImplementedError("Use the full VGHubertModel for saving to Hub")
    
    @classmethod
    def from_pretrained(cls, model_name: str, **kwargs):
        """Load model from HuggingFace Hub (for compatibility)."""
        return cls(model_ckpt=model_name, **kwargs)
