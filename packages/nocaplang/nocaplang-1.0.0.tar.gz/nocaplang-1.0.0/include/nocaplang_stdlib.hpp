#ifndef NOCAPLANG_STDLIB_HPP
#define NOCAPLANG_STDLIB_HPP

#include <string>
#include <vector>
#include <unordered_map>
#include <functional>
#include <algorithm>
#include <cmath>
#include <random>
#include <fstream>
#include <sstream>
#include <filesystem>
#include <cctype>

namespace nocaplang {
namespace stdlib {

// ============================================================================
// String Functions
// ============================================================================

/**
 * Get the length of a string
 */
inline double length(const std::string& s) {
    return static_cast<double>(s.length());
}

/**
 * Extract a substring from start to end (exclusive)
 */
inline std::string substring(const std::string& s, double start, double end) {
    size_t start_idx = static_cast<size_t>(start);
    size_t end_idx = static_cast<size_t>(end);
    
    if (start_idx >= s.length()) {
        return "";
    }
    
    if (end_idx > s.length()) {
        end_idx = s.length();
    }
    
    if (start_idx >= end_idx) {
        return "";
    }
    
    return s.substr(start_idx, end_idx - start_idx);
}

/**
 * Split a string by delimiter
 */
inline std::vector<std::string> split(const std::string& s, const std::string& delimiter) {
    std::vector<std::string> result;
    
    if (delimiter.empty()) {
        // Split into individual characters
        for (char c : s) {
            result.push_back(std::string(1, c));
        }
        return result;
    }
    
    size_t start = 0;
    size_t end = s.find(delimiter);
    
    while (end != std::string::npos) {
        result.push_back(s.substr(start, end - start));
        start = end + delimiter.length();
        end = s.find(delimiter, start);
    }
    
    result.push_back(s.substr(start));
    return result;
}

/**
 * Join strings with separator
 */
inline std::string join(const std::vector<std::string>& parts, const std::string& separator) {
    if (parts.empty()) {
        return "";
    }
    
    std::string result = parts[0];
    for (size_t i = 1; i < parts.size(); ++i) {
        result += separator + parts[i];
    }
    
    return result;
}

/**
 * Convert string to uppercase
 */
inline std::string uppercase(const std::string& s) {
    std::string result = s;
    std::transform(result.begin(), result.end(), result.begin(),
                   [](unsigned char c) { return std::toupper(c); });
    return result;
}

/**
 * Convert string to lowercase
 */
inline std::string lowercase(const std::string& s) {
    std::string result = s;
    std::transform(result.begin(), result.end(), result.begin(),
                   [](unsigned char c) { return std::tolower(c); });
    return result;
}

/**
 * Trim whitespace from both ends
 */
inline std::string trim(const std::string& s) {
    auto start = s.begin();
    while (start != s.end() && std::isspace(*start)) {
        ++start;
    }
    
    auto end = s.end();
    do {
        --end;
    } while (std::distance(start, end) > 0 && std::isspace(*end));
    
    return std::string(start, end + 1);
}

/**
 * Check if string contains substring
 */
inline bool contains(const std::string& s, const std::string& substring) {
    return s.find(substring) != std::string::npos;
}

/**
 * Replace all occurrences of old_str with new_str
 */
inline std::string replace(const std::string& s, const std::string& old_str, const std::string& new_str) {
    if (old_str.empty()) {
        return s;
    }
    
    std::string result = s;
    size_t pos = 0;
    
    while ((pos = result.find(old_str, pos)) != std::string::npos) {
        result.replace(pos, old_str.length(), new_str);
        pos += new_str.length();
    }
    
    return result;
}

// ============================================================================
// Math Functions
// ============================================================================

/**
 * Absolute value
 */
inline double abs(double n) {
    return std::abs(n);
}

/**
 * Square root
 */
inline double sqrt(double n) {
    return std::sqrt(n);
}

/**
 * Power function
 */
inline double pow(double base, double exp) {
    return std::pow(base, exp);
}

/**
 * Round to nearest integer
 */
inline double round(double n) {
    return std::round(n);
}

/**
 * Round down
 */
inline double floor(double n) {
    return std::floor(n);
}

/**
 * Round up
 */
inline double ceil(double n) {
    return std::ceil(n);
}

/**
 * Minimum of two values
 */
inline double min(double a, double b) {
    return std::min(a, b);
}

/**
 * Maximum of two values
 */
inline double max(double a, double b) {
    return std::max(a, b);
}

/**
 * Random number between 0 and 1
 */
inline double random() {
    static std::random_device rd;
    static std::mt19937 gen(rd());
    static std::uniform_real_distribution<> dis(0.0, 1.0);
    return dis(gen);
}

// ============================================================================
// Collection Functions
// ============================================================================

/**
 * Map function over vector
 */
template<typename T, typename U>
std::vector<U> map(const std::vector<T>& arr, std::function<U(T)> fn) {
    std::vector<U> result;
    result.reserve(arr.size());
    
    for (const auto& item : arr) {
        result.push_back(fn(item));
    }
    
    return result;
}

/**
 * Filter vector by predicate
 */
template<typename T>
std::vector<T> filter(const std::vector<T>& arr, std::function<bool(T)> fn) {
    std::vector<T> result;
    
    for (const auto& item : arr) {
        if (fn(item)) {
            result.push_back(item);
        }
    }
    
    return result;
}

/**
 * Reduce vector to single value
 */
template<typename T, typename U>
U reduce(const std::vector<T>& arr, std::function<U(U, T)> fn, U initial) {
    U result = initial;
    
    for (const auto& item : arr) {
        result = fn(result, item);
    }
    
    return result;
}

/**
 * Sort vector (returns new sorted vector)
 */
template<typename T>
std::vector<T> sort(const std::vector<T>& arr) {
    std::vector<T> result = arr;
    std::sort(result.begin(), result.end());
    return result;
}

/**
 * Reverse vector (returns new reversed vector)
 */
template<typename T>
std::vector<T> reverse(const std::vector<T>& arr) {
    std::vector<T> result = arr;
    std::reverse(result.begin(), result.end());
    return result;
}

/**
 * Get keys from map
 */
template<typename K, typename V>
std::vector<K> keys(const std::unordered_map<K, V>& obj) {
    std::vector<K> result;
    result.reserve(obj.size());
    
    for (const auto& pair : obj) {
        result.push_back(pair.first);
    }
    
    return result;
}

/**
 * Get values from map
 */
template<typename K, typename V>
std::vector<V> values(const std::unordered_map<K, V>& obj) {
    std::vector<V> result;
    result.reserve(obj.size());
    
    for (const auto& pair : obj) {
        result.push_back(pair.second);
    }
    
    return result;
}

/**
 * Check if map has key
 */
template<typename K, typename V>
bool has(const std::unordered_map<K, V>& obj, const K& key) {
    return obj.find(key) != obj.end();
}

// ============================================================================
// File I/O Functions
// ============================================================================

/**
 * Read entire file contents
 */
inline std::string read_file(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file: " + path);
    }
    
