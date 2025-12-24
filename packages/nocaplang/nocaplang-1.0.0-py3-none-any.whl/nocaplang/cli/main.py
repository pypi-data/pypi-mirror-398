"""Main entry point for the NoCapLang compiler CLI."""

import sys
import argparse
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional

from ..compiler import Compiler, Target

# Get version from package
try:
    from importlib.metadata import version
    __version__ = version("nocaplang")
except Exception:
    __version__ = "0.1.8"


def main() -> int:
    """Main entry point for the NoCapLang compiler.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        prog="nocap",
        description="NoCapLang - A Gen Z slang-based programming language compiler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  nocap program.nocap              Compile and run (default)
  nocap --run program.nocap        Compile and run
  nocap --compile-only program.nocap Compile without running
  nocap --output myprogram program.nocap Specify output file
  nocap --repl                     Start interactive REPL
        """
    )
    
    parser.add_argument(
        "file",
        nargs="?",
        type=str,
        help="NoCapLang source file (.nocap)"
    )
    
    parser.add_argument(
        "--target",
        choices=["cpp"],
        default="cpp",
        help="Target language for compilation (C++ only)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path"
    )
    
    parser.add_argument(
        "--run", "-r",
        action="store_true",
        help="Compile and run the program (default behavior)"
    )
    
    parser.add_argument(
        "--compile-only", "-c",
        action="store_true",
        help="Only compile, don't run the program"
    )
    
    parser.add_argument(
        "--repl",
        action="store_true",
        help="Start interactive REPL"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"NoCapLang {__version__}"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="Disable optimization passes"
    )
    
    args = parser.parse_args()
    
    # Start REPL if requested
    if args.repl:
        from ..repl import start_repl
        target = Target.CPP if args.target == "cpp" else Target.JAVA
        start_repl(target=target)
        return 0
    
    # Require input file if not in REPL mode
    if not args.file:
        parser.error("the following arguments are required: file (or use --repl)")
        return 1
    
    # Validate input file
    input_path = Path(args.file)
    if not input_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1
    
    if input_path.suffix != ".nocap":
        print(f"Warning: File does not have .nocap extension: {args.file}", file=sys.stderr)
    
    # Create compiler with specified target
    target = Target.CPP if args.target == "cpp" else Target.JAVA
    optimize = not args.no_optimize
    compiler = Compiler(target=target, verbose=args.verbose, optimize=optimize)
    
    # Determine output file
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = compiler.get_default_output_path(input_path)
    
    if args.verbose:
        print(f"Input: {input_path}")
        print(f"Output: {output_path}")
        print(f"Target: {args.target}")
    
    print(f"Compiling {input_path} to {args.target.upper()}...")
    
    # Compile the file
    result = compiler.compile_file(input_path, output_path)
    
    if result.success:
        print(f"✓ Compilation successful! Output written to: {output_path}")
        
        # Copy stdlib header if compiling to C++
        if target == Target.CPP:
            stdlib_header = Path(__file__).parent.parent / "stdlib" / "nocaplang_stdlib.hpp"
            if stdlib_header.exists():
                output_dir = output_path.parent
                shutil.copy(stdlib_header, output_dir / "nocaplang_stdlib.hpp")
                if args.verbose:
                    print(f"✓ Copied stdlib header to: {output_dir}")
        
        # Run the program unless --compile-only is specified
        should_run = not args.compile_only
        
        if should_run:
            print(f"\n{'='*50}")
            print("Running program...")
            print(f"{'='*50}\n")
            
            exit_code = run_compiled_program(output_path, target, args.verbose)
            
            if exit_code != 0:
                print(f"\n✗ Program exited with code {exit_code}", file=sys.stderr)
                return exit_code
        
        return 0
    else:
        print("✗ Compilation failed with errors:", file=sys.stderr)
        for error in result.errors:
            print(error, file=sys.stderr)
        return 1


def run_compiled_program(output_path: Path, target: Target, verbose: bool = False) -> int:
    """Compile and run the generated code.
    
    Args:
        output_path: Path to the generated source file
        target: Target language (CPP or JAVA)
        verbose: Enable verbose output
        
    Returns:
        Exit code from the program
    """
    try:
        if target == Target.CPP:
            return run_cpp_program(output_path, verbose)
        else:
            return run_java_program(output_path, verbose)
    except FileNotFoundError as e:
        print(f"✗ Error: Required compiler not found: {e}", file=sys.stderr)
        print(f"  Please install the required compiler:", file=sys.stderr)
        if target == Target.CPP:
            print(f"  - For C++: Install g++ or clang++", file=sys.stderr)
        else:
            print(f"  - For Java: Install JDK (javac and java)", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as e:
        print(f"✗ Error during execution: {e}", file=sys.stderr)
        return e.returncode
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1


def run_cpp_program(cpp_file: Path, verbose: bool = False) -> int:
    """Compile and run a C++ program.
    
    Args:
        cpp_file: Path to the C++ source file
        verbose: Enable verbose output
        
    Returns:
        Exit code from the program
    """
    # Create temporary executable
    with tempfile.NamedTemporaryFile(suffix=".out", delete=False) as tmp:
        exe_path = Path(tmp.name)
    
    try:
        # Check if g++ is available, otherwise try clang++
        compiler = "g++"
        if shutil.which(compiler) is None:
            compiler = "clang++"
            if shutil.which(compiler) is None:
                raise FileNotFoundError("g++ or clang++")
        
        # Compile the C++ code
        compile_cmd = [compiler, "-std=c++17", str(cpp_file), "-o", str(exe_path)]
        
        if verbose:
            print(f"Compiling with: {' '.join(compile_cmd)}")
        
        result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"✗ C++ compilation failed:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return result.returncode
        
        # Run the compiled executable
        if verbose:
            print(f"Executing: {exe_path}")
        
        result = subprocess.run([str(exe_path)])
        return result.returncode
        
    finally:
        # Clean up temporary executable
        if exe_path.exists():
            exe_path.unlink()


def run_java_program(java_file: Path, verbose: bool = False) -> int:
    """Compile and run a Java program.
    
    Args:
        java_file: Path to the Java source file
        verbose: Enable verbose output
        
    Returns:
        Exit code from the program
    """
    # Check if javac and java are available
    if shutil.which("javac") is None or shutil.which("java") is None:
        raise FileNotFoundError("javac and java")
    
    # Get the class name from the file
    class_name = java_file.stem
    
    # Create temporary directory for compiled classes
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Compile the Java code
        compile_cmd = ["javac", "-d", str(tmp_path), str(java_file)]
        
        if verbose:
            print(f"Compiling with: {' '.join(compile_cmd)}")
        
        result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"✗ Java compilation failed:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return result.returncode
        
        # Run the compiled Java class
        run_cmd = ["java", "-cp", str(tmp_path), class_name]
        
        if verbose:
            print(f"Executing: {' '.join(run_cmd)}")
        
        result = subprocess.run(run_cmd)
        return result.returncode


if __name__ == "__main__":
    sys.exit(main())
