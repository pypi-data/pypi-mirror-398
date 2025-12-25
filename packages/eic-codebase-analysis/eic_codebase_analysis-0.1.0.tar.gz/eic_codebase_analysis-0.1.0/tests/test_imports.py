import unittest
import sys
import os

# Add src to sys.path to simulate installation
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import eic_codebase_analysis

class TestImports(unittest.TestCase):
    def test_imports(self):
        self.assertTrue(hasattr(eic_codebase_analysis, 'generate_detailed_markdown'))
        self.assertTrue(hasattr(eic_codebase_analysis, 'generate_repository_structure_markdown'))
        self.assertTrue(hasattr(eic_codebase_analysis, 'generate_file_metadata_markdown'))
        self.assertTrue(hasattr(eic_codebase_analysis, 'generate_and_write_hierarchical_metadata'))

if __name__ == '__main__':
    unittest.main()
