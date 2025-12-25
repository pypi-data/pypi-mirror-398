// Handles the creation and management of sockets
#ifndef SCT_SOCKETS_H
#define SCT_SOCKETS_H

#include "sct_error.h"
#include "sct_result.h"
#include <string.h>
#include <stdio.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <net/if.h>
#include <fcntl.h>
#include <unistd.h>
#include <linux/can.h>
#include <linux/can/raw.h>
#include <sys/ioctl.h>

#define CAN_PREFIX "can"
#define VCAN_PREFIX "vcan"

#define MAX_SOCKETS 16

typedef struct SocketEntry {
    int sockfd;
    SocketType type;
    char name[SOCKET_NAME_MAX_LEN];  // Contains either the CAN interface name or the IP address endpoint

    // Only used for TCP sockets
    uint8_t tcp_buffer[TCP_BUF_SIZE];  // The buffer for the TCP socket
    uint16_t tcp_buf_len;  // The length of the TCP buffer
} SocketEntry;

// All of the currently open sockets
static SocketEntry sockets[MAX_SOCKETS] = {0};
static int num_sockets = 0;
static pthread_mutex_t sockets_mutex = PTHREAD_MUTEX_INITIALIZER;

// Adds a new socket to the sockets array and returns the index. Returns -1 if the socket could not be added.
// Assumes you have acquired the sockets mutex already
static int add_new_socket(int sockfd, SocketType type, const char *name) {
    if (num_sockets >= MAX_SOCKETS) RAISE(SCTERR_USER, "Max number of sockets reached");

    sockets[num_sockets].type = type;
    strncpy(sockets[num_sockets].name, name, SOCKET_NAME_MAX_LEN-1);
    sockets[num_sockets].name[SOCKET_NAME_MAX_LEN-1] = '\0';
    sockets[num_sockets].sockfd = sockfd;
    return num_sockets++;
}

// Creates a new TCP socket and returns the index in the sockets array.
// Assumes you have acquired the sockets mutex already
static int create_tcp_socket(const char *endpoint) {    
    // Parse the IP address and optionally the port from the endpoint
    char ip[64];
    int port;
    int consumed = -1;    
    if (sscanf(endpoint, "%63[^:]:%d%n", ip, &port, &consumed) != 2) 
        RAISE(SCTERR_USER, "Endpoint must be in the format 'IP:port' (got '%s')", endpoint);
    if (consumed != strnlen(endpoint, sizeof(ip))) RAISE(SCTERR_USER, "Failed to parse IP/port from '%s'", endpoint);

    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) RAISE(SCTERR_SYSTEM, "Failed to create TCP socket: %s:%d", ip, port);

    struct sockaddr_in server_addr = {0};
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);

    if (inet_pton(AF_INET, ip, &server_addr.sin_addr) <= 0) 
        RAISE_FINALLY(SCTERR_USER, close(sockfd), "Invalid IP address: %s", ip);
    if (connect(sockfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0)
        RAISE_FINALLY(SCTERR_SYSTEM, close(sockfd), "Failed to connect to server: %s:%d", ip, port);

    // Set Nonblocking
    int flags = fcntl(sockfd, F_GETFL, 0);
    if (flags < 0) RAISE_FINALLY(SCTERR_SYSTEM, close(sockfd), "Failed to get file descriptor flags: %d", sockfd);
    if (fcntl(sockfd, F_SETFL, flags | O_NONBLOCK) < 0)
        RAISE_FINALLY(SCTERR_SYSTEM, close(sockfd), "Failed to set nonblocking mode for TCP socket: %s:%d", ip, port);

    int result = add_new_socket(sockfd, SOCKET_TYPE_TCP, ip);
    if (result < 0) RAISE_TRACE_FINALLY(SCT_NO_OVERRIDE, close(sockfd), "Failed to add TCP socket: %s:%d", ip, port);
    return result;
}

// Creates a new CAN socket and returns the index in the sockets array.
// Assumes you have acquired the sockets mutex already
static int create_can_socket(const char *ifname) {
    if (strnlen(ifname, IFNAMSIZ) >= IFNAMSIZ) RAISE(SCTERR_USER, "CAN interface name too long: %s", ifname);
    int sockfd = socket(PF_CAN, SOCK_RAW, CAN_RAW);
    if (sockfd < 0) RAISE(SCTERR_SYSTEM, "Failed to create CAN socket: %s", ifname);
    
    // Get the system-level index of the CAN interface
    struct ifreq ifr;
    strncpy(ifr.ifr_name, ifname, IFNAMSIZ-1);
    if (ioctl(sockfd, SIOCGIFINDEX, &ifr) < 0) 
        RAISE_FINALLY(SCTERR_SYSTEM, close(sockfd), "Failed ioctl on CAN socket: %s", ifname);

    // Enable loopback mode on vcan interfaces
    if (strncmp(ifname, VCAN_PREFIX, strlen(VCAN_PREFIX)) == 0) {
        int loopback = 1;
        if (setsockopt(sockfd, SOL_CAN_RAW, CAN_RAW_RECV_OWN_MSGS, &loopback, sizeof(loopback)) < 0)
            RAISE_FINALLY(SCTERR_SYSTEM, close(sockfd), "Failed to set loopback mode for CAN socket: %s", ifname);
    }
    
    // Bind the socket to the CAN interface
    struct sockaddr_can addr;
    addr.can_family = AF_CAN;
    addr.can_ifindex = ifr.ifr_ifindex;
    if (bind(sockfd, (struct sockaddr *)&addr, sizeof(addr)) < 0) 
        RAISE_FINALLY(SCTERR_SYSTEM, close(sockfd), "Failed to bind CAN socket: %s", ifname);
    
    // Socket created, add it to the sockets array
    int result = add_new_socket(sockfd, SOCKET_TYPE_CAN, ifname);
    if (result < 0) RAISE_TRACE_FINALLY(SCT_NO_OVERRIDE, close(sockfd), "Failed to add CAN socket: %s", ifname);
    return result;
}

// Returns the index in the sockets array of the socket with the given info, or creates a new one if not found.
// Assumes you have acquired the sockets mutex already
static int _get_or_create_socket_index_locked(SocketType type, const char *name) {
    for (int i = 0; i < num_sockets; i++) {
        if (sockets[i].type == type && strcmp(sockets[i].name, name) == 0) return i;
    }

    int result = -1;
    switch (type) {
        case SOCKET_TYPE_TCP:
            result = create_tcp_socket(name);
            break;
        case SOCKET_TYPE_CAN:
            result = create_can_socket(name);
            break;
    }

    if (result < 0) RAISE_TRACE(SCT_NO_OVERRIDE, "Failed to create socket: \"%s\"", name);
    return result;
}

// Returns the index in the sockets array of the socket with the given info, or creates a new one if not found.
// Will acquire the sockets mutex when running
static int get_or_create_socket_index(SocketType type, const char *name) {
    if (timed_mutex_acquire(&sockets_mutex, MUTEX_TIMEOUT_NS)) 
        RAISE_TRACE(SCT_NO_OVERRIDE, "Failed to acquire sockets lock");
    int result = _get_or_create_socket_index_locked(type, name);
    if (mutex_release(&sockets_mutex) != 0) RAISE_TRACE(SCT_NO_OVERRIDE, "Failed to release sockets lock");
    return result;  // No need to add an extra error message here
}

#endif // SCT_SOCKETS_H