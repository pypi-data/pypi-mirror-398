#include "pykimix_gpu.h"

extern "C" {

void draw_sprite(
    uint32_t* framebuffer,
    int fb_w,
    int fb_h,
    Sprite* sprite
) {
    for (int y = 0; y < sprite->h; y++) {
        for (int x = 0; x < sprite->w; x++) {
            int fb_x = sprite->x + x;
            int fb_y = sprite->y + y;

            if (fb_x < 0 || fb_y < 0 || fb_x >= fb_w || fb_y >= fb_h)
                continue;

            framebuffer[fb_y * fb_w + fb_x] =
                sprite->pixels[y * sprite->w + x];
        }
    }
}

}