# coding: utf-8

# based on fastimage lib
# removed ImageCollector code
# fix some jpg issues
# take a look at https://github.com/bmuller/fastimage/blob/master/fastimage/detect.py (+-BMP, +-TIFF)
#                https://github.com/scardine/image_size/blob/master/get_image_size.py (+TIFF, -WEBP, +ICO)
#                https://github.com/shibukawa/imagesize_py/blob/master/imagesize.py (+tiff, reads dpi)
import struct
import logging
from io import BytesIO
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

__all__ = (
    'IMAGE_HEADER_MIN_SIZE',
    'bytes_to_size_fmt',
    'ImageFormat',
)

IMAGE_HEADER_MIN_SIZE = 800 * 1024  # 800kb, some jpg images have huge meta info, should be enough
# gif - 10b
# jpg - ?? looks like 256b is enough
#   Each APPN data area has a length field that is 2 bytes, so 65536 would hold the biggest one.
#   If you are just worried about the EXIF data, it would be a bit less.
#   http://www.fileformat.info/format/jpeg/egff.htm There are at most 16 different APPN markers in
#   a single file. I don't think they can be repeated, so 16*65K should be the theoretical max.
#   ----
#   So, at max, data before image size block may take up to 16*65kb = 1040 * 1024 bytes + few bytes for data
#   1100kb should be enough
# png - 24b
# webp - 31b
# tiff - ??
# bmp - 26b


class ImageFormat:  # not enum to keep all parent code as is
    gif = 'gif'
    jpg = 'jpg'
    png = 'png'
    tif = 'tif'
    bmp = 'bmp'
    webp = 'webp'
    avif = 'avif'
    heif = 'heif'


def gif(bytes):
    try:
        return struct.unpack('<HH', bytes[6:10])
    except struct.error:
        return None


def jpeg(bytes):
    fhandle = BytesIO(bytes)
    fhandle.seek(0)
    fhandle.read(2)
    b = fhandle.read(1)
    try:
        while b and ord(b) != 0xDA:
            while ord(b) != 0xFF:
                b = fhandle.read(1)
            while ord(b) == 0xFF:
                b = fhandle.read(1)
            if 0xC0 <= ord(b) <= 0xC3:
                fhandle.read(3)
                h, w = struct.unpack('>HH', fhandle.read(4))
                break
            else:
                fhandle.read(int(struct.unpack('>H', fhandle.read(2))[0]) - 2)
            b = fhandle.read(1)
        return int(w), int(h)
    except Exception:
        return None


def webp(bytes):
    # pylint: disable=invalid-name
    vp8 = bytes[12:16]
    if vp8 == b'VP8 ' and len(bytes) > 30:
        width, height = struct.unpack('<HH', bytes[26:30])
        return width & 0x3fff, height & 0x3fff
    elif vp8 == b'VP8L' and len(bytes) > 25:
        b1, b2, b3, b4 = bytes[21:25]
        width = 1 + (((b2 & 0x3f) << 8) | b1)
        height = 1 + (((b4 & 0xF) << 10) | (b3 << 2) | ((b2 & 0xC0) >> 6))
        return width, height
    elif vp8 == b'VP8X' and len(bytes) > 30:
        b1, b2, b3, b4, b5, b6 = struct.unpack('BBBBBB', bytes[24:30])
        width = 1 + b1 + (b2 << 8) + (b3 << 16)
        height = 1 + b4 + (b5 << 8) + (b6 << 16)
        return width, height
    return None


def png(bytes):
    try:
        check = struct.unpack('>i', bytes[4:8])[0]
        if check != 0x0d0a1a0a:
            return None
        return struct.unpack('>ii', bytes[16:24])
    except struct.error:
        return None


def bmp(bytes):
    # source: https://github.com/scardine/image_size/blob/master/get_image_size.py
    try:
        header_size = struct.unpack('<I', bytes[14:18])[0]
        if header_size == 12:
            w, h = struct.unpack('<HH', bytes[18:22])
            return int(w), int(h)
        elif header_size >= 40:
            w, h = struct.unpack('<ii', bytes[18:26])
            # as h is negative when stored upside down
            return int(w), abs(int(h))
        else:
            return None
    except struct.error:
        return None


