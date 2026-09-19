/* Characterized adapters only. Another DC variant needs its own identity
 * and decoder; revision/interface strings are not profile identities. */
#ifndef VON_RAPHNET_MAP_H
#define VON_RAPHNET_MAP_H
#include "twinstick_state.h"
enum { VON_HID_TANITA, VON_HID_DC_V1, VON_HID_SATURN_V2 };
static inline int von_hid_identity(unsigned vid, unsigned pid, unsigned rev) {
    if (vid==0x1f4f && pid==0x9001 && rev==0x0200) return VON_HID_TANITA;
    if (vid==0x289b && pid==0x0008) return VON_HID_DC_V1;
    if (vid==0x289b && pid==0x0043) return VON_HID_SATURN_V2;
    return -1;
}
static inline uint32_t raphnet_dc_v1(uint32_t buttons) {
    /* Zero-based tester buttons, indexed by the semantic ABI bit. */
    static const unsigned source[14]={4,5,6,7,12,13,14,15,10,2,9,1,3,11};
    uint32_t controls=0;
    for (unsigned i=0;i<14;++i)
        if (buttons & (1u<<source[i])) controls |= 1u<<i;
    return controls;
}
static inline int raphnet_axis(int32_t value, int32_t min, int32_t max) {
    /* Descriptor-relative digital thresholds: inclusive middle half neutral.
     * int64 avoids overflow for signed or wide HID logical ranges. */
    int64_t position=((int64_t)value-min)*4, range=(int64_t)max-min;
    if (range<=0 || value<min || value>max) return 0;
    return position<range?-1:position>3*range?1:0;
}
static inline uint32_t raphnet_saturn_v2(uint32_t buttons,
        int32_t x, int32_t y, int32_t xmin, int32_t xmax,
        int32_t ymin, int32_t ymax) {
    static const unsigned source[9]={3,2,0,4,6,1,7,5,8};
    uint32_t controls=0;
    int horizontal=raphnet_axis(x,xmin,xmax), vertical=raphnet_axis(y,ymin,ymax);
    if (horizontal<0) controls |= VON_LEFT_LEFT;
    if (horizontal>0) controls |= VON_LEFT_RIGHT;
    if (vertical<0) controls |= VON_LEFT_UP;
    if (vertical>0) controls |= VON_LEFT_DOWN;
    for (unsigned i=0;i<9;++i)
        if (buttons & (1u<<source[i])) controls |= 1u<<(i+4);
    return controls; /* This hardware has no physical Pause control. */
}
#endif
