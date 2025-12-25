import unittest
import pathlib
from pylyr.crawler import Crawler


class CrawlerTest(unittest.TestCase):
    def test__similar(self):
        c = Crawler('The Flamingos', 'You, Me and the Sea')
        self.assertEqual(c._similar('You, Me, And The Sea', 
                                    '\n        The Flamingos\n'), True)

        # this requires a more complex approach (for in' ing mismatch)
        # see TODO.txt for verbose output
        #
        # c2 = Crawler('Haruomi Hosono', "Cosmic Surfin'")
        # self.assertEqual(c2._similar('コズミック・サーフィン (Cosmic Surfing)',
        #                             '\n        細野晴臣  (Haruomi Hosono)\n'),
        #                  True)

        c3 = Crawler('Dan Luke and the Raid', "Maybe It's the Drugs")
        self.assertEqual(c3._similar('Maybe It’s the Drugs', 
                         '\n        Dan Luke and The Raid\n'), True)

        c4 = Crawler('Chris Lake, Ragie Ban', 'Toxic')
        self.assertEqual(c4._similar('Toxic', 
             '\n        Chris Lake & Ragie Ban\n'), True)

        c5 = Crawler('of Montreal', 'Plateau Phase/No Careerism No Corruption')
        self.assertEqual(c5._similar('Plateau Phase/No Careerism No Corruption', 
             '\n        \u200bof Montreal\n'), True)


if __name__ == '__main__':
    unittest.main()
