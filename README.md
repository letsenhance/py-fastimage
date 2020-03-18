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
1. add your ssh keys to ssh agent (ssh-add) 
2. `pip install git+ssh://git@gitlab.com/letsenhance/py-fastimage.git`
- or for specific branch `pip install git+ssh://git@gitlab.com/letsenhance/py-fastimage.git@DLE-600-basic-setup`

**CI:**
- `git config --global url."https://gitlab-ci-token:${CI_JOB_TOKEN}@gitlab.com/".insteadOf "ssh://git@gitlab.com/"`
- `pip install git+ssh://git@gitlab.com/letsenhance/py-fastimage.git`
In this way it will work on CI as https cloning, and locally as ssh cloning without extra manipulations.

Option 2. Https, works only within runner
- `echo -e "machine gitlab.com\nlogin gitlab-ci-token\npassword ${CI_JOB_TOKEN}" > ~/.netrc`
- `pip install git+https://gitlab-ci-token@gitlab.com/letsenhance/py-fastimage.git`
