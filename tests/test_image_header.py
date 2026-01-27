import os
import unittest

from fastimage import IMAGE_HEADER_MIN_SIZE, bytes_to_size_fmt


class ImageHeaderTestCase(unittest.TestCase):

    def _read_file_header(self, filename, header_size=None):
        if header_size is None:
            header_size = IMAGE_HEADER_MIN_SIZE
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', filename)
        with open(file_path, mode='rb') as f:
            return f.read(header_size)

    def test_generic_png(self):
        self.assertEqual(((123, 45), 'png'),
                         bytes_to_size_fmt(self._read_file_header('123x45.png')))

    def test_generic_jpg(self):
        # jpeg vs jpg are the same
        # The reason for the different file extensions dates back to the early versions of Windows. The original
        # file extension for the Joint Photographic Expert Group File Format was ‘.jpeg’; however in Windows all
        # files required a three letter file extension. So, the file extension was shortened to ‘.jpg’. However,
        # Macintosh was not limited to three letter file extensions, so Mac users used ‘.jpeg’. Eventually, with
        # upgrades Windows also began to accept ‘.jpeg’. However, many users were already used to ‘.jpg’, so both
        # the three letter file extension and the four letter extension began to be commonly used, and still is.
        self.assertEqual(((123, 45), 'jpg'),
                         bytes_to_size_fmt(self._read_file_header('123x45.jpeg')))

    def test_generic_gif(self):
        self.assertEqual(((123, 45), 'gif'),
                         bytes_to_size_fmt(self._read_file_header('123x45.gif')))

    def test_generic_webp(self):
        self.assertEqual(((123, 45), 'webp'),
                         bytes_to_size_fmt(self._read_file_header('123x45_vp8.webp')))
        # todo: discuss: support webp with vp8l and vp8x bitstream
        # self.assertEqual(((123, 45), 'webp',), bytes_to_size_fmt(self._read_file_header('123x45_vp8l.webp')))
        # self.assertEqual(((123, 45), 'webp',), bytes_to_size_fmt(self._read_file_header('123x45_vp8x.webp')))

    def test_generic_bmp(self):
        self.assertEqual(((123, 45), 'bmp'),
                         bytes_to_size_fmt(self._read_file_header('123x45.bmp')))
        self.assertEqual(((123, 45), 'bmp'),
                         bytes_to_size_fmt(self._read_file_header('123x45_compress.bmp'))
        )
        self.assertEqual(((123, 45), 'bmp'),
                         bytes_to_size_fmt(self._read_file_header('123x45_flip_row.bmp'))
        )
        self.assertEqual(((123, 45), 'bmp'),
                         bytes_to_size_fmt(self._read_file_header('123x45_os2.bmp')))

    def test_generic_tif(self):
        self.assertEqual(((123, 45), 'tif'),
                         bytes_to_size_fmt(self._read_file_header('123x45.tif')))
        self.assertEqual(((123, 45), 'tif'),
                         bytes_to_size_fmt(self._read_file_header('123x45_lzw.tif')))
        self.assertEqual(((123, 45), 'tif'),
                         bytes_to_size_fmt(self._read_file_header('123x45_zip.tif')))
        self.assertEqual(((123, 45), 'tif',),
                         bytes_to_size_fmt(self._read_file_header('123x45_mac_byte_order.tif')))

    # todo: discuss: support heic format
    # def test_generic_heic(self):
    #     # iphone photo format
    #     self.assertEqual(((123, 45), 'heic',), bytes_to_size_fmt(self._read_file_header('123x45.heic')))

    def test_wrong_jpg_size_dle_358(self):
        # occurs on small and large jpg images, with some specific info in header
        self.assertEqual(((512, 384), 'jpg'),
                         bytes_to_size_fmt(self._read_file_header('dle_358_jpg_bad_size.jpg')))

    def test_wrong_jpg_bad_metadata(self):
        # occurs on small and large jpg images, with some specific info in header
        self.assertEqual(((3089, 2184), 'jpg'),
                         bytes_to_size_fmt(self._read_file_header('1274-crop_bad_metadata.jpg')))
        self.assertEqual(((4096, 4096), 'jpg'),
                         bytes_to_size_fmt(self._read_file_header('large_metadata.jpg')))  # 749kb of metadata

    def test_generic_avif(self):
        self.assertEqual(((123, 45), 'avif'),
                         bytes_to_size_fmt(self._read_file_header('123x45.avif')))
        self.assertEqual(((123, 45), 'avif'),
                         bytes_to_size_fmt(self._read_file_header('123x45_compress.avif')))

    def test_jpeg_exif_orientation(self):
        """Test JPEG with EXIF orientation tags"""
        import struct
        from io import BytesIO

        def create_jpeg_with_orientation(width, height, orientation):
            """Create a minimal JPEG with EXIF orientation tag"""
            buf = BytesIO()
            buf.write(b'\xff\xd8')  # SOI
            buf.write(b'\xff\xe1')  # APP1
            
            exif_data = BytesIO()
            exif_data.write(b'Exif\x00\x00')
            exif_data.write(b'II')  # little-endian
            exif_data.write(struct.pack('<H', 42))
            exif_data.write(struct.pack('<I', 8))
            exif_data.write(struct.pack('<H', 1))  # 1 IFD entry
            exif_data.write(struct.pack('<H', 0x0112))  # orientation tag
            exif_data.write(struct.pack('<H', 3))  # SHORT type
            exif_data.write(struct.pack('<I', 1))  # count
            exif_data.write(struct.pack('<H', orientation))
            exif_data.write(struct.pack('<H', 0))
            exif_data.write(struct.pack('<I', 0))
            
            exif_bytes = exif_data.getvalue()
            buf.write(struct.pack('>H', len(exif_bytes) + 2))
            buf.write(exif_bytes)
            
            buf.write(b'\xff\xc0')  # SOF0
            buf.write(struct.pack('>H', 17))
            buf.write(b'\x08')
            buf.write(struct.pack('>H', height))
            buf.write(struct.pack('>H', width))
            buf.write(b'\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01')
            buf.write(b'\xff\xda')  # SOS
            
            return buf.getvalue()

        # Test orientations 1-4 (no dimension swap)
        for orientation in range(1, 5):
            data = create_jpeg_with_orientation(100, 200, orientation)
            self.assertEqual(((100, 200), 'jpg'), bytes_to_size_fmt(data))

        # Test orientations 5-8 (dimensions swapped)
        for orientation in range(5, 9):
            data = create_jpeg_with_orientation(100, 200, orientation)
            self.assertEqual(((200, 100), 'jpg'), bytes_to_size_fmt(data))

    def test_jpeg_exif_after_sof(self):
        """Test JPEG with EXIF APP1 appearing AFTER SOF marker (edge case)"""
        import struct
        from io import BytesIO
        
        # Create JPEG with SOF BEFORE APP1 - ensures we continue scanning
        buf = BytesIO()
        buf.write(b'\xff\xd8')  # SOI
        
        # First comes SOF0 (with dimensions)
        buf.write(b'\xff\xc0')  # SOF0
        buf.write(struct.pack('>H', 17))
        buf.write(b'\x08')
        buf.write(struct.pack('>HH', 200, 100))  # height=200, width=100
        buf.write(b'\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01')
        
        # NOW comes APP1 with orientation=6 (should swap dimensions)
        buf.write(b'\xff\xe1')  # APP1
        exif_data = BytesIO()
        exif_data.write(b'Exif\x00\x00')
        exif_data.write(b'II')  # little-endian
        exif_data.write(struct.pack('<H', 42))
        exif_data.write(struct.pack('<I', 8))
        exif_data.write(struct.pack('<H', 1))
        exif_data.write(struct.pack('<H', 0x0112))
        exif_data.write(struct.pack('<H', 3))
        exif_data.write(struct.pack('<I', 1))
        exif_data.write(struct.pack('<H', 6))  # orientation = 6
        exif_data.write(struct.pack('<H', 0))
        exif_data.write(struct.pack('<I', 0))
        exif_bytes = exif_data.getvalue()
        buf.write(struct.pack('>H', len(exif_bytes) + 2))
        buf.write(exif_bytes)
        
        buf.write(b'\xff\xda')  # SOS
        
        result = bytes_to_size_fmt(buf.getvalue())
        # Should swap dimensions even though APP1 came after SOF
        self.assertEqual(((200, 100), 'jpg'), result)

    def test_tiff_orientation(self):
        """Test TIFF with orientation tags"""
        import struct
        from io import BytesIO

        def create_tiff_with_orientation(width, height, orientation):
            """Create a minimal TIFF with orientation tag"""
            buf = BytesIO()
            buf.write(b'II')  # little-endian
            buf.write(struct.pack('<H', 42))
            buf.write(struct.pack('<I', 8))
            buf.write(struct.pack('<H', 3))  # 3 entries
            
            # Width
            buf.write(struct.pack('<H', 256))
            buf.write(struct.pack('<H', 4))
            buf.write(struct.pack('<I', 1))
            buf.write(struct.pack('<I', width))
            
            # Height
            buf.write(struct.pack('<H', 257))
            buf.write(struct.pack('<H', 4))
            buf.write(struct.pack('<I', 1))
            buf.write(struct.pack('<I', height))
            
            # Orientation
            buf.write(struct.pack('<H', 274))
            buf.write(struct.pack('<H', 3))
            buf.write(struct.pack('<I', 1))
            buf.write(struct.pack('<H', orientation))
            buf.write(struct.pack('<H', 0))
            
            buf.write(struct.pack('<I', 0))
            return buf.getvalue()

        # Test orientations 1-4 (no dimension swap)
        for orientation in range(1, 5):
            data = create_tiff_with_orientation(100, 200, orientation)
            self.assertEqual(((100, 200), 'tif'), bytes_to_size_fmt(data))

        # Test orientations 5-8 (dimensions swapped)
        for orientation in range(5, 9):
            data = create_tiff_with_orientation(100, 200, orientation)
            self.assertEqual(((200, 100), 'tif'), bytes_to_size_fmt(data))

    def test_jpeg_exif_fail_tolerance(self):
        """Test JPEG EXIF parsing handles malformed data gracefully"""
        import struct
        from io import BytesIO

        # Test 1: JPEG with truncated EXIF (pad to ≥24 bytes so it reaches JPEG parser)
        buf = BytesIO()
        buf.write(b'\xff\xd8\xff\xe1\x00\x0cExif\x00\x00II')
        buf.write(b'\x00' * 10)  # padding to reach 24 bytes minimum
        result = bytes_to_size_fmt(buf.getvalue())
        self.assertEqual(result[1], 'jpg')  # should detect format even with truncated EXIF

        # Test 2: JPEG with invalid byte order but valid SOF
        buf = BytesIO()
        buf.write(b'\xff\xd8\xff\xe1')
        buf.write(struct.pack('>H', 30))
        buf.write(b'Exif\x00\x00XX')  # invalid byte order
        buf.write(b'\x00' * 20)  # padding
        buf.write(b'\xff\xc0\x00\x11\x08')
        buf.write(struct.pack('>HH', 100, 50))
        buf.write(b'\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xda')
        result = bytes_to_size_fmt(buf.getvalue())
        self.assertEqual(result, ((50, 100), 'jpg'))  # should return dims with orientation=1

        # Test 3: JPEG with orientation value out of range
        buf = BytesIO()
        buf.write(b'\xff\xd8\xff\xe1')
        exif_data = BytesIO()
        exif_data.write(b'Exif\x00\x00II')
        exif_data.write(struct.pack('<H', 42))
        exif_data.write(struct.pack('<I', 8))
        exif_data.write(struct.pack('<H', 1))  # 1 entry
        exif_data.write(struct.pack('<HHIHH', 0x0112, 3, 1, 99, 0))  # invalid orientation, 12-byte IFD entry
        exif_data.write(struct.pack('<I', 0))
        exif_bytes = exif_data.getvalue()
        buf.write(struct.pack('>H', len(exif_bytes) + 2))
        buf.write(exif_bytes)
        buf.write(b'\xff\xc0\x00\x11\x08')
        buf.write(struct.pack('>HH', 100, 50))
        buf.write(b'\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xda')
        result = bytes_to_size_fmt(buf.getvalue())
        self.assertEqual(result, ((50, 100), 'jpg'))  # invalid orientation ignored

    def test_tiff_orientation_fail_tolerance(self):
        """Test TIFF orientation parsing handles malformed data gracefully"""
        import struct
        from io import BytesIO

        # Test 1: TIFF with orientation value out of range
        buf = BytesIO()
        buf.write(b'II')
        buf.write(struct.pack('<H', 42))
        buf.write(struct.pack('<I', 8))
        buf.write(struct.pack('<H', 3))  # 3 entries
        buf.write(struct.pack('<HHII', 256, 4, 1, 100))  # width
        buf.write(struct.pack('<HHII', 257, 4, 1, 50))   # height
        buf.write(struct.pack('<HHIHH', 274, 3, 1, 999, 0))  # invalid orientation
        buf.write(struct.pack('<I', 0))
        result = bytes_to_size_fmt(buf.getvalue())
        self.assertEqual(result, ((100, 50), 'tif'))  # invalid orientation ignored

        # Test 2: TIFF with truncated data (pad to ≥24 bytes so it reaches TIFF parser)
        buf = BytesIO()
        buf.write(b'II\x2a\x00\x08\x00\x00\x00\x03\x00')  # claims 3 entries but truncated
        buf.write(b'\x00' * 14)  # padding to reach 24 bytes minimum
        result = bytes_to_size_fmt(buf.getvalue())
        self.assertEqual(result, (None, 'tif'))  # should detect format with truncated IFD
