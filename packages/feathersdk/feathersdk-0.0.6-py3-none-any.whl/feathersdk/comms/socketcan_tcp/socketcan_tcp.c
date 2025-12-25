// Compile with: gcc -fvisibility=hidden -shared -O3 -march=native -fPIC -o libsocketcantcp.so socketcan_tcp.c
#define _FUNC_VISIBILITY __attribute__((visibility("default")))
#ifdef __cplusplus
#define FUNCTION_EXPORT _FUNC_VISIBILITY extern "C"
#else
#define FUNCTION_EXPORT _FUNC_VISIBILITY
#endif

#include <pthread.h>
#include <time.h>
#include <errno.h>
#include <string.h>
#include "sct_error.h"

#define NANOS_PER_SEC 1000000000ULL
#define MUTEX_TIMEOUT_NS (NANOS_PER_SEC / 1000ULL)  // 1ms timeout waiting for mutex acquisition

// Acquires a mutex with a timeout
int timed_mutex_acquire(pthread_mutex_t *mutex, int timeout_ns) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);

    ts.tv_sec  += timeout_ns / NANOS_PER_SEC;
    ts.tv_nsec += (timeout_ns % NANOS_PER_SEC);

    // Normalize in case tv_nsec overflowed
    if (ts.tv_nsec >= NANOS_PER_SEC) {
        ts.tv_sec++;
        ts.tv_nsec -= NANOS_PER_SEC;
    }

    int result = pthread_mutex_timedlock(mutex, &ts);
    if (result == ETIMEDOUT) RAISE(SCTERR_TIMEOUT, "Timed out waiting for mutex");
    if (result != 0) RAISE(SCTERR_SYSTEM, "Failed to acquire mutex: %s", strerror(result));
    return 0;
}

int mutex_release(pthread_mutex_t *mutex) {
    int result = pthread_mutex_unlock(mutex);
    if (result != 0) RAISE(SCTERR_SYSTEM, "Failed to release mutex: %s", strerror(result));
    return 0;
}

#include "sct_sockets.h"
#include "sct_write.h"
#include "sct_poll.h"
