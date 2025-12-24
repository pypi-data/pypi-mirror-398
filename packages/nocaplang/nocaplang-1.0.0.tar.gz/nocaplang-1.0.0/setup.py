"""
NoCapLang - A Gen Z slang-based programming language
Setup configuration for PyPI distribution
"""

from setuptools import setup, find_packages

setup(
    # Package identity
    name="nocaplang",
    version="1.0.0",
    
    # Author information
    author="Soumik Mukherjee",
    
    # Package description (will show on PyPI)
    description="A Gen Z slang-based programming language that compiles to C++. No cap fr fr! 🔥",
    long_description="""
# NoCapLang

A Gen Z slang-based programming language that compiles to C++.

## Installation

```bash
pip install nocaplang
```

## Quick Start

```nocap
tea: Hello World in NoCapLang
fr message: text = "Hello, World!"
yap(message)
```

Run your program (compiles and executes automatically):
```bash
nocap hello.nocap
```

That's it! Output appears immediately.

## Advanced Usage

Want more control? Use these flags:

```bash
# Just compile without running
nocap --compile-only hello.nocap

# Specify custom output file
nocap -o myprogram hello.nocap
```

## Features

- 🎨 Gen Z slang keywords (fr, yap, vibecheck, lowkey, etc.)
- 🚀 Compiles to blazing-fast C++
- 💻 Full OOP support with classes and inheritance
- 🔄 Pattern matching with check/hits/otherwise
- ⚡ Async/await support
- 📦 Comprehensive standard library (string, math, collections)
- 🎮 Interactive REPL
- 🌐 Try it online at https://nocaplang.com/playground

## Documentation

Visit **https://nocaplang.com** for:
- Complete language reference
- Interactive playground
- Tutorials and examples
- Standard library API

## Example

```nocap
lowkey greet(name: text) -> text {
    comeback "Yo, " + name + "! 👋"
}

fr names: lineup<text> = ["Alice", "Bob", "Charlie"]
each person in names {
    yap(greet(person))
}
```

## License

MIT License
    """,
    long_description_content_type="text/markdown",
    
    # URLs
    url="https://nocaplang.com",
    project_urls={
        "Homepage": "https://nocaplang.com",
        "Documentation": "https://nocaplang.com/docs",
        "Playground": "https://nocaplang.com/playground",
    },
    
    # Package structure
    packages=find_packages(where="python"),
    package_dir={"": "python"},
    include_package_data=True,
    package_data={
        "nocaplang.stdlib": ["*.hpp"],
    },
    
    # Requirements
    python_requires=">=3.8",
    install_requires=[
        # No runtime dependencies needed
    ],
    
    # Optional dependencies for development
    extras_require={
        "dev": [
            "pytest>=7.0",
            "hypothesis>=6.0.0",
            "black>=23.0",
        ],
    },
    
    # CLI command
    entry_points={
        "console_scripts": [
            "nocaplang=nocaplang.cli.main:main",
            "nocap=nocaplang.cli.main:main",
        ],
    },
    
    # PyPI classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Natural Language :: English",
    ],
    
    # Keywords for PyPI search
    keywords=[
        "programming-language",
        "compiler",
        "transpiler",
        "gen-z",
        "slang",
        "cpp",
        "java",
        "education",
        "fun",
    ],
    
    # License
    license="MIT",
    
    # Package options
    zip_safe=False,
)
