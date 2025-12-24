# NoCapLang

A Gen Z slang-based programming language that compiles to C++. No cap fr fr! 🔥

NoCapLang combines the expressiveness of modern programming languages with Gen Z slang syntax, making coding more fun while maintaining full functionality. The language supports object-oriented programming, async/await, pattern matching, and includes a comprehensive standard library.

## Quick Start

```nocap
tea: Hello World in NoCapLang
fr message: text = "Hello, World! No cap!"
yap(message)
```

Run your program (compiles and executes automatically):
```bash
nocap hello.nocap
```

That's it! Output appears immediately. No need to manually compile and run.

## Documentation

- **[Getting Started](https://nocaplang.com/docs/getting-started)** - Installation and first steps
- **[Language Reference](https://nocaplang.com/docs/language-reference)** - Complete language syntax and features
- **[Compiler Usage](https://nocaplang.com/docs/compiler-usage)** - How to use the compiler
- **[REPL Tutorial](https://nocaplang.com/docs/repl-tutorial)** - Interactive programming guide
- **[Standard Library API](https://nocaplang.com/docs/stdlib-reference)** - Built-in functions reference
- **[Try Online Playground](https://nocaplang.com/playground)** - Test NoCapLang in your browser
- **[Examples](https://nocaplang.com/playground)** - Sample programs demonstrating all features

## Project Structure

```
NoCapLang/
├── src/                    # C++ source files
│   ├── lexer/             # Lexical analysis
│   ├── parser/            # Syntax analysis
│   ├── semantic/          # Semantic analysis
│   ├── codegen/           # Code generation
│   ├── stdlib/            # Standard library (C++)
│   ├── repl/              # REPL implementation
│   └── cli/               # CLI and compiler driver
├── python/                 # Python implementation
│   └── nocaplang/         # Python package
│       ├── lexer/
│       ├── parser/
│       ├── semantic/
│       ├── codegen/
│       ├── stdlib/
│       ├── repl/
│       └── cli/
├── java/                   # Java implementation
│   └── src/
│       ├── main/java/com/nocaplang/
│       │   ├── lexer/
│       │   ├── parser/
│       │   ├── semantic/
│       │   ├── codegen/
│       │   ├── stdlib/
│       │   ├── repl/
│       │   └── cli/
│       └── test/java/com/nocaplang/
├── tests/                  # C++ tests
├── include/                # C++ header files
├── examples/               # Example NoCapLang programs
├── docs/                   # Documentation
├── CMakeLists.txt         # CMake build configuration
├── build.gradle           # Gradle build configuration
├── setup.py               # Python package setup
└── requirements.txt       # Python dependencies
```

## Building

### C++ Implementation

```bash
mkdir build && cd build
cmake ..
make
```

### Python Implementation

```bash
pip install -e .
```

### Java Implementation

```bash
./gradlew build
```

## Running

### Compile a NoCapLang program

```bash
# Using Python
nocap program.nocap

# Using C++
./build/nocap program.nocap

# Using Java
./gradlew run --args="program.nocap"
```

### Start REPL

```bash
# Using Python
nocap --repl

# Using C++
./build/nocap --repl

# Using Java
./gradlew runRepl
```

## Testing

### C++ Tests (with RapidCheck)

```bash
cd build
make test
```

### Python Tests (with Hypothesis)

```bash
pytest python/tests/
```

### Java Tests (with jqwik)

```bash
./gradlew test
```

## Development Status

This project is in early development. The compiler infrastructure is being built according to the specification in `.kiro/specs/nocap-lang/`.

## Language Features

NoCapLang supports:
- **Variables and data types** - text, digits, tf, lineup, bag
- **Control flow** - vibecheck, run, until, each, dip, skip
- **Functions** - lowkey, comeback, lambda functions
- **Classes and inheritance** - vibe, vibes_with, self
- **Error handling** - tryna, oops, nomatter, crash
- **Async/await** - chill, holdup
- **Pattern matching** - match, case with value/type/range matching
- **Module system** - grab with relative imports
- **Comments** - tea: (single-line), rant: :end (multi-line)
- **Assertions** - nocap for runtime checks
- **Standard library** - String, math, collection, and file I/O functions

## Example Programs

Check out the [examples/](examples/) directory for complete programs:

- **[hello.nocap](examples/hello.nocap)** - Hello World and basics
- **[comprehensive_demo.nocap](examples/comprehensive_demo.nocap)** - All language features
- **[functions_test.nocap](examples/functions_test.nocap)** - Function examples
- **[classes_test.nocap](examples/classes_test.nocap)** - OOP examples
- **[collections_test.nocap](examples/collections_test.nocap)** - Arrays and objects
- **[error_handling_test.nocap](examples/error_handling_test.nocap)** - Try-catch examples
- **[async_example.nocap](examples/async_example.nocap)** - Async/await examples
- **[pattern_matching.nocap](examples/pattern_matching.nocap)** - Pattern matching examples
- **[stdlib_example.nocap](examples/stdlib_example.nocap)** - Standard library usage
- **[assertions_example.nocap](examples/assertions_example.nocap)** - Assertion examples

## Contributing

Contributions are welcome! Please read the documentation and check existing examples before submitting PRs.

## License

TBD
