// Result struct that is passed to the handler functions
#ifndef SCT_RESULT_H
#define SCT_RESULT_H

#include "sct_error.h"
#include <stdint.h>

#define CAN_DATA_SIZE 8
#define TCP_BUF_SIZE 512
#define SOCKET_NAME_MAX_LEN 32

typedef enum SocketType {
    SOCKET_TYPE_UNINITIALIZED = 0,
    SOCKET_TYPE_CAN = 1,
    SOCKET_TYPE_TCP = 2,
    SOCKET_TYPE_ERROR = 3,
} SocketType;

// Message handler functions are called with a SocketResult struct containing either successfully parsed
// data or error information if parsing/reading failed.
typedef struct SocketResult {
    uint8_t result_type;
    uint8_t socket_name[SOCKET_NAME_MAX_LEN];

    // CAN specific fields
    uint32_t can_id;
    uint8_t data[CAN_DATA_SIZE];
    uint8_t dlc;
    
    // TCP specific fields
    uint8_t tcp_buffer[TCP_BUF_SIZE];
    uint32_t tcp_buf_len;
    
    // Error message during handling
    int32_t err_type;
    uint8_t err_msg[MAX_ERR_STR_LEN];
} SocketResult;

typedef void (*socket_result_handler_t)(SocketResult *result);

#endif // SCT_RESULT_H