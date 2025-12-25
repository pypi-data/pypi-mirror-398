import os
from datasets import Dataset, load_from_disk
from typing import Tuple, Callable, List
from torch.utils.data import DataLoader


def split_dataset(
    dataset: Dataset, train_size: float = 0.8, val_size: float = 0.1, seed: int = 42
) -> Tuple[Dataset, Dataset, Dataset]:
    """
    Split HF dataset into train, validation and test.

    Args:
        dataset: HF dataset.
        train_size: train ratio from 0 to 1.
        val_size: validation ratio from 0 to 1.
        seed: seed used for splitting.

    Returns:
        a tuple of 3 datasets for train, validation and test.

    train_size and val_size are taken from total and their sum should not be more than 1.

    Test size would be equal to 1 - train_size - val_size.
    """
    split1 = dataset.train_test_split(train_size=train_size, seed=seed)  # type: ignore
    train = split1["train"]
    temp = split1["test"]
    temp_val_size = val_size / (1.0 - train_size)
    split2 = temp.train_test_split(train_size=temp_val_size, seed=seed)  # type: ignore
    val = split2["train"]
    test = split2["test"]
    return train, val, test


def load_cached(cache_path: str, process_fn: Callable) -> Dataset:
    """
    Try loading processed dataset from cache. Processes dataset and saves it to cache if pre-cached dataset is not found.

    Args:
        cache_path: path to load/save dataset.
        process_fn: function that will return a new processed dataset if cache is not found.

    Returns:
        a pre-processed HF dataset.
    """
    if os.path.exists(cache_path):
        print(f"Loading dataset from '{cache_path}'...")
        ds = load_from_disk(cache_path)
    else:
        ds = process_fn()
        print("Saving processed dataset to disk...")
        ds.save_to_disk(cache_path)
        print(f"Processed dataset saved to '{cache_path}'")
    print("Dataset is ready!")
    return ds  # type: ignore


def get_loaders(
    dataset: Dataset,
    collate_fn: Callable = lambda x: x,
    batch_size: int = 16,
    train_size: float = 0.8,
    val_size: float = 0.1,
    num_workers: int = 15,
    seed: int = 42,
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    Shortcut to generate pytorch dataloaders (train/val/test) from hf dataset.

    Args:
        dataset: HF dataset.
        collate_fn: function used for dataset collation.
        batch_size: batch_size for dataloaders.
        train_size: train split size. see `split_dataset`.
        val_size: validation split size. see `split_dataset`.
        num_workers: number of pytorch dataloader workers.
        seed: random seed used for splitting.

    Returns:
        a tuple with train, validation and test pytorch dataloaders.

    Splits dataset and assigns collators automatically.
    """
    train, val, test = split_dataset(
        dataset, train_size=train_size, val_size=val_size, seed=seed
    )
    train_loader = DataLoader(train, batch_size=batch_size, collate_fn=collate_fn, num_workers=num_workers, shuffle=True)  # type: ignore
    val_loader = DataLoader(val, batch_size=batch_size, collate_fn=collate_fn, num_workers=num_workers, shuffle=False)  # type: ignore
    test_loader = DataLoader(test, batch_size=batch_size, collate_fn=collate_fn, num_workers=num_workers, shuffle=False)  # type: ignore
    return train_loader, val_loader, test_loader


def strip_features(
    dataset: Dataset, keep_features: List[str] = ["input_ids", "prompt_mask"]
) -> Dataset:
    """
    Remove all features from dataset except specified ones.

    Args:
        dataset: HF dataset to purify.
        keep_features: list of feature names to keep.

    Returns:
        a new dataset with only specified features.

    Useful for reducing memory usage and cleaning up datasets.
    """

    # Get current features
    current_features = set(dataset.features.keys())
    features_to_remove = current_features - set(keep_features)

    if not features_to_remove:
        print(f"Dataset already has only {keep_features} features")
        return dataset

    print(f"Removing features: {list(features_to_remove)}")
    print(f"Keeping features: {keep_features}")

    # Remove unwanted features
    return dataset.remove_columns(list(features_to_remove))
