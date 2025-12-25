// Subscribe to multiple sockets and call a handler for each message received.
#ifndef SCT_POLL_H
#define SCT_POLL_H

#include "sct_error.h"
#include "sct_sockets.h"
#include <poll.h>
#include <pthread.h>
#include <stdbool.h>
#include <linux/can.h>
#include <linux/can/raw.h>
#include <unistd.h>
#include <string.h>
#include <time.h>

#define POLL_TIMEOUT_MS 1

// Array of file descriptors to poll in comms_subscribe_multi, and their indices in the sockets array
// These are currently out here instead of in the polling function because we might want to add the ability to
//  add/remove sockets while polling (not sure if we'll want to do this or not).
static struct pollfd poll_fds[MAX_SOCKETS] = {0};
static int num_poll_fds = 0;
static int poll_fd_inds[MAX_SOCKETS] = {0};

// Whether we should continue polling
static bool _continue_polling = false;
static pthread_mutex_t poll_mutex = PTHREAD_MUTEX_INITIALIZER;

/**
 * @brief Signals the polling loop to stop.
 * 
 * Sets the internal flag to stop the active polling loop in comms_subscribe_multi.
 * Thread-safe and can be called from signal handlers or other threads.
 */
FUNCTION_EXPORT void stop_polling() {
    _continue_polling = false;
}

/**
 * @brief Closes and clears all registered sockets.
 * 
 * Closes all socket file descriptors and resets the socket array.
 * Cannot be called while polling is active. Thread-safe.
 * 
 * @return 0 on success, -1 on error (sets err_str)
 */
FUNCTION_EXPORT int clear_all_sockets() {
    // Acquire the locks to make sure we can clear sockets while not polling and thread-safe
    if (_continue_polling) RAISE(SCTERR_USER, "Cannot clear sockets while polling");
    if (timed_mutex_acquire(&poll_mutex, MUTEX_TIMEOUT_NS)) RAISE_TRACE(SCT_NO_OVERRIDE, "Failed to acquire poll lock");
    if (timed_mutex_acquire(&sockets_mutex, MUTEX_TIMEOUT_NS)) 
        RAISE_TRACE_FINALLY(SCT_NO_OVERRIDE, mutex_release(&poll_mutex), "Failed to acquire sockets lock");

    // Close all of the sockets and reset the socket array
    bool had_error = false;
    for (int i = 0; i < num_sockets; i++) {
        if (close(sockets[i].sockfd) != 0) {
            had_error = true;
            set_err_str("Failed to close socket \"%s\": %s", sockets[i].name, strerror(errno));
            break;
        }
        sockets[i].sockfd = -1;
        sockets[i].type = SOCKET_TYPE_UNINITIALIZED;
    }
    num_sockets = 0;

    // Release the locks first, then return error if failed
    if (mutex_release(&poll_mutex) != 0) 
        RAISE_TRACE_FINALLY(SCT_NO_OVERRIDE, mutex_release(&sockets_mutex), "Failed to release poll lock");
    if (mutex_release(&sockets_mutex) != 0) RAISE_TRACE(SCT_NO_OVERRIDE, "Failed to release sockets lock");

    if (had_error) RAISE_TRACE(SCTERR_SYSTEM, "Failed to close all sockets");
    return 0;
}

static int val = 0;

// Reads a CAN message from the socket and calls the handler with the parsed message.
static int _handle_can_message(int sock_idx, SocketResult *result, socket_result_handler_t handler) {
    struct can_frame frame;
    int nbytes = read(sockets[sock_idx].sockfd, &frame, sizeof(frame));

    // Check if we failed to read a full can frame
    if (nbytes < 0) 
        RAISE(SCTERR_SYSTEM, "Failed to read CAN frame: %s", sockets[sock_idx].name)
    else if (nbytes < (int)sizeof(struct can_frame)) 
        RAISE(SCTERR_SYSTEM, "Incomplete CAN frame: %s", sockets[sock_idx].name)

    // Parse the CAN frame data and store into the result struct
    result->result_type = SOCKET_TYPE_CAN;
    result->can_id = frame.can_id & CAN_EFF_MASK;
    result->dlc = frame.can_dlc;
    if (result->dlc > CAN_DATA_SIZE) 
        RAISE(SCTERR_OVERFLOW, "CAN DLC %d exceeds maximum %d: %s", result->dlc, CAN_DATA_SIZE, sockets[sock_idx].name);
    memcpy(result->data, frame.data, result->dlc);

    handler(result);
    return 0;
}

