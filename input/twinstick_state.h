/* Native Twin-Stick ABI. Bits 0..11 follow the game's twelve lever slots,
 * not an Xbox controller layout. Start and Pause are independent controls. */
#ifndef VON_TWINSTICK_STATE_H
#define VON_TWINSTICK_STATE_H
#include <stdint.h>
enum {
    VON_LEFT_UP=1u<<0, VON_LEFT_DOWN=1u<<1,
    VON_LEFT_LEFT=1u<<2, VON_LEFT_RIGHT=1u<<3,
    VON_RIGHT_UP=1u<<4, VON_RIGHT_DOWN=1u<<5,
    VON_RIGHT_LEFT=1u<<6, VON_RIGHT_RIGHT=1u<<7,
    VON_LEFT_TRIGGER=1u<<8, VON_RIGHT_TRIGGER=1u<<9,
    VON_LEFT_TOP=1u<<10, VON_RIGHT_TOP=1u<<11,
    VON_START=1u<<12, VON_PAUSE=1u<<13
};
typedef struct { uint32_t controls; } VonTwinState;
#endif
