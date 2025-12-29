"""
Image Transforms for Vbai
"""

from typing import Tuple, Optional, Callable
from torchvision import transforms


# ImageNet normalization values
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Default image size
DEFAULT_SIZE = 224


def get_transforms(
    image_size: int = DEFAULT_SIZE,
    is_training: bool = True,
    normalize: bool = True,
    augment: bool = True
) -> transforms.Compose:
    """
    Get image transforms for MRI data.
    
    Args:
        image_size: Target image size
        is_training: Whether to include training augmentations
        normalize: Whether to apply ImageNet normalization
        augment: Whether to apply data augmentation (only if is_training)
    
    Returns:
        Composed transform
    """
    transform_list = []
    
    # Resize
    transform_list.append(transforms.Resize((image_size, image_size)))
    
    # Training augmentations
    if is_training and augment:
        transform_list.extend([
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(10),
            transforms.ColorJitter(
                brightness=0.1,
                contrast=0.1,
                saturation=0.1
            ),
        ])
    
    # To tensor
    transform_list.append(transforms.ToTensor())
    
    # Normalize
    if normalize:
        transform_list.append(
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        )
    
    return transforms.Compose(transform_list)


def get_train_transforms(
    image_size: int = DEFAULT_SIZE,
    augmentation_strength: str = 'medium'
) -> transforms.Compose:
    """
    Get training transforms with configurable augmentation.
    
    Args:
        image_size: Target image size
        augmentation_strength: 'light', 'medium', or 'strong'
    
    Returns:
        Training transform
    """
    base_transforms = [
        transforms.Resize((image_size, image_size)),
    ]
    
    # Augmentation based on strength
    if augmentation_strength == 'light':
        augmentations = [
            transforms.RandomHorizontalFlip(p=0.3),
        ]
    elif augmentation_strength == 'medium':
        augmentations = [
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(10),
            transforms.ColorJitter(brightness=0.1, contrast=0.1),
        ]
    elif augmentation_strength == 'strong':
        augmentations = [
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.2),
            transforms.RandomRotation(15),
            transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
            transforms.ColorJitter(
                brightness=0.2,
                contrast=0.2,
                saturation=0.1,
                hue=0.05
            ),
            transforms.RandomPerspective(distortion_scale=0.1, p=0.3),
        ]
    else:
        augmentations = []
    
    final_transforms = [
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ]
    
    return transforms.Compose(base_transforms + augmentations + final_transforms)


def get_val_transforms(image_size: int = DEFAULT_SIZE) -> transforms.Compose:
    """
    Get validation/inference transforms (no augmentation).
    
    Args:
        image_size: Target image size
    
    Returns:
        Validation transform
    """
    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def get_test_time_augmentation(
    image_size: int = DEFAULT_SIZE,
    num_augmentations: int = 5
) -> Callable:
    """
    Get test-time augmentation transforms.
    
    Returns a function that generates multiple augmented versions
    of an input image for ensemble prediction.
    
    Args:
        image_size: Target image size
        num_augmentations: Number of augmented versions to generate
    
    Returns:
        Function that takes an image and returns list of augmented tensors
    """
    base_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])
    
    augment_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(5),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])
    
    def apply_tta(image):
        """Apply TTA to a single image."""
        augmented = [base_transform(image)]  # Original
        for _ in range(num_augmentations - 1):
            augmented.append(augment_transform(image))
        return augmented
    
    return apply_tta


def denormalize(
    tensor,
    mean: Tuple[float, ...] = IMAGENET_MEAN,
    std: Tuple[float, ...] = IMAGENET_STD
):
    """
    Denormalize a tensor for visualization.
    
    Args:
        tensor: Normalized tensor
        mean: Normalization mean values
        std: Normalization std values
    
    Returns:
        Denormalized tensor (0-1 range)
    """
    import torch
    
    mean = torch.tensor(mean).view(3, 1, 1)
    std = torch.tensor(std).view(3, 1, 1)
    
    if tensor.device != mean.device:
        mean = mean.to(tensor.device)
        std = std.to(tensor.device)
    
    return tensor * std + mean
