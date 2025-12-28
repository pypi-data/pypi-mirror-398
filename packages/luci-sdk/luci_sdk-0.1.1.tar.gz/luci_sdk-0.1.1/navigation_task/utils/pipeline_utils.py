#!/usr/bin/env python3
"""
Pipeline utilities for video analysis tasks
"""

import os
import json
import glob
from datetime import datetime

def find_videos(video_dir, formats):
    """Find all video files in directory"""
    video_files = []
    for fmt in formats:
        pattern = os.path.join(video_dir, fmt)
        video_files.extend(glob.glob(pattern))
    return sorted(video_files)

def create_task_structure(task_dir, task_name, description):
    """Create task directory structure"""
    os.makedirs(task_dir, exist_ok=True)
    os.makedirs(os.path.join(task_dir, "videos"), exist_ok=True)
    os.makedirs(os.path.join(task_dir, "results"), exist_ok=True)

def create_questions_template(questions_file, task_name, description):
    """Create questions template file"""
    template = {
        "task_info": {
            "task_name": task_name,
            "description": description,
            "created": datetime.now().isoformat()
        },
        "questions": [
            {
                "id": 1,
                "category": "example",
                "question": "What is the main subject in the video?",
                "options": [
                    "Person",
                    "Animal",
                    "Vehicle",
                    "Building"
                ]
            },
            {
                "id": 2,
                "category": "example",
                "question": "What is the setting/environment?",
                "options": [
                    "Indoor",
                    "Outdoor",
                    "Mixed indoor/outdoor",
                    "Cannot determine"
                ]
            }
        ]
    }

    with open(questions_file, 'w') as f:
        json.dump(template, f, indent=2)

def generate_summary(task_name, results_dir, total_videos, success_count):
    """Generate task summary"""
    summary = {
        "task_name": task_name,
        "completion_time": datetime.now().isoformat(),
        "total_videos": total_videos,
        "successful_videos": success_count,
        "failed_videos": total_videos - success_count,
        "success_rate": f"{success_count * 100 // total_videos}%" if total_videos > 0 else "0%"
    }

    summary_file = os.path.join(results_dir, f"{task_name}_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    return summary_file

def get_video_name(video_path):
    """Extract clean video name without extension"""
    return os.path.splitext(os.path.basename(video_path))[0]