// Reads a TCP message from the socket and calls the handler with the parsed message.
static int _handle_tcp_message(int sock_idx, SocketResult *result, socket_result_handler_t handler) {
    char buf[128];

    // Read available TCP data, check for any errors
    int n = read(sockets[sock_idx].sockfd, buf, sizeof(buf));
    if (n == 0) {
        // TODO: Close the socket
        RAISE(SCTERR_SYSTEM, "TCP connection closed: %s", sockets[sock_idx].name);
    }
    else if (n < 0) {
        if (errno != EWOULDBLOCK && errno != EAGAIN) 
            RAISE(SCTERR_SYSTEM, "Failed to read TCP frame: %s", sockets[sock_idx].name)
        return 0;
    }

    // We have data, append to TCP buffer
    if (sockets[sock_idx].tcp_buf_len + n > TCP_BUF_SIZE) 
        RAISE_FINALLY(SCTERR_OVERFLOW, sockets[sock_idx].tcp_buf_len = 0, "TCP overflow: %s", sockets[sock_idx].name)
    memcpy(&sockets[sock_idx].tcp_buffer[sockets[sock_idx].tcp_buf_len], buf, n);
    sockets[sock_idx].tcp_buf_len += n;
    
    // Process complete Modbus messages
    while (sockets[sock_idx].tcp_buf_len >= 7) {
        uint8_t* buf_ptr = sockets[sock_idx].tcp_buffer;
        uint16_t total_len = ((uint16_t)(buf_ptr[4] << 8) | (uint16_t)(buf_ptr[5])) + 6;

        if (total_len > TCP_BUF_SIZE) {
            sockets[sock_idx].tcp_buf_len = 0;
            RAISE(SCTERR_OVERFLOW, "TCP frame length %d too long: %s", total_len, sockets[sock_idx].name);
        }
        
        if (sockets[sock_idx].tcp_buf_len < total_len) break;  // Wait for complete frame
        
        // Copy the frame to the result and call the handler
        memcpy(result->tcp_buffer, buf_ptr, total_len);
        result->tcp_buf_len = total_len;
        handler(result);
        
        // Remove processed frame
        sockets[sock_idx].tcp_buf_len -= total_len;
        memmove(buf_ptr, buf_ptr + total_len, sockets[sock_idx].tcp_buf_len);
    }

    return 0;
}

// Rebuilds the poll_fds array based on the endpoints array for comms_subscribe_multi polling
// Assumes you have acquired the poll lock already
static int _rebuild_poll_fds(const char *endpoints[], int count) {
    if (!endpoints || count <= 0) RAISE(SCTERR_USER, "Did not supply any endpoints to subscribe to");
    if (count > MAX_SOCKETS) RAISE(SCTERR_USER, "Too many endpoints: %d, max: %d", count, MAX_SOCKETS)

    if (timed_mutex_acquire(&sockets_mutex, MUTEX_TIMEOUT_NS)) 
        RAISE_TRACE_FINALLY(SCT_NO_OVERRIDE, mutex_release(&poll_mutex), "Failed to acquire sockets lock");

    // Create or Get all of the sockets and their file descriptors
    for (int i = 0; i < count; i++) {
        const char *ep = endpoints[i];

        // Determine the socket type based on the endpoint name
        SocketType type = SOCKET_TYPE_TCP;
        if (strncmp(ep, CAN_PREFIX, strlen(CAN_PREFIX)) == 0 || strncmp(ep, VCAN_PREFIX, strlen(VCAN_PREFIX)) == 0) {
            type = SOCKET_TYPE_CAN;
        }

        // Get or create the socket and add it to the poll_fds array
        int sock_idx = _get_or_create_socket_index_locked(type, ep);
        if (sock_idx < 0) RAISE_TRACE_FINALLY(
            SCT_NO_OVERRIDE, 
            mutex_release(&sockets_mutex), 
            "Failed get/create socket: %s", ep
        )
        
        poll_fd_inds[i] = sock_idx;
        poll_fds[i].fd = sockets[sock_idx].sockfd;
        poll_fds[i].events = POLLIN;
    }

    // Release the locks first, then return error if failed
    if (mutex_release(&sockets_mutex) != 0) RAISE_TRACE(SCT_NO_OVERRIDE, "Failed to release sockets lock");

    return 0;
}

