from setuptools import setup, find_packages

setup(
    name="eldar-millionaire-quiz",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "millionaire-quiz=eldar_millionaire_quiz.game:main"
        ]
    },
    author="Eldar",
    description="Millionaire style quiz game (CLI)",
    python_requires=">=3.8",
)
