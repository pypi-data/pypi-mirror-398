#pragma once
#include <stdint.h>

extern "C" {

struct Sprite {
    int x;
    int y;
    int w;
    int h;
    uint32_t* pixels;
};

void draw_sprite(
    uint32_t* framebuffer,
    int fb_w,
    int fb_h,
    Sprite* sprite
);

}