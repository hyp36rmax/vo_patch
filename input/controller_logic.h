/* Pure capture/ownership rules, also exercised on the build host. */
#ifndef VON_CONTROLLER_LOGIC_H
#define VON_CONTROLLER_LOGIC_H
#include <stdint.h>
#include <string.h>
typedef struct { int source, attempted; } VonOwner;
/* Sources 0..3 XInput, 4..5 Tanita, 6..7 DC, 8..9 Saturn.
 * Physical HID paths remain reserved independently within each family. */
static inline int von_source_family(int source) {
    return source < 0 || source > 9 ? -1 : source < 4 ? 0 : (source-2)/2;
}
static inline int von_kind_family(unsigned kind) {
    return kind==5?1:kind==7?2:kind==8?3:
           (kind==1 || kind==2 || kind==4 || kind==6)?0:-1;
}
static inline int von_source_first(unsigned kind) {
    int family=von_kind_family(kind);
    return family<0?-1:family==0?0:2+family*2;
}
static inline int von_source_end(unsigned kind) {
    int first=von_source_first(kind);
    return first<0?-1:first+(first?2:4);
}
/* Neutral before a fresh Start edge; simultaneous claim requests are rejected. */
static inline int von_start_edge(unsigned *ready, unsigned connected, unsigned held) {
    unsigned edges=*ready & connected & held;
    *ready=connected & ~held;
    if (!edges) return -1;
    if (edges & (edges-1)) return -2;
    for (int i=0;i<10;++i) if (edges==(1u<<i)) return i;
    return -1;
}
static int von_claim(VonOwner owner[2], unsigned player, int source) {
    if (player > 1 || source < 0 || source > 9)
        return 0;
    if (owner[1-player].source == source) {
        int previous = owner[player].source;
        owner[1-player].source = previous >= 0 && von_source_family(previous) == von_source_family(source) ? previous : -1;
        owner[1-player].attempted = owner[1-player].source >= 0;
    }
    owner[player].source = source;
    owner[player].attempted = 1;
    return 1;
}
static int von_owned_source(const VonOwner owner[2], unsigned player, unsigned kind) {
    return player < 2 && owner[player].source >= 0 &&
           von_source_family(owner[player].source) == von_kind_family(kind);
}
static uint32_t von_inputs(uint16_t b, unsigned lt, unsigned rt,
                          int lx, int ly, int rx, int ry, int threshold) {
    uint32_t m = 0;
    static const uint16_t masks[6] = {0x1000,0x2000,0x4000,0x8000,0x100,0x200};
    unsigned i;
    for (i=0;i<6;++i) if (b & masks[i]) m |= 1u<<i;
    if (lt>64) m|=1u<<6;
    if (rt>64) m|=1u<<7;
    if (ly>threshold) m|=1u<<8;
    if (ly<-threshold) m|=1u<<9;
    if (lx<-threshold) m|=1u<<10;
    if (lx>threshold) m|=1u<<11;
    if (ry>threshold) m|=1u<<12;
    if (ry<-threshold) m|=1u<<13;
    if (rx<-threshold) m|=1u<<14;
    if (rx>threshold) m|=1u<<15;
    for (i=0;i<4;++i) if (b & (1u<<i)) m |= 1u<<(16+i);
    return m;
}
typedef struct { int released; } VonCapture;
/* Require complete neutral first. Ambiguous diagonals/chords must be retried. */
static int von_capture(VonCapture *capture, uint32_t mask) {
    unsigned i;
    if (!mask) { capture->released = 1; return 0; }
    if (!capture->released) return 0;
    capture->released = 0;
    if (mask & (mask-1)) return 0;
    for (i=0;i<20;++i) if (mask == (1u<<i)) return 0xe0+(int)i;
    return 0;
}
#endif
