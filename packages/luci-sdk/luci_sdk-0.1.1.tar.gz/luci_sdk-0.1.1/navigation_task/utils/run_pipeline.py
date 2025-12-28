#!/usr/bin/env python3
"""
Universal Pipeline Runner - All complex logic here
"""

import sys
import os
import subprocess

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from pipeline_utils import (
    find_videos, create_task_structure, create_questions_template,
    generate_summary, get_video_name
)

# Colors for output
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'

def print_info(msg): print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")
def print_success(msg): print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}")
def print_warning(msg): print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {msg}")
def print_error(msg): print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")

def main():
    if len(sys.argv) < 11:
        print("Usage: python run_pipeline.py <task_name> <description> <video_formats> <model_path> <ego_st_path> <python_cmd> <custom_dataset_path> <fallback_model> <max_timeout> <parallel_jobs>")
        sys.exit(1)

    # Parse all parameters from bash file
    task_name = sys.argv[1]
    description = sys.argv[2]
    video_formats = sys.argv[3].split()
    model_path = sys.argv[4]
    ego_st_path = sys.argv[5]
    python_cmd = sys.argv[6]
    custom_dataset_path = sys.argv[7] if sys.argv[7] else None
    fallback_model = sys.argv[8]
    max_timeout = int(sys.argv[9])
    parallel_jobs = int(sys.argv[10])

    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    task_dir = os.path.join(project_dir, "tasks", task_name)
    video_dir = os.path.join(task_dir, "videos")
    results_dir = os.path.join(task_dir, "results")
    questions_file = os.path.join(task_dir, f"{task_name}_questions.json")

    print_info("🚀 Starting Universal Video QA Pipeline")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"📋 Task: {task_name}")
    print(f"📝 Description: {description}")
    print(f"📂 Task Directory: {task_dir}")
    print(f"🤖 Model Path: {model_path}")
    print(f"📚 Ego-ST Path: {ego_st_path}")
    if custom_dataset_path:
        print(f"📊 Custom Dataset: {custom_dataset_path}")
    print(f"⏱️  Timeout: {max_timeout}s")
    print(f"🔧 Python: {python_cmd}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Step 1: Create task structure if needed
    if not os.path.exists(task_dir):
        print_warning("Creating new task structure...")
        create_task_structure(task_dir, task_name, description)
        create_questions_template(questions_file, task_name, description)

        print_success(f"✓ Created task: {task_name}")
        print_warning(f"📝 Edit questions: {questions_file}")
        print_warning(f"🎥 Add videos: {video_dir}")
        print_info("🔄 Run again to process videos")
        return

    # Step 2: Check files
    if not os.path.exists(questions_file):
        print_error(f"Questions file missing: {questions_file}")
        return

    # Step 3: Find videos
    print_info("🔍 Searching for videos...")
    video_files = find_videos(video_dir, video_formats)

    if not video_files:
        print_error(f"No videos found in: {video_dir}")
        print_info(f"Supported formats: {' '.join(video_formats)}")
        return

    print_success(f"Found {len(video_files)} video(s)")

    # Step 4: Process videos
    print_info("⚡ Processing videos...")
    success_count = 0

    for i, video_file in enumerate(video_files):
        video_name = get_video_name(video_file)
        print_info(f"Processing ({i+1}/{len(video_files)}): {video_name}")

        # Run universal analysis
        result_file = os.path.join(results_dir, f"{task_name}_{video_name}_result.json")

        try:
            # Change to src directory to run universal analysis
            src_dir = os.path.join(project_dir, "src")
            cmd = [
                python_cmd, "universal_analysis.py",
                questions_file, video_file, model_path, fallback_model
            ]

            result = subprocess.run(
                cmd, cwd=src_dir, capture_output=True, text=True, timeout=max_timeout
            )

            if result.returncode == 0:
                # Save result
                with open(result_file, 'w') as f:
                    f.write(result.stdout)
                print_success(f"✓ {video_name}")
                success_count += 1
            else:
                print_error(f"✗ {video_name}: {result.stderr}")

        except subprocess.TimeoutExpired:
            print_error(f"✗ {video_name}: Timeout")
        except Exception as e:
            print_error(f"✗ {video_name}: {e}")

    # Step 5: Generate summary
    summary_file = generate_summary(task_name, results_dir, len(video_files), success_count)

    # Step 6: Report results
    print("")
    print_success("🎉 Pipeline completed!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"📊 Results: {success_count}/{len(video_files)} successful")
    print(f"📁 Results: {results_dir}")
    print(f"📄 Summary: {summary_file}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if success_count == len(video_files):
        print_success("🌟 All videos processed successfully!")
    else:
        print_warning("⚠️  Some videos failed. Check individual results.")

if __name__ == "__main__":
    main()