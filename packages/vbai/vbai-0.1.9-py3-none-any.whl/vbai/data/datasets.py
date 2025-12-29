"""
Dataset Classes for Vbai
"""

import os
import random
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Callable, Union
from PIL import Image

import torch
from torch.utils.data import Dataset, DataLoader

from .transforms import get_train_transforms, get_val_transforms


class MRIDataset(Dataset):
    """
    Simple MRI Dataset for single-task training.
    
    Args:
        root: Root directory containing class folders
        transform: Optional transform to apply
        is_training: Whether this is training data (affects default transforms)
    
    Example:
        >>> dataset = MRIDataset(
        ...     root='./data/dementia',
        ...     is_training=True
        ... )
        >>> image, label = dataset[0]
    """
    
    def __init__(
        self,
        root: str,
        transform: Optional[Callable] = None,
        is_training: bool = True
    ):
        self.root = Path(root)
        self.is_training = is_training
        
        # Set default transform if not provided
        if transform is None:
            self.transform = get_train_transforms() if is_training else get_val_transforms()
        else:
            self.transform = transform
        
        # Discover classes and images
        self.classes = sorted([
            d.name for d in self.root.iterdir() 
            if d.is_dir() and not d.name.startswith('.')
        ])
        self.class_to_idx = {cls: i for i, cls in enumerate(self.classes)}
        
        # Collect all samples
        self.samples: List[Tuple[Path, int]] = []
        for class_name in self.classes:
            class_dir = self.root / class_name
            class_idx = self.class_to_idx[class_name]

            for img_path in class_dir.iterdir():
                if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                    self.samples.append((img_path, class_idx))

        if len(self.samples) == 0:
            raise ValueError(
                f"No valid image samples found in '{self.root}'. "
                f"Please ensure the directory contains subdirectories with image files "
                f"(.jpg, .jpeg, .png, .bmp, .gif)."
            )
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img_path, label = self.samples[idx]
        
        # Load image
        image = Image.open(img_path).convert('RGB')
        
        # Apply transform
        if self.transform:
            image = self.transform(image)
        
        return image, label
    
    def get_class_counts(self) -> Dict[str, int]:
        """Get number of samples per class."""
        counts = {cls: 0 for cls in self.classes}
        for _, label in self.samples:
            class_name = self.classes[label]
            counts[class_name] += 1
        return counts