def tiff(bytes):
    # source: https://github.com/scardine/image_size/blob/master/get_image_size.py
    try:
        # Standard TIFF, big- or little-endian
        # BigTIFF and other different but TIFF-like formats are not supported currently
        byteOrder = bytes[:2]
        boChar = '>' if byteOrder == b'MM' else '<'
        # maps TIFF type id to size (in bytes)
        # and python format char for struct
        tiffTypes = {
            1: (1, boChar + 'B'),  # BYTE
            2: (1, boChar + 'c'),  # ASCII
            3: (2, boChar + 'H'),  # SHORT
            4: (4, boChar + 'L'),  # LONG
            5: (8, boChar + 'LL'),  # RATIONAL
            6: (1, boChar + 'b'),  # SBYTE
            7: (1, boChar + 'c'),  # UNDEFINED
            8: (2, boChar + 'h'),  # SSHORT
            9: (4, boChar + 'l'),  # SLONG
            10: (8, boChar + 'll'),  # SRATIONAL
            11: (4, boChar + 'f'),  # FLOAT
            12: (8, boChar + 'd')  # DOUBLE
        }
        ifdOffset = struct.unpack(boChar + 'L', bytes[4:8])[0]
        input = BytesIO(bytes)
        countSize = 2
        input.seek(ifdOffset)
        ec = input.read(countSize)
        ifdEntryCount = struct.unpack(boChar + 'H', ec)[0]
        # 2 bytes: TagId + 2 bytes: type + 4 bytes: count of values + 4
        # bytes: value offset
        ifdEntrySize = 12
        width = None
        height = None
        for i in range(ifdEntryCount):
            entryOffset = ifdOffset + countSize + i * ifdEntrySize
            input.seek(entryOffset)
            tag = input.read(2)
            tag = struct.unpack(boChar + 'H', tag)[0]
            if tag == 256 or tag == 257:
                # if type indicates that value fits into 4 bytes, value
                # offset is not an offset but value itself
                type = input.read(2)
                type = struct.unpack(boChar + 'H', type)[0]
                if type not in tiffTypes:
                    logger.warning('Unknown TIFF field type: %s ' % (str(type), ))
                    return None
                typeSize = tiffTypes[type][0]
                typeChar = tiffTypes[type][1]
                input.seek(entryOffset + 8)
                value = input.read(typeSize)
                value = int(struct.unpack(typeChar, value)[0])
                if tag == 256:
                    width = value
                else:
                    height = value
            if width is not None and width > -1 and height is not None and height > -1:
                return width, height
    except struct.error:
        pass
    return None


