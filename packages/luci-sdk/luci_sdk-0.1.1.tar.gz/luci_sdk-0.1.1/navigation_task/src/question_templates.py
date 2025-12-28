"""
Question templates for egocentric navigation video analysis
"""


class QuestionBank:
    """Predefined questions for navigation video analysis"""

    @staticmethod
    def get_spatial_questions():
        return {
            "mcq": [
                {
                    "question": "What direction does the person move?",
                    "options": ["Forward", "Backward", "Left", "Right"]
                },
                {
                    "question": "What is the spatial layout?",
                    "options": ["Narrow corridor", "Wide open space", "Curved path", "Multiple pathways"]
                }
            ],
            "open": [
                "Describe the spatial layout of the environment.",
                "How does the person's spatial position change?"
            ]
        }

    @staticmethod
    def get_temporal_questions():
        return {
            "mcq": [
                {
                    "question": "What happens first in the video?",
                    "options": ["Person starts walking", "Person changes direction", "Person stops", "Person encounters obstacle"]
                },
                {
                    "question": "How does movement speed change?",
                    "options": ["Constant speed", "Speeds up", "Slows down", "Variable speed"]
                }
            ],
            "open": [
                "Describe the sequence of movements.",
                "How does behavior change over time?"
            ]
        }

    @staticmethod
    def get_object_questions():
        return {
            "mcq": [
                {
                    "question": "What type of environment is shown?",
                    "options": ["Indoor hallway", "Outdoor street", "Park area", "Parking lot"]
                },
                {
                    "question": "What is the primary surface?",
                    "options": ["Concrete/paved", "Carpet/soft", "Grass/natural", "Wood/tile"]
                }
            ],
            "open": [
                "What landmarks are visible?",
                "Describe architectural features."
            ]
        }

    @staticmethod
    def get_navigation_questions():
        return {
            "open": [
                "Give step-by-step navigation instructions.",
                "Describe the route for someone to follow.",
                "What landmarks should someone look for?"
            ]
        }

    @staticmethod
    def get_all_questions():
        return {
            "spatial": QuestionBank.get_spatial_questions(),
            "temporal": QuestionBank.get_temporal_questions(),
            "object": QuestionBank.get_object_questions(),
            "navigation": QuestionBank.get_navigation_questions()
        }