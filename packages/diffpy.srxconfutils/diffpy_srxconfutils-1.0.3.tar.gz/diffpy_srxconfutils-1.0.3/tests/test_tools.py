import hashlib
import zlib

from diffpy.srxconfutils import tools


def test_get_md5(temp_file):
    file_path, content = temp_file
    expected_md5 = hashlib.md5(content).hexdigest()
    result = tools.get_md5(file_path)
    assert result == expected_md5


def test_get_crc32(temp_file):
    """Test the get_crc32 function."""
    file_path, content = temp_file
    val = tools.get_crc32(file_path)
    expected = zlib.crc32(content)
    assert val == expected
