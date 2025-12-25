import unittest
from heaserver.service.mimetypes import guess_mime_type


class GuessMimeTypeTest(unittest.TestCase):
    def test_text_plain(self):
        self.assertEqual('text/plain', guess_mime_type('TextFile.txt'))  # add assertion here

    def test_application_pdf(self):
        self.assertEqual('application/pdf', guess_mime_type('PDFFile.pdf'))  # add assertion here

    def test_no_extension(self):
        self.assertEqual('application/octet-stream', guess_mime_type('PDFFile'))  # add assertion here

    def test_no_filename(self):
        with self.assertRaises(TypeError):
            self.assertEqual('application/octet-stream', guess_mime_type(None))  # add assertion here

    def test_empty_string_for_filename(self):
        self.assertEqual('application/octet-stream', guess_mime_type(''))  # add assertion here


if __name__ == '__main__':
    unittest.main()
