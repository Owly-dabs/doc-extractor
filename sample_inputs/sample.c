// Adds two integers and returns the result
int add(int a, int b) {
    return a + b;
}

/** User-defined type representing a person */
struct Person {
    /** Person's age */
    int age;
};

/* Values for max_lazy_match, good_match and max_chain_length, depending on
 * the desired pack level (0..9). The values given below have been tuned to
 * exclude worst case performance for pathological files. Better values may be
 * found for specific files.
 */
typedef struct config_s {
    // reduce lazy search above this match length
    ush good_length;
    // do not perform lazy search above this match length
    ush max_lazy;    
    ush nice_length; // quit search above this match length //NOTE: Inline comments not supported 
    ush max_chain;
    compress_func func;
} config;