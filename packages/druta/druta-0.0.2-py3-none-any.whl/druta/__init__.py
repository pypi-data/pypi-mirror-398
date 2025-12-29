from .video_dataset import DecordVideoDataset
from .video_dataset import DrutaDataset as Dataset
import os


def prep_dataset(
    video: str,
    save_as: str,
    batch_size: int = 1024,
    max_num_batches: int = None,
    video_decode_device: str = 'cpu',
    num_threads: int = 8
):
    """
    Compile a video file into a .druta format for fast loading.

    Args:
        video (str): Path to input video file (e.g., .mp4, .avi, .mkv)
        save_as (str): Path where the .druta file should be saved
        batch_size (int, optional): Number of frames to process at once. 
            Larger batches are faster but use more memory. Default: 1024
        max_num_batches (int, optional): Maximum number of batches to process.
            Useful for testing with a subset of frames. Default: None (process all)
        video_decode_device (str, optional): Device for video decoding. 
            Options: 'cpu' or 'cuda'. Default: 'cpu'
        num_threads (int, optional): Number of CPU threads for decoding. 
            Default: 8
    
    Returns:
        dict: Metadata dictionary with keys 'num_frames', 'height', 'width', 'channels'
    
    Example:
        >>> from druta import prepare, DrutaDataset
        >>> 
        >>> # Compile video to .druta format
        >>> metadata = prepare("my_video.mp4", "my_video.druta")
        >>> print(f"Prepared {metadata['num_frames']} frames at {metadata['height']}x{metadata['width']}")
        >>> 
        >>> # Load and use
        >>> dataset = DrutaDataset("my_video.druta")
        >>> frame = dataset[0]
    """
    # Create DecordVideoDataset
    dataset = DecordVideoDataset(
        filename=video,
        video_decode_device=video_decode_device,
        num_threads=num_threads
    )
    
    print(f"Compiling '{video}' to '{save_as}'...")
    print(f"Total frames: {len(dataset)}")
    
    # Compile to .druta format
    dataset.compile(
        save_as=save_as,
        batch_size=batch_size,
        max_num_batches=max_num_batches
    )
    
    # Read and return metadata
    metadata = Dataset.read_metadata(save_as)
    
    file_size_gb = os.path.getsize(save_as) / (1024**3)
    print(f"\033[1;94m[druta]\033[0m Saved \033[92m{save_as}\033[0m | Frames: \033[93m{metadata['num_frames']}\033[0m | Height: \033[93m{metadata['height']}\033[0m | Width: \033[93m{metadata['width']}\033[0m | Channels: \033[93m{metadata['channels']}\033[0m | Size: \033[93m{file_size_gb:.2f} GB\033[0m")
    
    return metadata