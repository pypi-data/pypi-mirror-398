# druta (द्रुत)

A fast video dataset format for PyTorch (for when storage isn't a problem)


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