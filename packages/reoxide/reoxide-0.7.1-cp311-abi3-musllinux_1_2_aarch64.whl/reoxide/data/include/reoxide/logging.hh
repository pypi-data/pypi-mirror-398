#pragma once
#define LOG_ERROR(...) reoxide_log(LEVEL_ERROR, __VA_ARGS__);
#define LOG_WARN(...) reoxide_log(LEVEL_WARN, __VA_ARGS__);
#define LOG_INFO(...) reoxide_log(LEVEL_INFO, __VA_ARGS__);
#define LOG_DEBUG(...) reoxide_log(LEVEL_DEBUG, __VA_ARGS__);
#define LOG_ASSERT(x, msg)                                                              \
    if (!(x)) {                                                                         \
        reoxide_log(LEVEL_ERROR, "assert at %s, line %d: %s", __FILE__, __LINE__, msg); \
        std::exit(1);                                                                   \
    }
#define LOG_FATAL(...)                                                          \
    {                                                                           \
        reoxide_log(LEVEL_ERROR, "fatal at %s, line %d: ", __FILE__, __LINE__); \
        reoxide_log(LEVEL_ERROR, __VA_ARGS__);                                  \
        std::exit(1);                                                           \
    }

enum LogLevel : unsigned char {
    LEVEL_DEBUG,
    LEVEL_INFO,
    LEVEL_WARN,
    LEVEL_ERROR,
    LEVEL_COUNT
};

extern "C" void reoxide_initialize_log();
extern "C" void reoxide_close_log();
extern "C" void reoxide_log(LogLevel level, const char* fmt, ...);
