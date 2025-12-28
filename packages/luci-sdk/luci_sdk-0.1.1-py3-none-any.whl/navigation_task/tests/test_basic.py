"""
Basic tests for navigation task
"""

import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from question_templates import QuestionBank


class TestQuestionBank(unittest.TestCase):

    def test_spatial_questions(self):
        questions = QuestionBank.get_spatial_questions()
        self.assertIn("mcq", questions)
        self.assertIn("open", questions)
        self.assertGreater(len(questions["mcq"]), 0)

    def test_all_questions(self):
        all_q = QuestionBank.get_all_questions()
        expected_categories = ["spatial", "temporal", "object", "navigation"]
        for category in expected_categories:
            self.assertIn(category, all_q)


if __name__ == "__main__":
    unittest.main()