#include "pykimix_utils.h"

extern "C" {

float clamp(float v, float min, float max) {
    if (v < min) return min;
    if (v > max) return max;
    return v;
}

}