import unittest
from struct import pack
from pyaxml.arscobject import ARSC
from pyaxml.stringblocks import StringBlocks
from pyaxml.proto import axml_pb2
import os

test_dir = os.path.dirname(os.path.abspath(__file__))

class TestARSC(unittest.TestCase):
    def setUp(self):
        """Set up a basic ARSC instance with real axml_pb2 data."""

        

    def test_full_list_packages(self):
        """Test full list_packages metod
        """
        for filename in ["data/ARSC/example.arsc"]:
            ref = ""
            with open(os.path.join(test_dir, filename) + ".xml", "r") as f:
                ref = f.read() 
            with open(os.path.join(test_dir, filename), "rb") as f:
                # Read AXML
                axml, _ = ARSC.from_axml(f.read())
                xml = axml.list_packages()
                self.assertEqual(xml, ref, "resources not correctly decoded")
        


if __name__ == "__main__":
    unittest.main()
