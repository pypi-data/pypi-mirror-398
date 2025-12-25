// Writes to a CAN or TCP socket
#ifndef SCT_WRITE_H
#define SCT_WRITE_H

#include "sct_error.h"
#include "sct_sockets.h"
#include <linux/can.h>
#include <linux/can/raw.h>
#include <unistd.h>
#include <string.h>
#include <sys/socket.h>
#include <stdint.h>
#include <stdbool.h>

// Makes sure the write actually goes through
// Does an exponential backoff, with min of 30us and max of 1ms, total time with 100 iterations: ~100ms before giving up
static int _canwrite_checked(const int sockfd, const struct can_frame *frame) {
    int n_checks = 100, wait_time_us = 30, max_wait_time_us = 1000;

    for (int i = 0; i < n_checks; i++) {
        errno = 0;  // Clear the errno before writing
        int nbytes = write(sockfd, frame, sizeof(struct can_frame));
        if (nbytes == sizeof(struct can_frame)) return 0;  // Success, return now
        
        // Some kind of error, check if it's a buffer full error and sleep and try again if so
        if (errno == ENOBUFS) {
            usleep(wait_time_us);
            wait_time_us *= 1.5;
            if (wait_time_us > max_wait_time_us) wait_time_us = max_wait_time_us;
            continue;
        } else {
            RAISE(SCTERR_SYSTEM, "Can write error: %s", strerror(errno));
        }
    }
    RAISE(SCTERR_TIMEOUT, "Can write timed out");
}

/**
 * @brief Sends a CAN message on the specified interface.
 * 
 * Creates or retrieves a CAN socket for the interface and sends a CAN frame with the specified
 * parameters. Performs exponential backoff retry on buffer full conditions.
 * 
 * @param iface CAN interface name (e.g., "can0", "vcan0")
 * @param extended Whether to use extended CAN ID format (29-bit) or standard (11-bit)
 * @param can_id CAN identifier (max 0x7FF for standard, 0x1FFFFFFF for extended)
 * @param data Pointer to data buffer containing the CAN payload
 * @param dlc Data length code (number of bytes to send, max 8)
 * @return 0 on success, -1 on error (sets err_str)
 */
FUNCTION_EXPORT int cansend(const char *iface, bool extended, uint32_t can_id, uint8_t data[], uint8_t dlc) {
    int sock_idx = get_or_create_socket_index(SOCKET_TYPE_CAN, iface);
    if (sock_idx < 0) RAISE_TRACE(SCT_NO_OVERRIDE, "Failed to get CAN socket: \"%s\"", iface);
    int sockfd = sockets[sock_idx].sockfd;

    // Only a max of 29 bits are allowed for the CAN ID
    if (!extended && can_id > 0x7FF) RAISE(SCTERR_USER, "Standard CAN ID too large: %d", can_id)
    else if (can_id > 0x1FFFFFFF) RAISE(SCTERR_USER, "Extended CAN ID too large: %d", can_id)
    
    struct can_frame frame = {0};
    frame.can_id = extended ? (can_id | CAN_EFF_FLAG) : can_id;
    frame.can_dlc = dlc;
    memcpy(frame.data, data, dlc);
    
    if (_canwrite_checked(sockfd, &frame) != 0) RAISE_TRACE(SCT_NO_OVERRIDE, "Failed to write CAN frame: %s", iface);
    return 0;
}

/**
 * @brief Sends a Modbus TCP message to write a single register.
 * 
 * Creates or retrieves a TCP socket for the specified IP address and sends a Modbus TCP
 * packet with the specified transaction ID, unit ID, function code, register address, and value.
 * 
 * @param ip IP address and port of the Modbus TCP server (e.g., "192.168.1.100:502")
 * @param tid Transaction identifier for matching requests and responses
 * @param uid Unit identifier (Modbus slave address)
 * @param fcode Modbus function code (e.g., 0x06 for write single register)
 * @param reg_addr Register address to write to
 * @param reg_val Value to write to the register
 * @return 0 on success, -1 on error (sets err_str)
 */
FUNCTION_EXPORT int tcpsend_modbus(const char *ip, uint16_t tid, uint16_t uid, uint8_t fcode, uint16_t reg_addr, uint16_t reg_val) {
    int sock_idx = get_or_create_socket_index(SOCKET_TYPE_TCP, ip);
    if (sock_idx < 0) RAISE_TRACE(SCT_NO_OVERRIDE, "Failed to get TCP socket: %s", ip);
    int sockfd = sockets[sock_idx].sockfd;
    
    // Build Modbus TCP packet (12 bytes total)
    unsigned char packet[12], response[12];
    memset(packet, 0, sizeof(packet));
    
    // MBAP Header
    packet[0] = (tid >> 8) & 0xFF;      // Transaction ID high byte
    packet[1] = tid & 0xFF;             // Transaction ID low byte
    packet[2] = 0x00;                   // Protocol ID high (always 0 for Modbus TCP)
    packet[3] = 0x00;                   // Protocol ID low
    packet[4] = 0x00;
    packet[5] = 0x06;                   // Length: 6 bytes follow
    packet[6] = uid;                    // Unit Identifier
    
    // PDU
    packet[7] = fcode;                  // Function code
    packet[8] = (reg_addr >> 8) & 0xFF; // Register Address high
    packet[9] = reg_addr & 0xFF;        // Register Address low
    packet[10] = (reg_val >> 8) & 0xFF; // Register Value high
    packet[11] = reg_val & 0xFF;        // Register Value low
    
    ssize_t sent = send(sockfd, packet, sizeof(packet), 0);
    if (sent != sizeof(packet)) RAISE(SCTERR_SYSTEM, "Failed to send Modbus TCP packet: %s", ip);

    return 0;
}

#endif // SCT_WRITE_H