    std::stringstream buffer;
    buffer << file.rdbuf();
    return buffer.str();
}

/**
 * Write content to file (overwrites existing)
 */
inline void write_file(const std::string& path, const std::string& content) {
    std::ofstream file(path);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file for writing: " + path);
    }
    
    file << content;
}

/**
 * Append content to file
 */
inline void append_file(const std::string& path, const std::string& content) {
    std::ofstream file(path, std::ios::app);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file for appending: " + path);
    }
    
    file << content;
}

/**
 * Check if file exists
 */
inline bool file_exists(const std::string& path) {
    return std::filesystem::exists(path);
}

/**
 * Delete file
 */
inline void delete_file(const std::string& path) {
    if (!std::filesystem::remove(path)) {
        throw std::runtime_error("Failed to delete file: " + path);
    }
}

/**
 * List directory contents
 */
inline std::vector<std::string> list_directory(const std::string& path) {
    std::vector<std::string> result;
    
    if (!std::filesystem::exists(path)) {
        throw std::runtime_error("Directory does not exist: " + path);
    }
    
    if (!std::filesystem::is_directory(path)) {
        throw std::runtime_error("Path is not a directory: " + path);
    }
    
    for (const auto& entry : std::filesystem::directory_iterator(path)) {
        result.push_back(entry.path().filename().string());
    }
    
    return result;
}

} // namespace stdlib
} // namespace nocaplang

#endif // NOCAPLANG_STDLIB_HPP
