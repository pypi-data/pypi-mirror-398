// Error handling macros for socketcan_tcp
#ifndef SCT_ERROR_H
#define SCT_ERROR_H

#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <threads.h>
#include <stdint.h>

#define MAX_ERR_STR_LEN 1024

// Many errors will have a specific error type so it can be easily filtered/handled in the python code
typedef enum SCTErrorType {
    SCT_NO_OVERRIDE = -1,   // Use in a RAISE_TRACE-like macro to not override the lower error type
    SCTERR_NONE = 0,        // No error
    SCTERR_SYSTEM = 1,      // System level error
    SCTERR_OVERFLOW = 2,    // Buffer overflow or buffer full error
    SCTERR_USER = 3,        // Error due to invalid user input or settings
    SCTERR_TIMEOUT = 4,     // Timeout error
} SCTErrorType;

static thread_local char err_str[MAX_ERR_STR_LEN];
static thread_local SCTErrorType err_type = SCTERR_NONE;

/**
 * @brief Sets the thread-local error string with formatted output.
 * 
 * @param format Printf-style format string
 * @param ... Variable arguments for formatting
 */
static void set_err_str(const char *format, ...) {
    va_list args;
    va_start(args, format);
    vsnprintf(err_str, MAX_ERR_STR_LEN, format, args);
    va_end(args);
    err_str[MAX_ERR_STR_LEN-1] = '\0';
}

/**
 * @brief Retrieves the current thread-local error string.
 * 
 * @param err_str_out Output buffer to store the error string. Must be at least MAX_ERR_STR_LEN bytes.
 */
FUNCTION_EXPORT void get_err_str(char *err_str_out) {
    strncpy(err_str_out, err_str, MAX_ERR_STR_LEN-1);
    err_str_out[MAX_ERR_STR_LEN-1] = '\0';  // Ensure null termination
}

/**
 * @brief Returns the current thread-local error type.
 * 
 * @return The current SCTErrorType value cast to int32_t
 */
FUNCTION_EXPORT int32_t get_err_type(void) {
    return err_type;
}

/**
 * @brief Clears the thread-local error string and resets the error type to SCTERR_NONE.
 */
FUNCTION_EXPORT void clear_err_str(void) {
    err_str[0] = '\0';
    err_type = SCTERR_NONE;
}

// Updates the error type and message, calls the `finally` block, and returns -1. Set _err_type to
// SCT_NO_OVERRIDE to not override the current error type. Always overrides any previous error.
#define RAISE_FINALLY(_err_type, finally, fmt, ...) { \
    if (_err_type != SCT_NO_OVERRIDE) err_type = _err_type; \
    set_err_str(fmt, ##__VA_ARGS__); \
    finally; \
    return -1; \
}
// Same as RAISE_FINALLY, but without the `finally` block.
#define RAISE(_err_type, fmt, ...) RAISE_FINALLY(_err_type, ;, fmt, ##__VA_ARGS__)

// Updates the error type and message, calls the `finally` block, and returns -1. Set _err_type to
// SCT_NO_OVERRIDE to not override the current error type. Will append the current error message to the
// new error message to act as a pseudo-stack trace.
#define RAISE_TRACE_FINALLY(_err_type, finally, fmt, ...) { \
    if (_err_type != SCT_NO_OVERRIDE) err_type = _err_type; \
    char __tmp[MAX_ERR_STR_LEN]; \
    get_err_str(__tmp); \
    set_err_str(fmt "\n\tDue to error: %s", ##__VA_ARGS__, __tmp); \
    finally; \
    return -1; \
}
// Same as RAISE_TRACE_FINALLY, but without the `finally` block.
#define RAISE_TRACE(_err_type, fmt, ...) RAISE_TRACE_FINALLY(_err_type, ;, fmt, ##__VA_ARGS__)

#endif // SCT_ERROR_H