class UnifiedMRIDataset(Dataset):
    """
    Unified dataset for multi-task brain MRI classification.
    
    Combines dementia and tumor datasets, handling cases where
    only one label is available (using ignore_index for loss).
    
    Args:
        dementia_path: Path to dementia dataset (optional)
        tumor_path: Path to tumor dataset (optional)
        transform: Transform to apply
        is_training: Whether this is training data
        dementia_classes: List of dementia class names (auto-detected if None)
        tumor_classes: List of tumor class names (auto-detected if None)
    
    Example:
        >>> dataset = UnifiedMRIDataset(
        ...     dementia_path='./data/dementia',
        ...     tumor_path='./data/tumor',
        ...     is_training=True
        ... )
        >>> image, dementia_label, tumor_label = dataset[0]
    """
    
    DEMENTIA_CLASSES = [
        'AD_Alzheimer', 'AD_Mild_Demented', 'AD_Moderate_Demented',
        'AD_Very_Mild_Demented', 'CN_Non_Demented', 'PD_Parkinson'
    ]
    
    TUMOR_CLASSES = ['Glioma', 'Meningioma', 'No_Tumor', 'Pituitary']
    
    def __init__(
        self,
        dementia_path: Optional[str] = None,
        tumor_path: Optional[str] = None,
        transform: Optional[Callable] = None,
        is_training: bool = True,
        dementia_classes: Optional[List[str]] = None,
        tumor_classes: Optional[List[str]] = None
    ):
        if dementia_path is None and tumor_path is None:
            raise ValueError("At least one of dementia_path or tumor_path must be provided")
        
        self.dementia_path = Path(dementia_path) if dementia_path else None
        self.tumor_path = Path(tumor_path) if tumor_path else None
        self.is_training = is_training
        
        # Set transform
        if transform is None:
            self.transform = get_train_transforms() if is_training else get_val_transforms()
        else:
            self.transform = transform
        
        # Class mappings
        self.dementia_classes = dementia_classes or self.DEMENTIA_CLASSES
        self.tumor_classes = tumor_classes or self.TUMOR_CLASSES
        
        self.dementia_to_idx = {cls: i for i, cls in enumerate(self.dementia_classes)}
        self.tumor_to_idx = {cls: i for i, cls in enumerate(self.tumor_classes)}
        
        # Collect samples
        self.samples: List[Tuple[Path, int, int]] = []  # (path, dementia_label, tumor_label)
        
        # Add dementia samples
        if self.dementia_path and self.dementia_path.exists():
            for class_dir in self.dementia_path.iterdir():
                if not class_dir.is_dir() or class_dir.name.startswith('.'):
                    continue
                
                class_name = class_dir.name
                if class_name in self.dementia_to_idx:
                    dementia_idx = self.dementia_to_idx[class_name]
                    
                    for img_path in class_dir.iterdir():
                        if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                            # -1 for tumor (unknown)
                            self.samples.append((img_path, dementia_idx, -1))
        
        # Add tumor samples
        if self.tumor_path and self.tumor_path.exists():
            for class_dir in self.tumor_path.iterdir():
                if not class_dir.is_dir() or class_dir.name.startswith('.'):
                    continue
                
                class_name = class_dir.name
                if class_name in self.tumor_to_idx:
                    tumor_idx = self.tumor_to_idx[class_name]
                    
                    for img_path in class_dir.iterdir():
                        if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                            # -1 for dementia (unknown)
                            self.samples.append((img_path, -1, tumor_idx))
        
        if len(self.samples) == 0:
            error_msg = "No valid samples found. "
            if self.dementia_path:
                if not self.dementia_path.exists():
                    error_msg += f"Dementia path '{self.dementia_path}' does not exist. "
                else:
                    error_msg += f"Dementia path '{self.dementia_path}' exists but contains no valid images. "
            if self.tumor_path:
                if not self.tumor_path.exists():
                    error_msg += f"Tumor path '{self.tumor_path}' does not exist. "
                else:
                    error_msg += f"Tumor path '{self.tumor_path}' exists but contains no valid images. "
            error_msg += "Please check your dataset paths and ensure they contain subdirectories with image files."
            raise ValueError(error_msg)

        if is_training:
            random.shuffle(self.samples)
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int, int]:
        img_path, dementia_label, tumor_label = self.samples[idx]
        
        # Load image
        image = Image.open(img_path).convert('RGB')
        
        # Apply transform
        if self.transform:
            image = self.transform(image)
        
        return image, dementia_label, tumor_label
    
    def get_statistics(self) -> Dict:
        """Get dataset statistics."""
        dementia_counts = {cls: 0 for cls in self.dementia_classes}
        tumor_counts = {cls: 0 for cls in self.tumor_classes}
        
        for _, d_label, t_label in self.samples:
            if d_label >= 0:
                dementia_counts[self.dementia_classes[d_label]] += 1
            if t_label >= 0:
                tumor_counts[self.tumor_classes[t_label]] += 1
        
        return {
            'total_samples': len(self.samples),
            'dementia_samples': sum(dementia_counts.values()),
            'tumor_samples': sum(tumor_counts.values()),
            'dementia_distribution': dementia_counts,
            'tumor_distribution': tumor_counts,
        }
    
    def get_dataloader(
        self,
        batch_size: int = 32,
        shuffle: Optional[bool] = None,
        num_workers: int = 4,
        pin_memory: bool = True
    ) -> DataLoader:
        """Create a DataLoader for this dataset."""
        if shuffle is None:
            shuffle = self.is_training
        
        return DataLoader(
            self,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
            pin_memory=pin_memory
        )


def create_dataloaders(
    dementia_path: Optional[str] = None,
    tumor_path: Optional[str] = None,
    batch_size: int = 32,
    val_split: float = 0.2,
    num_workers: int = 4,
    seed: int = 42
) -> Tuple[DataLoader, DataLoader]:
    """
    Create train and validation dataloaders.
    
    Args:
        dementia_path: Path to dementia dataset
        tumor_path: Path to tumor dataset
        batch_size: Batch size
        val_split: Validation split ratio
        num_workers: Number of data loading workers
        seed: Random seed for reproducibility
    
    Returns:
        Tuple of (train_loader, val_loader)
    """
    # Create full dataset
    full_dataset = UnifiedMRIDataset(
        dementia_path=dementia_path,
        tumor_path=tumor_path,
        is_training=True
    )
    
    # Split into train/val
    total = len(full_dataset)
    val_size = int(total * val_split)
    train_size = total - val_size
    
    torch.manual_seed(seed)
    train_dataset, val_dataset = torch.utils.data.random_split(
        full_dataset, [train_size, val_size]
    )
    
    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )
    
    return train_loader, val_loader
