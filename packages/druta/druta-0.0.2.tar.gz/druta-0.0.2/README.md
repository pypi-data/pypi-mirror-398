# druta (द्रुत)

A fast video dataset format for PyTorch (for when storage is cheap, but time is not)

```
pip install druta
```

```python
import druta

druta.prep_dataset(
    video="video.mp4",
    save_as="video.druta",
    num_threads=4,
)

dataset = druta.Dataset(
    filename="video.druta",
)

for i in range(len(dataset)):
    frame = dataset[i]
    ## (height, width, 3)
    print(f"Frame {i} shape: {frame.shape}")
```

## Why druta?
<p align="center">
    <img src="images/explainer.png" width="45%" style="display:inline-block;">
    <img src="images/decord_vs_druta_benchmark.png" width="45%" style="display:inline-block;">
</p>

When training a model on video data using something like decord, we end up performing the video decoding gymnastics thousands of times redundantly. Druta skips this redundancy by decoding the video once and storing it as a memory mapped file with raw `uint8` tensor data.

But there's no free lunch. The speedup comes at a cost of a massive disk-size, but this trade-off is well worth it for some folks. (The speed-tests were run on an M3 Max macbook pro on 2048 frames)

## Running tests

```
pytest -vvx --capture=no tests/
```