#include <stdint.h>
#include <stdio.h>
#include <unistd.h>
extern int mrat_add(int, int, uint8_t *);
int main(int argc, char **argv) {
    if (argc != 2) return 2;
    FILE *out = fopen(argv[1], "w");
    if (!out) return 3;
    for (int i=0; i<200; i++) {
        uint8_t buffer[4] = {0, 255, 65, 0};
        int result = mrat_add(19, 23, buffer);
        fprintf(out, "%d,%d\n", result, buffer[2]);
        fflush(out);
        usleep(50000);
    }
    fclose(out);
    return 0;
}