/**
 * @brief Subscribes to multiple endpoints and polls them for incoming messages.
 * 
 * Creates or retrieves sockets for the specified endpoints (CAN or TCP) and enters a polling loop
 * that continuously monitors all sockets for incoming data. When data arrives, the appropriate
 * handler is called to process the message. The loop continues until stop_polling() is called.
 * 
 * Message handlers are called with a SocketResult struct containing either successfully parsed
 * data or error information if parsing/reading failed.
 * 
 * @param endpoints Array of endpoint strings (e.g., "can0", "vcan0", or TCP addresses)
 * @param count Number of endpoints in the array (must be > 0 and <= MAX_SOCKETS)
 * @param handler Callback function invoked for each received message or error
 * @return 0 on success, -1 on error (sets err_str)
 */
FUNCTION_EXPORT int comms_subscribe_multi(const char *endpoints[], int count, socket_result_handler_t handler) {
    if (timed_mutex_acquire(&poll_mutex, MUTEX_TIMEOUT_NS)) RAISE_TRACE(SCT_NO_OVERRIDE, "Failed to acquire poll lock");
    if (_rebuild_poll_fds(endpoints, count) != 0) 
        RAISE_TRACE_FINALLY(SCT_NO_OVERRIDE, mutex_release(&poll_mutex), "Failed to build poll fds");
    _continue_polling = true;
    
    // Begin the infinite polling loop
    int handle_result = 0;
    SocketResult result;
    while (_continue_polling) {
        // Poll for new data. Return after POLL_TIMEOUT_MS milliseconds if no data to check continue_polling
        int poll_result = poll(poll_fds, count, POLL_TIMEOUT_MS);

        // Check for errors, and continue polling if there was no data available.
        if (poll_result < 0) 
            RAISE_FINALLY(SCTERR_SYSTEM, mutex_release(&poll_mutex), "Error in poll: %s", strerror(errno))
        if (poll_result == 0) continue;  // No data available

        // Process each socket that has data available
        for (int i = 0; i < count; i++) {
            if (poll_fds[i].revents & POLLIN) {
                // Copy the socket name and type to the result
                strncpy((char *)result.socket_name, sockets[poll_fd_inds[i]].name, SOCKET_NAME_MAX_LEN-1);
                result.socket_name[SOCKET_NAME_MAX_LEN-1] = '\0';
                result.result_type = sockets[poll_fd_inds[i]].type;

                // Handle the message from the socket and store the result
                if (sockets[poll_fd_inds[i]].type == SOCKET_TYPE_CAN)
                    handle_result = _handle_can_message(poll_fd_inds[i], &result, handler);
                else
                    handle_result = _handle_tcp_message(poll_fd_inds[i], &result, handler);
                
                // If an error occurred, set the result type to error and copy the error message
                if (handle_result < 0) {
                    result.result_type = SOCKET_TYPE_ERROR;
                    get_err_str(result.err_msg);
                    result.err_type = get_err_type();
                    handler(&result);
                }
            }
        }
    }
    
    if (mutex_release(&poll_mutex) != 0) RAISE_TRACE(SCT_NO_OVERRIDE, "Failed to release poll lock");
    return 0;
}

#endif // SCT_POLL_H