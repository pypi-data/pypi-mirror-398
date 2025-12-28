#!/usr/bin/env python3
"""
Model download script for ST-R1 navigation model
Based on download.txt requirements
"""

import os
import subprocess
from huggingface_hub import snapshot_download


def download_st_r1_model(save_path="./ST-R1-mcq"):
    """
    Download ST-R1 model from Hugging Face using hf CLI
    Based on: hf download openinterx/ST-R1-mcq
    """
    try:
        model_name = "openinterx/ST-R1-mcq"
        print(f"Downloading {model_name} to {save_path}...")

        # Method 1: Using huggingface_hub directly
        snapshot_download(
            repo_id=model_name,
            local_dir=save_path,
            local_dir_use_symlinks=False
        )
        print(f"Model downloaded successfully to {save_path}")
        return True

    except Exception as e:
        print(f"Direct download failed: {e}")

        # Method 2: Using hf CLI command as fallback
        try:
            print("Trying hf CLI download...")
            cmd = f"hf download {model_name} --local-dir {save_path}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"Model downloaded successfully via CLI to {save_path}")
                return True
            else:
                print(f"CLI download failed: {result.stderr}")

        except Exception as cli_error:
            print(f"CLI download error: {cli_error}")

        print("Alternative: Use base Qwen2-VL model")
        return False


def download_ego_st_repo(save_path="./Ego-ST"):
    """
    Download Ego-ST repository
    Based on: https://github.com/WPR001/Ego-ST.git
    """
    try:
        repo_url = "https://github.com/WPR001/Ego-ST.git"
        print(f"Cloning {repo_url} to {save_path}...")

        cmd = f"git clone {repo_url} {save_path}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"Repository cloned successfully to {save_path}")
            return True
        else:
            print(f"Git clone failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"Repository download failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Download models and repositories")
    parser.add_argument("--model-path", default="./ST-R1-mcq", help="Model download path")
    parser.add_argument("--repo-path", default="./Ego-ST", help="Repository download path")
    parser.add_argument("--model-only", action="store_true", help="Download model only")
    parser.add_argument("--repo-only", action="store_true", help="Download repository only")
    args = parser.parse_args()

    success = True

    if not args.repo_only:
        print("Downloading ST-R1 model...")
        success &= download_st_r1_model(args.model_path)

    if not args.model_only:
        print("\nDownloading Ego-ST repository...")
        success &= download_ego_st_repo(args.repo_path)

    if success:
        print("\nAll downloads completed successfully!")
    else:
        print("\nSome downloads failed. Check output above.")