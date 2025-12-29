from druta.video_dataset import DecordVideoDataset, DrutaDataset
import pytest
import os

cache_dir = "./test_cache"

video_paths_by_resolution = {
    "1080p": "videos/sample_1080p.mp4",
    "720p": "videos/sample_720p.mp4",
    "360p": "videos/sample_360p.mp4",
}

resolution_to_shape_mapping = {
    "1080p": {
        "height": 1080,
        "width": 1920,
    },
    "720p": {
        "height": 720,
        "width": 1280,
    },
    "360p": {
        "height": 360,
        "width": 640,
    },
}


@pytest.mark.parametrize("resolution", ["1080p", "720p", "360p"])
@pytest.mark.parametrize("num_threads", [1, 4])
def test_decord_video_dataset(
    resolution: str,
    num_threads: int
):
    video_path = video_paths_by_resolution[resolution]
    dataset = DecordVideoDataset(
        filename=video_path,
        video_decode_device='cpu',
        num_threads=num_threads,
    )
    
    assert len(dataset) > 0, "Dataset length should be greater than 0."
    
    # Test random access
    for i in range(0, len(dataset), max(1, len(dataset) // 10)):
        frame = dataset[i]
        assert frame.ndim == 3, "Frame should have 3 dimensions (H, W, C)."
        assert frame.shape[2] == 3, "Frame should have 3 channels (C=3)."
        assert frame.shape[0] == resolution_to_shape_mapping[resolution]["height"], \
            f"Frame height should be {resolution_to_shape_mapping[resolution]['height']}."
        assert frame.shape[1] == resolution_to_shape_mapping[resolution]["width"], \
            f"Frame width should be {resolution_to_shape_mapping[resolution]['width']}."


@pytest.mark.parametrize("resolution", ["1080p", "720p", "360p"])
@pytest.mark.parametrize("num_threads", [1, 4])
def test_compile_and_load(resolution: str, num_threads: int):
    video_path = video_paths_by_resolution[resolution]
    
    # Create DecordVideoDataset
    dataset = DecordVideoDataset(
        filename=video_path,
        video_decode_device='cpu',
        num_threads=num_threads,
    )
    
    num_frames = len(dataset)
    assert num_frames > 0, "Dataset should have frames."
    
    # Ensure cache directory exists
    os.makedirs(cache_dir, exist_ok=True)
    
    # Compile to .druta format
    druta_path = os.path.join(cache_dir, f"test_output_{resolution}_threads{num_threads}.druta")
    dataset.compile(
        save_as=druta_path,
        batch_size=16,
        max_num_batches=None
    )
    
    assert os.path.exists(druta_path), "Compiled .druta file should exist."
    
    # Load DrutaDataset - no shape parameters needed anymore!
    druta_dataset = DrutaDataset(filename=druta_path)
    
    # Verify metadata was read correctly
    assert druta_dataset.num_frames == num_frames, \
        f"DrutaDataset num_frames ({druta_dataset.num_frames}) should match original ({num_frames})."
    assert druta_dataset.H == resolution_to_shape_mapping[resolution]["height"], \
        f"DrutaDataset height should be {resolution_to_shape_mapping[resolution]['height']}."
    assert druta_dataset.W == resolution_to_shape_mapping[resolution]["width"], \
        f"DrutaDataset width should be {resolution_to_shape_mapping[resolution]['width']}."
    assert druta_dataset.C == 3, "DrutaDataset channels should be 3."
    
    assert len(druta_dataset) == num_frames, "DrutaDataset length should match original dataset."
    
    # Test loading frames from compiled dataset
    for i in range(0, len(druta_dataset), max(1, len(druta_dataset) // 10)):
        frame = druta_dataset[i]
        assert frame.ndim == 3, "Frame should have 3 dimensions (H, W, C)."
        assert frame.shape[2] == 3, "Frame should have 3 channels (C=3)."
        assert frame.shape[0] == resolution_to_shape_mapping[resolution]["height"]
        assert frame.shape[1] == resolution_to_shape_mapping[resolution]["width"]
    
    # Verify frames match exactly between original and compiled dataset
    for i in range(0, len(dataset), max(1, len(dataset) // 10)):
        original_frame = dataset[i]
        compiled_frame = druta_dataset[i]
        assert (original_frame == compiled_frame).all(), \
            f"Frame {i} should match exactly between original and compiled dataset."
    
    # Cleanup
    if os.path.exists(druta_path):
        os.remove(druta_path)


@pytest.mark.parametrize("resolution", ["1080p", "720p", "360p"])
def test_metadata_reading(resolution: str):
    """Test the static metadata reading utility function."""
    video_path = video_paths_by_resolution[resolution]
    
    # Create and compile dataset
    dataset = DecordVideoDataset(
        filename=video_path,
        video_decode_device='cpu',
        num_threads=1,
    )
    
    os.makedirs(cache_dir, exist_ok=True)
    druta_path = os.path.join(cache_dir, f"test_metadata_{resolution}.druta")
    
    dataset.compile(
        save_as=druta_path,
        batch_size=16,
        max_num_batches=None
    )
    
    # Test static metadata reading without loading full dataset
    metadata = DrutaDataset.read_metadata(druta_path)
    
    assert metadata['num_frames'] == len(dataset), \
        f"Metadata num_frames should match dataset length."
    assert metadata['height'] == resolution_to_shape_mapping[resolution]["height"], \
        f"Metadata height should be {resolution_to_shape_mapping[resolution]['height']}."
    assert metadata['width'] == resolution_to_shape_mapping[resolution]["width"], \
        f"Metadata width should be {resolution_to_shape_mapping[resolution]['width']}."
    assert metadata['channels'] == 3, "Metadata channels should be 3."
    
    # Cleanup
    if os.path.exists(druta_path):
        os.remove(druta_path)