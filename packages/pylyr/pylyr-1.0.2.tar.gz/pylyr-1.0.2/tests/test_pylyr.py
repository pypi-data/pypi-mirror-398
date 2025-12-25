import unittest
import pathlib
from pylyr import PyLyr


class PyLyrTest(unittest.TestCase):
    def test_lyrics_file(self):
        p = PyLyr('SingleWordArtist', 'SingleWordTitle')
        self.assertEqual(p.lyrics_file, pathlib.Path.home() / '.lyrics' /\
            'SingleWordArtist - SingleWordTitle.txt')


    def test_get_lyrics(self):
        p = PyLyr('SingleWordArtist', 'SingleWordTitle')
        p.lyrics_file = 'tests/data/SingleWordArtist - SingleWordTitle.txt'
        self.assertEqual(p.get_lyrics().strip(), 
            'SingleWordArtist - SingleWordTitle\
\n──────────────────────────────────\nlyrics')


if __name__ == '__main__':
    unittest.main()
