import decord
import os
import struct
from torchtyping import TensorType
from tqdm import tqdm
import torch
from torch.utils.data import Dataset

valid_devices = ['cpu', 'cuda']

# Metadata format: 4 integers (num_frames, height, width, channels) as 4-byte ints
METADATA_SIZE = 16  # 4 integers × 4 bytes each
METADATA_FORMAT = 'IIII'  # 4 unsigned integers


class DecordVideoDataset:
    def __init__(
        self,
        filename: str,
        video_decode_device: str = 'cpu',
        num_threads: int = 8,
    ):
        assert video_decode_device in valid_devices, \
            f"Invalid video_decode_device '{video_decode_device}'. Must be one of {valid_devices}."
        
        assert os.path.exists(filename), f"Video file '{filename}' does not exist."
        
        decord.bridge.set_bridge('torch')  # Makes get_batch() return torch.Tensor directly!

        self.video_path = filename
        self.ctx = decord.cpu() if video_decode_device == 'cpu' else decord.gpu(0)

        # Initialize VideoReader
        self.vr = decord.VideoReader(
            filename,
            ctx=self.ctx,
            num_threads=num_threads
        )
        self.total_frames = len(self.vr)

    def __len__(self):
        return self.total_frames

    def __getitem__(self, index) -> TensorType["H", "W", 3]:
        # Read single frame by index
        frame = self.vr[index]  # Shape: (H, W, C)
        return frame

    def compile(self, save_as: str, batch_size: int = 1024, max_num_batches: int = None):
        """
        Preprocess the video and save as a raw torch tensor file with metadata header.
        Format: [16-byte metadata header][raw frame data]
        Metadata: num_frames (4 bytes), height (4 bytes), width (4 bytes), channels (4 bytes)
        """
        
        print(f"Compiling video into tensor file: {self.video_path}")

        total_frames_to_save = self.total_frames
        if max_num_batches is not None:
            total_frames_to_save = min(total_frames_to_save, batch_size * max_num_batches)

        # Get shape from first frame
        sample = self.vr.get_batch([0])
        H, W, C = sample.shape[1:]

        # Write metadata header + frames
        with open(save_as, "wb") as f:
            # Write metadata header
            metadata = struct.pack(METADATA_FORMAT, total_frames_to_save, H, W, C)
            f.write(metadata)
            print(f"Written metadata: num_frames={total_frames_to_save}, H={H}, W={W}, C={C}")

            # Write frames sequentially
            for i, start in enumerate(tqdm(range(0, total_frames_to_save, batch_size), desc="Compiling frames")):
                end = min(start + batch_size, total_frames_to_save)
                indices = list(range(start, end))
                frames = self.vr.get_batch(indices)  # torch tensor (B,H,W,C)
                f.write(frames.cpu().numpy().tobytes())
                
                # After first batch, print expected final size
                if i == 0:
                    expected_final_size_gb = (METADATA_SIZE + total_frames_to_save * H * W * C) / (1024 * 1024 * 1024)
                    print(f"\033[92mExpected final size: {expected_final_size_gb:.3f} GB\033[0m")
        
        # Print final stats
        final_shape = (total_frames_to_save, H, W, C)
        final_size = os.path.getsize(save_as)
        final_size_gb = final_size / (1024 * 1024 * 1024)
        print(f"Final size: {final_size_gb:.3f} GB")

class DrutaDataset(Dataset):
    def __init__(
        self,
        filename: str,
        transform=None
    ):
        """
        Fast dataset reading from raw tensor file with embedded metadata.
        Automatically reads shape information from the file header.
        
        Args:
            filename (str): Path to .druta file with metadata header
            transform: Optional transform to apply to video clips
        """
        self.filename = filename
        self.transform = transform

        # Read metadata from file header
        with open(filename, 'rb') as f:
            metadata_bytes = f.read(METADATA_SIZE)
            self.num_frames, self.H, self.W, self.C = struct.unpack(METADATA_FORMAT, metadata_bytes)
            assert self.num_frames > 0, f"Number of frames must be positive but got: {self.num_frames}"
            assert self.H > 0 and self.W > 0 and self.C > 0, \
                f"Invalid frame dimensions: H={self.H}, W={self.W}, C={self.C}"
        
        # print(f"Loaded metadata: num_frames={self.num_frames}, H={self.H}, W={self.W}, C={self.C}")

        # Memory-map the entire file including metadata
        file_size = os.path.getsize(filename)
        total_elements = file_size  # Read entire file as bytes
        mapped_data = torch.from_file(
            filename, 
            dtype=torch.uint8,
            size=total_elements,
            shared=False
        )
        
        # Skip the metadata header and reshape
        self.all_frames = mapped_data[METADATA_SIZE:].view(self.num_frames, self.H, self.W, self.C)

    def __len__(self):
        return self.num_frames

    def __getitem__(self, index):
        frame = self.all_frames[index]

        if self.transform:
            frame = self.transform(frame)

        return frame
    
    @staticmethod
    def read_metadata(filename: str):
        """
        Utility function to read just the metadata without loading the full dataset.
        
        Returns:
            dict: Dictionary with keys 'num_frames', 'height', 'width', 'channels'
        """
        with open(filename, 'rb') as f:
            metadata_bytes = f.read(METADATA_SIZE)
            num_frames, height, width, channels = struct.unpack(METADATA_FORMAT, metadata_bytes)
        
        return {
            'num_frames': num_frames,
            'height': height,
            'width': width,
            'channels': channels
        }