/* Pure mapping, shared by the Windows reader and host-side tests. */
#ifndef VON_TANITA_MAP_H
#define VON_TANITA_MAP_H
#include <stdint.h>
typedef struct {
    uint16_t buttons;
    uint8_t lt, rt;
    int16_t x, y, z, rz;
} TanitaState;
static int16_t tanita_axis(int32_t v, int32_t lo, int32_t hi, int invert) {
    int64_t scaled = ((int64_t)v - lo) * 4, span = (int64_t)hi - lo;
    int sign = scaled < span ? -1 : scaled > span * 3 ? 1 : 0;
    return (int16_t)(sign * (invert ? -32767 : 32767));
}
static TanitaState tanita_map(const int32_t *v, unsigned b,
    int32_t xl, int32_t xh, int32_t yl, int32_t yh,
    int32_t zl, int32_t zh, int32_t rl, int32_t rh,
    int32_t hl, int32_t hh) {
    /* Observed top switches are zero-based 6/7; retain 10/11 dash aliases. */
    static const uint16_t buttons[13] = {
        0x4000,0x1000,0x2000,0x8000,0,0,0x140,0x280,0x20,0x10,0x100,0x200,0};
    static const uint16_t hats[8] = {1,9,8,10,2,6,4,5};
    TanitaState s = {0};
    unsigned i;
    for(i=0;i<13;++i) if(b & (1u<<i)) s.buttons |= buttons[i];
    if (hh-hl == 7 && v[4] >= hl && v[4] <= hh) s.buttons |= hats[v[4]-hl];
    else if (hh-hl == 3 && v[4] >= hl && v[4] <= hh) s.buttons |= hats[(v[4]-hl)*2];
    s.lt = (b & 16) ? 255 : 0; s.rt = (b & 32) ? 255 : 0;
    s.x=tanita_axis(v[0],xl,xh,0); s.y=tanita_axis(v[1],yl,yh,1);
    s.z=tanita_axis(v[2],zl,zh,0); s.rz=tanita_axis(v[3],rl,rh,1);
    return s;
}
#endif
