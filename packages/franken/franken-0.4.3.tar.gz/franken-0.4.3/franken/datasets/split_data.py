import argparse
import random
from ase.io import read, write
import os


def split_trajectory(
    file_path, split_ratio=0.8, seed=None, train_output=None, val_output=None
):
    # Set the random seed if provided, for reproducibility
    if seed is not None:
        random.seed(seed)

    # Load the frames from the trajectory file
    frames = read(file_path, index=":")
    num_frames = len(frames)
    print(f"Loaded {num_frames} frames from '{file_path}'.")

    # Shuffle and split frames based on the split ratio
    indices = list(range(num_frames))
    random.shuffle(indices)

    # Calculate the split index
    split_index = int(num_frames * split_ratio)
    train_indices = indices[:split_index]
    val_indices = indices[split_index:]

    # Create train and validation splits
    train_frames = [frames[i] for i in train_indices]
    val_frames = [frames[i] for i in val_indices]

    # Set default output filenames if not provided
    if train_output is None:
        train_output = f"{os.path.splitext(file_path)[0]}_train.xyz"
    if val_output is None:
        val_output = f"{os.path.splitext(file_path)[0]}_val.xyz"

    # Write the split trajectories to separate files
    write(train_output, train_frames)
    write(val_output, val_frames)

    print(
        f"Saved {len(train_frames)} frames to '{train_output}' and {len(val_frames)} frames to '{val_output}'."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Split an ASE trajectory file into train and validation sets in a reproducible way."
    )

    # Mandatory argument
    parser.add_argument(
        "file_path", type=str, help="Path to the input .xyz trajectory file."
    )

    # Optional arguments
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (default: None).",
    )
    parser.add_argument(
        "--split_ratio",
        type=float,
        default=0.8,
        help="Ratio of train to validation split (default: 0.8 for 80%% train).",
    )
    parser.add_argument(
        "--train_output",
        type=str,
        default=None,
        help="Output filename for the train set (default: 'input_train.xyz').",
    )
    parser.add_argument(
        "--val_output",
        type=str,
        default=None,
        help="Output filename for the validation set (default: 'input_val.xyz').",
    )

    args = parser.parse_args()

    # Validate the split ratio
    if not 0 < args.split_ratio < 1:
        parser.error("split_ratio must be between 0 and 1 (exclusive).")

    # Call the split function with the provided arguments
    split_trajectory(
        args.file_path, args.split_ratio, args.seed, args.train_output, args.val_output
    )


if __name__ == "__main__":
    main()
