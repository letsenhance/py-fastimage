Small lib to determinate image size and format based on first few bytes

**API:**
- `IMAGE_HEADER_MIN_SIZE` - magic number, represents how many first bytes we need to be sure.
    in general, we need only about `40` bytes, but `jpeg`'s and `tiff`'s metadata can be really large. 
    For now `800kb` looks like enough.
- `ImageFormat` -  represents supported formats
- `bytes_to_size_fmt(bytes)` - reads format and size information

**Rotation Metadata Support:**
The library automatically handles rotation metadata for formats that support it:
- **JPEG**: EXIF orientation tags (orientations 1-8)
- **TIFF**: Orientation tags (tag 274)
- **HEIC/AVIF**: irot box in ISO BMFF structure

Dimensions are automatically swapped for 90° and 270° rotations (EXIF orientations 5, 6, 7, 8) 
to match the displayed orientation.

**Usage:**
```python
from fastimage import IMAGE_HEADER_MIN_SIZE, bytes_to_size_fmt

with open('123x45.png', mode='rb') as f:
    header = f.read(IMAGE_HEADER_MIN_SIZE)
    print(bytes_to_size_fmt(header))
    # (123, 45), 'png'
```

**Installation:**
`pip install git+https://github.com/letsenhance/py-fastimage.git`
