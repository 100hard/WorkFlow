import unittest
             from unittest.mock import patch
             from joke_cli import get_random_joke
             
             class TestJokeCli(unittest.TestCase):
                 @patch('requests.get')
                 def test_main(self, mock_get):
                     # Mock the API call to return a specific response
                     mock_response = {'setup': 'Why was the math book sad?', 'punchline': 'Because it had too many problems.'}
                     mock_get.return_value = mock_response
                     
                     # Run the main function and check that it runs without errors
                     self.assertIsNone(get_random_joke())
                     
                 def test_output_format(self):
                     # Test the output format of the joke
                     joke = get_random_joke()
                     self.assertEqual(joke, 'Why was the math book sad?\nBecause it had too many problems.')