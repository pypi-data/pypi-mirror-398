"""
IrisVision - Face Recognition Suite
Made in Emirates 🇦🇪 | Product of Dubai

Usage:
    from irisvision import IrisVisionAixL
    
    model = IrisVisionAixL.load()
    embedding = model.encode("face.jpg")
    similarity = model.compare(emb1, emb2)
    is_match, score = model.verify(emb1, emb2)
"""

__version__ = "0.1.0"
__author__ = "vCodesUAE"
__email__ = "info@vcodes.ae"
__license__ = "MIT"

from .model import IrisVisionAixL, IrisVisionBackbone, ArcFaceModel

__all__ = [
    "IrisVisionAixL",
    "IrisVisionBackbone", 
    "ArcFaceModel",
    "__version__",
]


def info():
    """Display package information"""
    print("=" * 60)
    print("   IrisVision - Face Recognition Suite")
    print("   Made in Emirates 🇦🇪 | Product of Dubai")
    print("=" * 60)
    print(f"   Version:    {__version__}")
    print(f"   Accuracy:   98.58%")
    print(f"   Embedding:  512-dimensional")
    print(f"   Model:      vCodesUAE/IrisVisionAixL")
    print("=" * 60)
