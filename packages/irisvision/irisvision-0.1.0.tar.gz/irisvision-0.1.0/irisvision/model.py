"""
IrisVisionAixL - Face Recognition Model
Made in Emirates 🇦🇪 | Product of Dubai

Repository: https://huggingface.co/vCodesUAE/IrisVisionAixL
Architecture: IResNet-100 [3, 13, 30, 3]
"""

import os
import json
import torch
import torch.nn as nn
import torch.nn.functional as F
from huggingface_hub import hf_hub_download
from PIL import Image
import numpy as np
from typing import Union, List
from pathlib import Path


class BasicBlockIR(nn.Module):
    """Basic residual block for IResNet"""
    def __init__(self, in_channels, out_channels, stride):
        super().__init__()
        
        self.res_layer = nn.Sequential(
            nn.BatchNorm2d(in_channels),
            nn.Conv2d(in_channels, out_channels, 3, 1, 1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.PReLU(out_channels),
            nn.Conv2d(out_channels, out_channels, 3, stride, 1, bias=False),
            nn.BatchNorm2d(out_channels)
        )
        
        # Named 'shortcut_layer' to match checkpoint
        self.shortcut_layer = None
        if in_channels != out_channels or stride != 1:
            self.shortcut_layer = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 1, stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x):
        shortcut = x if self.shortcut_layer is None else self.shortcut_layer(x)
        return self.res_layer(x) + shortcut


class OutputLayer(nn.Module):
    """
    Output layer that matches checkpoint structure:
    - output_layer.0: BatchNorm2d(512)
    - output_layer.1: Dropout (no weights)
    - output_layer.2: Flatten (no weights)  
    - output_layer.3: Linear(25088, 512)
    - output_layer.4: BatchNorm1d(512)
    
    With added adaptive pooling before flatten.
    """
    def __init__(self, embedding_dim=512):
        super().__init__()
        # Match checkpoint indices exactly
        self.add_module('0', nn.BatchNorm2d(512))
        self.add_module('1', nn.Dropout(0.4))
        self.add_module('2', nn.Flatten())
        self.add_module('3', nn.Linear(512 * 7 * 7, embedding_dim))
        self.add_module('4', nn.BatchNorm1d(embedding_dim))
        
        # Adaptive pool (not in checkpoint, applied in forward)
        self.pool = nn.AdaptiveAvgPool2d((7, 7))
    
    def forward(self, x):
        x = self._modules['0'](x)      # BatchNorm2d
        x = self.pool(x)               # AdaptiveAvgPool2d (added)
        x = self._modules['1'](x)      # Dropout
        x = self._modules['2'](x)      # Flatten
        x = self._modules['3'](x)      # Linear
        x = self._modules['4'](x)      # BatchNorm1d
        return x


class IrisVisionBackbone(nn.Module):
    """
    IResNet-100 backbone for face recognition
    Configuration: [3, 13, 30, 3] = 49 blocks
    """
    def __init__(self, embedding_dim=512):
        super().__init__()
        
        # Input layer
        self.input_layer = nn.Sequential(
            nn.Conv2d(3, 64, 3, 1, 1, bias=False),
            nn.BatchNorm2d(64),
            nn.PReLU(64)
        )
        
        # Build body: [3, 13, 30, 3] configuration
        blocks = []
        
        # Stage 1: 64 channels (3 blocks)
        for _ in range(3):
            blocks.append(BasicBlockIR(64, 64, 1))
        
        # Stage 2: 128 channels (13 blocks)
        blocks.append(BasicBlockIR(64, 128, 2))
        for _ in range(12):
            blocks.append(BasicBlockIR(128, 128, 1))
        
        # Stage 3: 256 channels (30 blocks)
        blocks.append(BasicBlockIR(128, 256, 2))
        for _ in range(29):
            blocks.append(BasicBlockIR(256, 256, 1))
        
        # Stage 4: 512 channels (3 blocks)
        blocks.append(BasicBlockIR(256, 512, 2))
        for _ in range(2):
            blocks.append(BasicBlockIR(512, 512, 1))
        
        self.body = nn.Sequential(*blocks)
        
        # Output layer
        self.output_layer = OutputLayer(embedding_dim)
    
    def forward(self, x):
        x = self.input_layer(x)
        x = self.body(x)
        x = self.output_layer(x)
        return F.normalize(x, p=2, dim=1)


class ArcFaceModel(nn.Module):
    """Wrapper for compatibility"""
    def __init__(self, embedding_dim=512, num_classes=405):
        super().__init__()
        self.backbone = IrisVisionBackbone(embedding_dim)
    
    def forward(self, x):
        return self.backbone(x)