class IsoBmff:
    # HEIC/AVIF are a special case of the general ISO_BMFF format, in which all data is encapsulated in typed boxes,
    # with a mandatory ftyp box that is used to indicate particular file types. Is composed of nested "boxes". Each
    # box has a header composed of
    # - Size (32 bit integer)
    # - Box type (4 chars)
    # - Extended size: only if size === 1, the type field is followed by 64 bit integer of extended size
    # - Payload: Type-dependent
    # ____________________________________________________
    # Translated from Ruby to Python for Letsenhance/Claid
    #
    # Ruby implementation
    #   for HEIC: https://github.com/sdsykes/fastimage/pull/125/files
    #   for AVIF: https://github.com/sdsykes/fastimage/pull/135/files
    #
    # ISOBMFF Box Structure Viewer: https://gpac.github.io/mp4box.js/test/filereader.html

    def __init__(self, bytes):
        self.bytes = bytes
        self.rotation = 0
        self.primary_box = None
        self.ipma_boxes = []
        self.ispe_boxes = []
        self.final_size = None

        self.finish_processing = False
        self.input = BytesIO(self.bytes)

    @staticmethod
    def get_widht_and_height(bytes):
        iso_bmff = IsoBmff(bytes=bytes)
        iso_bmff.read_boxes()
        size = iso_bmff.final_size

        if iso_bmff.rotation in {90, 270}:
            size.reverse()

        return size or None

    def read_uint8(self):
        return struct.unpack('B', self.input.read(1))[0]

    def read_uint16(self):
        return struct.unpack('!H', self.input.read(2))[0]

    def read_uint32(self):
        return struct.unpack('!I', self.input.read(4))[0]

    def read_box_header(self):
        size = self.read_uint32()
        type = self.input.read(4)

        return [type, size - 8]

    def handle_irot_box(self):
        self.rotation = (self.read_uint8() & 0x3) * 90

    def handle_meta_box(self, box_size):
        if box_size < 4:
            self.finish_processing = True
            return

        self.input.read(4)
        self.read_boxes(box_size=box_size-4)
        if not self.primary_box:
            self.finish_processing = True
            return

        primary_indices = []
        for ipma_box in self.ipma_boxes:
            if ipma_box['id'] == self.primary_box:
                primary_indices.append(ipma_box['property_index'])

        ispe_box = None
        for box in self.ispe_boxes:
            if box['index'] in primary_indices:
                ispe_box = box

        if ispe_box:
            self.final_size = ispe_box['size']

        self.finish_processing = True

    def handle_hdlr_box(self, box_size):
        if box_size < 12:
            self.finish_processing = True
            return

        data = self.input.read(box_size)
        if data[8:12] != b'pict':
            self.finish_processing = True

    def handle_pitm_box(self, box_size):
        data = self.input.read(box_size)
        self.primary_box = struct.unpack('!H', data[4:6])[0]

    def handle_ipma_box(self, box_size):
        self.input.read(3)

        flags3 = self.read_uint8()
        entries_count = self.read_uint32()

        for _ in range(entries_count):
            id = self.read_uint16()
            essen_count = self.read_uint8()

            for __ in range(essen_count):
                property_index = self.read_uint8() & 0x7F

                if flags3 & 1 == 1:
                    property_index = (property_index << 7) + self.read_uint8()

                self.ipma_boxes.append({'id': id, 'property_index': property_index - 1})

    def handle_ispe_box(self, box_size, index):
        if box_size < 12:
            self.finish_processing = True
            return

        data = self.input.read(box_size)
        width = struct.unpack('!I', data[4:8])[0]
        height = struct.unpack('!I', data[8:12])[0]
        self.ispe_boxes.append({'index': index, 'size': (width, height)})

    def read_boxes(self, box_size=None):
        index = 0

        end_pos = None if box_size is None else self.input.tell() + box_size

        while True:
            if end_pos and self.input.tell() >= end_pos:
                return

            if self.finish_processing:
                return

            box_type, box_size = self.read_box_header()
            if box_type == b'meta':
                self.handle_meta_box(box_size)
            elif box_type == b'pitm':
                self.handle_pitm_box(box_size)
            elif box_type == b'ipma':
                self.handle_ipma_box(box_size)
            elif box_type == b'hdlr':
                self.handle_hdlr_box(box_size)
            elif box_type in (b'iprp', b'ipco'):
                self.read_boxes(box_size)
            elif box_type == b'irot':
                self.handle_irot_box()
            elif box_type == b'ispe':
                self.handle_ispe_box(box_size, index)
            elif box_type == b'mdat':
                self.finish_processing = True
                return
            else:
                self.input.read(box_size)

            index += 1


def bytes_to_size_fmt(bytes) -> Tuple[Optional[Tuple[int, int]], Optional[str]]:
    """
    Get image file size and type based on header, for best result use whole file.

    In some edge cases: (e.g. large metadata) we can determinate only format without image size info
    :param bytes: header or whole image
    :return:
        ((w,h), format) - known image
        (None, format) - can not determinate size info
        (None, None) - unknown image format
    """
    result = None, None
    if len(bytes) < 24:
        return result

    peek = bytes[:2]
    if peek == b'GI':
        result = gif(bytes), ImageFormat.gif
    elif peek == b'\xff\xd8':
        result = jpeg(bytes), ImageFormat.jpg
    elif peek == b'\x89P':
        result = png(bytes), ImageFormat.png
    elif bytes[:4] in {b'II\052\000', b'MM\000\052'}:
        result = tiff(bytes), ImageFormat.tif
    elif peek == b'BM':
        result = bmp(bytes), ImageFormat.bmp
    elif peek == b'RI' and bytes[8:12] == b'WEBP':
        result = webp(bytes), ImageFormat.webp
    elif peek == b'\x00\x00':
        size = IsoBmff.get_widht_and_height(bytes=bytes)
        ftyp = bytes[4:12]
        if ftyp == b'ftypavif':
            result = size, ImageFormat.avif
        elif ftyp in {b'ftypheic', b'ftypmif1', b'ftypheix', b'ftyphevc', b'ftyphevx', b'ftypmsf1'}:
            result = size, ImageFormat.heif
        else:
            logger.warning("Can't determine image format of image in ISO_BMFF format, "
                           "unexpected 'ftyp' box at the 5th bytes: %s " % ftyp)
            result = size, None

    if result[0] is None and result[1] is not None:
        logger.warning("Can't read size info of %s image, first 256 bytes: %r " % (result[1], bytes[:256]))

    return result
