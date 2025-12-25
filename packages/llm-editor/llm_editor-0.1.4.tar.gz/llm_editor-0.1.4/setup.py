import os
from setuptools import setup, find_packages

setup(
    name="llm-editor",
    version="0.1.4",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "openai",
        "PyYAML",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "edit=llm_editor.cli:main",
        ],
    },
    author="Abhinav",
    description="A CLI tool to edit and chat with files using LLMs",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/gptabhinav/llm-editor",  # homepage
    project_urls={
        "Source": "https://github.com/gptabhinav/llm-editor",
        "Bug Tracker": "https://github.com/gptabhinav/llm-editor/issues",
    },
    license="MIT"
)
