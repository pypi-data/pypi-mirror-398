#!/usr/bin/env python3
"""
Universal Video Analysis Script
Works with any task configuration - no task-specific code needed
"""

import sys
import os
import json
from video_qa import NavigationVideoQA

def main():
    """Universal analysis that works with any task"""
    if len(sys.argv) < 5:
        print("Usage: python universal_analysis.py <questions_file> <video_file> <model_path> <fallback_model>")
        sys.exit(1)

    questions_file = sys.argv[1]
    video_file = sys.argv[2]
    model_path = sys.argv[3]
    fallback_model = sys.argv[4]

    # Check if files exist
    if not os.path.exists(questions_file):
        print(f"Error: Questions file not found: {questions_file}")
        sys.exit(1)

    if not os.path.exists(video_file):
        print(f"Error: Video file not found: {video_file}")
        sys.exit(1)

    # Load questions
    try:
        with open(questions_file, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading questions: {e}")
        sys.exit(1)

    # Initialize QA system with provided model path and fallback
    try:
        if os.path.exists(model_path):
            qa = NavigationVideoQA(model_path)
        else:
            print(f"Warning: Model path not found: {model_path}")
            print(f"Falling back to: {fallback_model}")
            qa = NavigationVideoQA(fallback_model)
    except Exception as e:
        print(f"Error loading model: {e}")
        try:
            print(f"Trying fallback model: {fallback_model}")
            qa = NavigationVideoQA(fallback_model)
        except Exception as e2:
            print(f"Error loading fallback model: {e2}")
            sys.exit(1)

    # Process all questions
    results = []
    task_name = config.get("task_info", {}).get("task_name", "unknown")

    for q in config.get("questions", []):
        try:
            result = qa.ask_question(video_file, q["question"], q["options"])
            result["question_id"] = q["id"]
            result["category"] = q.get("category", "general")
            results.append(result)
        except Exception as e:
            print(f"Error processing question {q.get('id', '?')}: {e}")
            results.append({
                "question_id": q.get("id", 0),
                "question": q["question"],
                "error": str(e)
            })

    # Output results as JSON
    output = {
        "task": task_name,
        "video": video_file,
        "total_questions": len(config.get("questions", [])),
        "successful_answers": len([r for r in results if "error" not in r]),
        "results": results
    }

    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()