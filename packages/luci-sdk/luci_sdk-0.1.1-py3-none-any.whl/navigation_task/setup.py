from setuptools import setup, find_packages

setup(
    name="navigation-task",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "torch>=2.0.0",
        "transformers>=4.40.0",
        "qwen-vl-utils>=0.0.14",
        "accelerate>=0.20.0",
        "pillow>=8.0.0",
        "numpy>=1.21.0",
    ],
    python_requires=">=3.8",
    author="Your Name",
    description="Video QA for egocentric navigation",
    long_description_content_type="text/markdown",
)