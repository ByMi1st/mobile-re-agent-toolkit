/* Synthetic, source-built test fixture. No application code. */
#include <stdint.h>
__attribute__((visibility("default"), noinline))
int mrat_add(int a, int b, uint8_t *buffer) {
    buffer[2] ^= 1;
    return a + b;
}
