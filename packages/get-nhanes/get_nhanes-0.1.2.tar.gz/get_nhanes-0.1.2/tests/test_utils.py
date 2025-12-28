
import unittest
import pandas as pd
from get_nhanes.utils.getMetricsConvenient import sort_by_seqn

class TestUtils(unittest.TestCase):
    def test_sort_by_seqn_numeric(self):
        """Test sorting when seqn contains numeric prefixes"""
        data = {
            'seqn': ["100_2000", "2_2000", "20_2000", "5_2000"]
        }
        df = pd.DataFrame(data)
        
        sorted_df = sort_by_seqn(df)
        
        # Expected order: 2, 5, 20, 100
        expected_seqn = ["2_2000", "5_2000", "20_2000", "100_2000"]
        self.assertEqual(sorted_df['seqn'].tolist(), expected_seqn)

    def test_sort_by_seqn_fallback(self):
        """Test fallback to alphabetical sorting for non-standard formats"""
        data = {
            'seqn': ["b_2000", "a_2000", "c_2000"]
        }
        df = pd.DataFrame(data)
        
        sorted_df = sort_by_seqn(df)
        
        expected_seqn = ["a_2000", "b_2000", "c_2000"]
        self.assertEqual(sorted_df['seqn'].tolist(), expected_seqn)

    def test_sort_by_seqn_empty(self):
        """Test with empty DataFrame"""
        df = pd.DataFrame()
        sorted_df = sort_by_seqn(df)
        self.assertTrue(sorted_df.empty)

if __name__ == '__main__':
    unittest.main()
