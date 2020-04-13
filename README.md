Small lib to determinate image size and format based on first few bytes

**API:**
- `IMAGE_HEADER_MIN_SIZE` - magic number, represents how many first bytes we need to be sure.
    in general, we need only about `40` bytes, but `jpeg`'s and `tiff`'s metadata can be really large. 
    For now `384kb` looks like enough.
- `ImageFormat` -  represents supported formats
- `bytes_to_size_fmt(bytes)` - reads format and size information

**Usage:**
```python
from fastimage import IMAGE_HEADER_MIN_SIZE, bytes_to_size_fmt

with open('123x45.png', mode='rb') as f:
    header = f.read(IMAGE_HEADER_MIN_SIZE)
    print(bytes_to_size_fmt(header))
    # (123, 45), 'png'
```

**Installation:**
`pip install git+ssh://git@gitlab.com/letsenhance/py-fastimage.git`
- or for specific branch `pip install git+ssh://git@gitlab.com/letsenhance/py-fastimage.git@DLE-600-basic-setup`
