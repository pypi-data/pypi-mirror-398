#include "pykimix_math.h"

extern "C" {

int add(int a, int b) {
    return a + b;
}

int sub(int a, int b) {
    return a - b;
}

int mul(int a, int b) {
    return a * b;
}

float lerp(float a, float b, float t) {
    return a + (b - a) * t;
}

}