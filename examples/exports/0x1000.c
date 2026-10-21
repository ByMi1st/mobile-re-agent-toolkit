/* Synthetic example, not extracted from any application.
 * func-name: copy_record
 * func-address: 0x1000
 * callers: 0x2000
 */
void copy_record(char *out, const char *in, unsigned count) {
    memcpy(out, in, count);
}
