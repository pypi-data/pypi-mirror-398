from setuptools import setup, find_packages

setup(
    name="ephemeral-terminal-chat", # Daha benzersiz bir isim
    version="0.1.1",
    author="YourName",
    description="Zero-trace terminal chat with 59s read-to-expire logic",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ephemeral-chat",
    packages=find_packages(),
    py_modules=["main"], # main.py dosyası kök dizinde olduğu için
    install_requires=[
        "textual>=0.45.0",
        "supabase>=2.3.0",
        "python-dotenv>=1.0.0",
        "pyperclip>=1.8.2",
    ],
    entry_points={
        "console_scripts": [
            "ephemeral=main:main_func",
        ],
    },
    python_requires=">=3.10",
)