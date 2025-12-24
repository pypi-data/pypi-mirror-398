#include <iostream>
#include <string>
#include <vector>
#include <fstream>
#include <filesystem>

namespace fs = std::filesystem;

void print_usage(const char* program_name) {
    std::cout << "NoCapLang - A Gen Z slang-based programming language compiler\n\n";
    std::cout << "Usage: " << program_name << " [options] <file.nocap>\n\n";
    std::cout << "Options:\n";
    std::cout << "  --target <cpp|java>  Target language (default: cpp)\n";
    std::cout << "  --output, -o <file>  Output file path\n";
    std::cout << "  --repl               Start interactive REPL\n";
    std::cout << "  --version            Show version information\n";
    std::cout << "  --help, -h           Show this help message\n";
    std::cout << "  --verbose, -v        Enable verbose output\n\n";
    std::cout << "Examples:\n";
    std::cout << "  " << program_name << " program.nocap\n";
    std::cout << "  " << program_name << " --target java program.nocap\n";
    std::cout << "  " << program_name << " --output myprogram program.nocap\n";
    std::cout << "  " << program_name << " --repl\n";
}

void print_version() {
    std::cout << "NoCapLang version 0.1.0\n";
}

int main(int argc, char* argv[]) {
    std::string input_file;
    std::string output_file;
    std::string target = "cpp";
    bool repl_mode = false;
    bool verbose = false;
    
    // Parse command line arguments
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        
        if (arg == "--help" || arg == "-h") {
            print_usage(argv[0]);
            return 0;
        } else if (arg == "--version") {
            print_version();
            return 0;
        } else if (arg == "--repl") {
            repl_mode = true;
        } else if (arg == "--verbose" || arg == "-v") {
            verbose = true;
        } else if (arg == "--target") {
            if (i + 1 < argc) {
                target = argv[++i];
                if (target != "cpp" && target != "java") {
                    std::cerr << "Error: Invalid target '" << target << "'. Must be 'cpp' or 'java'.\n";
                    return 1;
                }
            } else {
                std::cerr << "Error: --target requires an argument\n";
                return 1;
            }
        } else if (arg == "--output" || arg == "-o") {
            if (i + 1 < argc) {
                output_file = argv[++i];
            } else {
                std::cerr << "Error: --output requires an argument\n";
                return 1;
            }
        } else if (arg[0] == '-') {
            std::cerr << "Error: Unknown option '" << arg << "'\n";
            print_usage(argv[0]);
            return 1;
        } else {
            input_file = arg;
        }
    }
    
    // Start REPL if requested
    if (repl_mode) {
        std::cout << "NoCapLang REPL v0.1.0\n";
        std::cout << "Type ':help' for help, ':exit' to quit\n";
        std::cout << "REPL not yet implemented - coming soon!\n";
        return 0;
    }
    
    // Require input file if not in REPL mode
    if (input_file.empty()) {
        std::cerr << "Error: No input file specified (or use --repl)\n";
        print_usage(argv[0]);
        return 1;
    }
    
    // Validate input file
    if (!fs::exists(input_file)) {
        std::cerr << "Error: File not found: " << input_file << "\n";
        return 1;
    }
    
    fs::path input_path(input_file);
    if (input_path.extension() != ".nocap") {
        std::cerr << "Warning: File does not have .nocap extension: " << input_file << "\n";
    }
    
    // Determine output file
    if (output_file.empty()) {
        if (target == "cpp") {
            output_file = input_path.stem().string() + ".cpp";
        } else {
            output_file = input_path.stem().string() + ".java";
        }
    }
    
    if (verbose) {
        std::cout << "Input: " << input_file << "\n";
        std::cout << "Output: " << output_file << "\n";
        std::cout << "Target: " << target << "\n";
    }
    
    std::cout << "Compiling " << input_file << " to " << target << "...\n";
    std::cout << "Compiler not yet implemented - coming soon!\n";
    
    return 0;
}
