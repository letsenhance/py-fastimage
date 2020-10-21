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