class IrisVisionAixL:
    """
    IrisVisionAixL - Production Face Recognition Model
    Made in Emirates 🇦🇪 | Product of Dubai
    
    Usage:
        from irisvision import IrisVisionAixL
        
        model = IrisVisionAixL.load()
        embedding = model.encode("face.jpg")
        similarity = model.compare(emb1, emb2)
        is_match, score = model.verify(emb1, emb2)
    """
    
    VERSION = "3.18"
    REPO_ID = "vCodesUAE/IrisVisionAixL"
    EMBEDDING_DIM = 512
    INPUT_SIZE = (112, 112)
    
    def __init__(self, model, device=None, config=None, identity_map=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = model.to(self.device)
        self.model.eval()
        self.config = config or {}
        self.identity_map = identity_map or {}
        self._init_transforms()
    
    @property
    def accuracy(self):
        return self.config.get("accuracy", 0.0)
    
    @property
    def num_classes(self):
        return self.config.get("classes", 405)
    
    def _init_transforms(self):
        from torchvision import transforms
        self.transform = transforms.Compose([
            transforms.Resize(self.INPUT_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])
    
    @classmethod
    def load(cls, repo_id=None, device=None, token=None, cache_dir=None):
        """Load model from HuggingFace Hub"""
        repo_id = repo_id or cls.REPO_ID
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"🇦🇪 Loading IrisVisionAixL v{cls.VERSION} from {repo_id}...")
        
        config = {}
        identity_map = {}
        
        # Load config
        try:
            config_path = hf_hub_download(repo_id=repo_id, filename="config.json", token=token, cache_dir=cache_dir)
            with open(config_path, "r") as f:
                config = json.load(f)
            acc = config.get('accuracy', 0)
            print(f"📋 Config: v{config.get('version', '?')} | {config.get('classes', '?')} classes | {acc:.2f}% accuracy")
        except Exception as e:
            print(f"⚠️ Config error: {e}")
        
        # Load identity map
        try:
            identity_path = hf_hub_download(repo_id=repo_id, filename="identity_map.json", token=token, cache_dir=cache_dir)
            with open(identity_path, "r") as f:
                identity_map = json.load(f)
            print(f"👥 Identity map loaded: {len(identity_map)} identities")
        except Exception as e:
            print(f"⚠️ Identity map error: {e}")
        
        # Load model weights
        try:
            model_path = hf_hub_download(repo_id=repo_id, filename="pytorch_model.bin", token=token, cache_dir=cache_dir)
        except:
            model_path = hf_hub_download(repo_id=repo_id, filename="backbone.pth", token=token, cache_dir=cache_dir)
        
        print(f"📦 Loading model weights...")
        checkpoint = torch.load(model_path, map_location=device, weights_only=False)
        
        # Create model
        model = IrisVisionBackbone(embedding_dim=cls.EMBEDDING_DIM)
        
        # Clean state dict - remove 'backbone.' prefix
        cleaned = {}
        for k, v in checkpoint.items():
            key = k[9:] if k.startswith("backbone.") else k
            cleaned[key] = v
        
        # Load weights
        missing, unexpected = model.load_state_dict(cleaned, strict=False)
        
        if len(missing) > 0:
            print(f"⚠️ Missing keys: {len(missing)}")
        if len(unexpected) > 0:
            print(f"⚠️ Unexpected keys: {len(unexpected)}")
        
        if len(missing) == 0 and len(unexpected) == 0:
            print(f"✅ All weights loaded perfectly!")
        
        print(f"🚀 IrisVisionAixL ready on {device}!")
        
        return cls(model, device, config, identity_map)
    
    @classmethod
    def from_pretrained(cls, model_path, config_path=None, identity_map_path=None, device=None):
        """Load from local files"""
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        config = {}
        identity_map = {}
        
        if config_path and os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
        
        if identity_map_path and os.path.exists(identity_map_path):
            with open(identity_map_path, "r") as f:
                identity_map = json.load(f)
        
        checkpoint = torch.load(model_path, map_location=device, weights_only=False)
        model = IrisVisionBackbone(embedding_dim=cls.EMBEDDING_DIM)
        
        cleaned = {}
        for k, v in checkpoint.items():
            key = k[9:] if k.startswith("backbone.") else k
            cleaned[key] = v
        
        model.load_state_dict(cleaned, strict=False)
        
        return cls(model, device, config, identity_map)
    
    def _preprocess(self, image):
        """Preprocess image for model input"""
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image).convert("RGB")
        elif isinstance(image, Image.Image):
            image = image.convert("RGB")
        
        tensor = self.transform(image)
        return tensor.unsqueeze(0).to(self.device)
    
    @torch.no_grad()
    def encode(self, image, normalize=True):
        """
        Extract face embedding from image
        
        Args:
            image: Face image (path, PIL Image, numpy array, or list)
            normalize: Whether to L2 normalize (default: True)
            
        Returns:
            512-dimensional embedding as numpy array
        """
        if isinstance(image, list):
            tensors = torch.cat([self._preprocess(img) for img in image], dim=0)
        else:
            tensors = self._preprocess(image)
        
        embedding = self.model(tensors)
        
        if normalize:
            embedding = F.normalize(embedding, p=2, dim=1)
        
        result = embedding.cpu().numpy()
        return result[0] if result.shape[0] == 1 else result
    
    def compare(self, emb1, emb2):
        """
        Calculate cosine similarity between two embeddings
        
        Returns:
            Similarity score (-1.0 to 1.0, higher = more similar)
        """
        if isinstance(emb1, torch.Tensor):
            emb1 = emb1.cpu().numpy()
        if isinstance(emb2, torch.Tensor):
            emb2 = emb2.cpu().numpy()
        
        emb1 = emb1 / (np.linalg.norm(emb1) + 1e-8)
        emb2 = emb2 / (np.linalg.norm(emb2) + 1e-8)
        
        return float(np.dot(emb1, emb2))
    
    def verify(self, emb1, emb2, threshold=0.4):
        """
        Verify if two embeddings are the same person
        
        Args:
            emb1, emb2: Face embeddings
            threshold: Similarity threshold (default: 0.4 for ArcFace)
            
        Returns:
            (is_match: bool, similarity: float)
        """
        similarity = self.compare(emb1, emb2)
        return similarity >= threshold, similarity
    
    def get_identity_name(self, class_idx):
        """Get identity name from class index"""
        return self.identity_map.get(str(class_idx), f"Unknown_{class_idx}")
    
    def __repr__(self):
        return f"IrisVisionAixL(version={self.VERSION}, accuracy={self.accuracy:.2f}%, classes={self.num_classes}, device={self.device})"
