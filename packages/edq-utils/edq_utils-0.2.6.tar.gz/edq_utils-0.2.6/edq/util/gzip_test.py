import os

import edq.testing.unittest

import edq.util.dirent
import edq.util.gzip

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(THIS_DIR, 'testdata', 'gzip')

class TestGzip(edq.testing.unittest.BaseTest):
    """ Test gzipping functionality. """

    def test_file_base(self):
        """ Test file-based operations. """

        text_contents = 'abc123'
        in_path = edq.util.dirent.get_temp_path('edq-testing=gzip-')
        edq.util.dirent.write_file(in_path, text_contents, newline = False)

        data = edq.util.gzip.compress_path(in_path)
        output = edq.util.gzip.uncompress_to_string(data)

        self.assertEqual(text_contents, output, 'Decompressed data does not match raw file data.')

    def test_file_base64(self):
        """ Test file-based operations using base64. """

        text_contents = 'abc123'
        in_path = edq.util.dirent.get_temp_path('edq-testing=gzip-')
        edq.util.dirent.write_file(in_path, text_contents, newline = False)

        data = edq.util.gzip.compress_path_as_base64(in_path)
        output = edq.util.gzip.uncompress_base64_to_string(data)

        self.assertEqual(text_contents, output, 'Decompressed data does not match raw file data.')
