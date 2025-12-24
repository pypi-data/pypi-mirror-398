/**
 * NoCapLang Standard Library - C++ Implementation
 * 
 * This header provides C++ implementations of all NoCapLang stdlib functions.
 * Automatically included when compiling NoCapLang to C++.
 */

#ifndef NOCAPLANG_STDLIB_HPP
#define NOCAPLANG_STDLIB_HPP

#include <string>
#include <vector>
#include <unordered_map>
#include <algorithm>
#include <cmath>
#include <cctype>
#include <functional>
#include <iostream>
#include <sstream>
#include <any>

namespace nocaplang {

// ============================================================================
// Null Type (for ghost values)
// ============================================================================

struct Null {
    friend std::ostream& operator<<(std::ostream& os, const Null&) {
        return os << "null";
    }
    
    // Allow comparison with nullptr
    bool operator==(std::nullptr_t) const { return true; }
    bool operator!=(std::nullptr_t) const { return false; }
    
    // Allow comparison with other Null values
    bool operator==(const Null&) const { return true; }
    bool operator!=(const Null&) const { return false; }
};

// Global null instance
static const Null null_value;

// ============================================================================
// String Functions
// ============================================================================

// Helper to convert any value to string
inline std::string to_text(double value) {
    // Check if it's a whole number
    if (value == std::floor(value)) {
        return std::to_string(static_cast<long long>(value));
    }
    return std::to_string(value);
}

inline std::string to_text(bool value) {
    return value ? "true" : "false";
}

inline std::string to_text(const std::string& value) {
    return value;
}

inline std::string to_text(const char* value) {
    return std::string(value);
}

inline std::string trim(const std::string& str) {
    size_t start = str.find_first_not_of(" \t\n\r");
    if (start == std::string::npos) return "";
    size_t end = str.find_last_not_of(" \t\n\r");
    return str.substr(start, end - start + 1);
}

inline std::string uppercase(const std::string& str) {
    std::string result = str;
    std::transform(result.begin(), result.end(), result.begin(), ::toupper);
    return result;
}

inline std::string lowercase(const std::string& str) {
    std::string result = str;
    std::transform(result.begin(), result.end(), result.begin(), ::tolower);
    return result;
}

inline double length(const std::string& str) {
    return static_cast<double>(str.length());
}

inline double len(const std::string& str) {
    return static_cast<double>(str.length());
}

template<typename T>
inline double length(const std::vector<T>& vec) {
    return static_cast<double>(vec.size());
}

template<typename T>
inline double len(const std::vector<T>& vec) {
    return static_cast<double>(vec.size());
}

template<typename K, typename V>
inline double length(const std::unordered_map<K, V>& map) {
    return static_cast<double>(map.size());
}

template<typename K, typename V>
inline double len(const std::unordered_map<K, V>& map) {
    return static_cast<double>(map.size());
}

// ============================================================================
// Math Functions
// ============================================================================

inline double nocap_abs(double x) {
    return std::abs(x);
}

inline double nocap_sqrt(double x) {
    return std::sqrt(x);
}

inline double nocap_pow(double base, double exp) {
    return std::pow(base, exp);
}

inline double nocap_round(double x) {
    return std::round(x);
}

inline double nocap_floor(double x) {
    return std::floor(x);
}

inline double nocap_ceil(double x) {
    return std::ceil(x);
}

inline double nocap_min(double a, double b) {
    return std::min(a, b);
}

inline double nocap_max(double a, double b) {
    return std::max(a, b);
}

inline double mod(double a, double b) {
    return std::fmod(a, b);
}

// Safe division that throws on divide by zero
inline double safe_divide(double a, double b) {
    if (b == 0.0) {
        throw std::runtime_error("Division by zero");
    }
    return a / b;
}

// Aliases without nocap_ prefix (use these to avoid conflicts)
using nocaplang::nocap_abs;
using nocaplang::nocap_sqrt;
using nocaplang::nocap_pow;
using nocaplang::nocap_round;
using nocaplang::nocap_floor;
using nocaplang::nocap_ceil;
using nocaplang::nocap_min;
using nocaplang::nocap_max;

// Define shorter names that won't conflict
#define abs nocap_abs
#define sqrt nocap_sqrt
#define pow nocap_pow
#define round nocap_round
#define floor nocap_floor
#define ceil nocap_ceil
#define min nocap_min
#define max nocap_max

// ============================================================================
// Collection Functions
// ============================================================================

template<typename T>
inline std::vector<T> sort(std::vector<T> vec) {
    std::sort(vec.begin(), vec.end());
    return vec;
}

template<typename T>
inline std::vector<T> reverse(std::vector<T> vec) {
    std::reverse(vec.begin(), vec.end());
    return vec;
}

template<typename T, typename Func>
inline auto map(const std::vector<T>& vec, Func func) -> std::vector<decltype(func(std::declval<T>()))> {
    std::vector<decltype(func(std::declval<T>()))> result;
    result.reserve(vec.size());
    for (const auto& item : vec) {
        result.push_back(func(item));
    }
    return result;
}

template<typename T, typename Func>
inline std::vector<T> filter(const std::vector<T>& vec, Func func) {
    std::vector<T> result;
    for (const auto& item : vec) {
        if (func(item)) {
            result.push_back(item);
        }
    }
    return result;
}

template<typename T, typename Func, typename Acc>
inline Acc reduce(const std::vector<T>& vec, Func func, Acc initial) {
    Acc result = initial;
    for (const auto& item : vec) {
        result = func(result, item);
    }
    return result;
}

template<typename T>
inline bool has(const std::vector<T>& vec, const T& value) {
    return std::find(vec.begin(), vec.end(), value) != vec.end();
}

template<typename K, typename V>
inline bool has(const std::unordered_map<K, V>& map, const K& key) {
    return map.find(key) != map.end();
}

// Overload for string keys with const char* argument
template<typename V>
inline bool has(const std::unordered_map<std::string, V>& map, const char* key) {
    return map.find(std::string(key)) != map.end();
}

} // namespace nocaplang

// Import nocaplang namespace for convenience
using namespace nocaplang;

// ============================================================================
// Helper Functions for Printing (must be in global namespace)
// ============================================================================

// Helper to print std::any values
inline std::ostream& operator<<(std::ostream& os, const std::any& value) {
    if (!value.has_value()) {
        return os << "null";
    }
    
    // Try common types in order
    try {
        return os << std::any_cast<const char*>(value);
    } catch (...) {}
    
    try {
        return os << std::any_cast<std::string>(value);
    } catch (...) {}
    
    try {
        return os << std::any_cast<double>(value);
    } catch (...) {}
    
    try {
        return os << (std::any_cast<bool>(value) ? "true" : "false");
    } catch (...) {}
    
    try {
        return os << std::any_cast<int>(value);
    } catch (...) {}
    
    return os << "<any>";
}

template<typename T>
std::ostream& operator<<(std::ostream& os, const std::vector<T>& vec) {
    os << "[";
    for (size_t i = 0; i < vec.size(); ++i) {
        if (i > 0) os << ", ";
        os << vec[i];
    }
    os << "]";
    return os;
}

template<typename K, typename V>
std::ostream& operator<<(std::ostream& os, const std::unordered_map<K, V>& map) {
    os << "{";
    size_t i = 0;
    for (const auto& [key, value] : map) {
        if (i > 0) os << ", ";
        os << key << ": " << value;
        ++i;
    }
    os << "}";
    return os;
}

#endif // NOCAPLANG_STDLIB_HPP
