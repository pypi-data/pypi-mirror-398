/*unhuffme v.2.4 compiled from https://io.netgarage.org/me/*/

/*
 * Unhuffme by bla<blapost@gmail.com>
 *
 * Indispensable help by:
 *   Igor Skochinsky, phcoder, Corey Kallenberg, Xeno Kovah, Rafal Wojtczuk
 *
 * Copyright (C) 2015-2015 bla <blapost@gmail.com>
 * All rights reserved.
 */
#include "pch_format.h"
#include <string.h>
extern char dict_cpt_code[][16];
extern char dict_cpt_data[][16];
extern char dict_pch_code[][16];
extern char dict_pch_data[][16];

int fasthuff(unsigned char *huff, unsigned char *out, int outlen, char dict[][16], unsigned int *shape) {
    int pos = 0, outpos = 0;
    unsigned int bitbuf, symlen, s, r, idx;
    unsigned char t;

    idx = 0;
    bitbuf= 0;
    bitbuf = bitbuf << 8 | huff[0];
    bitbuf = bitbuf << 8 | huff[1];
    bitbuf = bitbuf << 8 | huff[2];
    bitbuf = bitbuf << 8 | huff[3];
    pos = 32;

    while(outpos < outlen){
        idx = 0;
        for(symlen = 7; bitbuf < shape[symlen - 6]; symlen++)
            idx += (((shape[symlen - 7] - 1 - shape[symlen - 6]) >> (32 - symlen))) + 1;

        r = shape[symlen - 7];
        r -= 1;
        r >>= 32 - symlen;
        r -= bitbuf >> (32 - symlen);
        r += idx;
        memcpy(out + outpos, dict[r] + 1, dict[r][0]);
        outpos += dict[r][0];

        while(symlen >  0){
            s = 8 - (pos & 7);
            t = huff[pos >> 3];
            t <<= 8 - s;
            s =(s > symlen) ? symlen : s;
            t >>= 8 - s;
            bitbuf <<= s;
            bitbuf |= t;
            symlen -= s;
            pos += s;
        }
    }
    return outpos;
}
int unhuff(unsigned char *huff, unsigned char *out, int outlen, int flags, int version) {
    unsigned int shape_pch[] = {0,0xec000000, 0x9b000000,0x5f000000,0x3bc00000,
                            0x27400000,0x12b00000,0x02700000,0x01600000,
                            0x00aa0000,0x001f0000,0x00050000,0x00018000,0};
    unsigned int shape_cpt[] = {0,0xfc000000, 0xaa000000, 0x6d800000,0x4a000000,
                            0x31200000,0x19f00000,0x07800000,0x00780000,0};
    unsigned int *shape;
    void *cfast, *dfast;

    switch(version){
        case 6:
            shape = shape_pch;
            cfast = dict_pch_code;
            dfast = dict_pch_data;
            break;
        default:
            shape = shape_cpt;
            cfast = dict_cpt_code;
            dfast = dict_cpt_data;
            break;
    }

    switch(flags) {
        case LUT_FLAG_UNCOMPRESSED:
            memcpy(out, huff, outlen);
            break;
        case LUT_FLAG_CODE:
            fasthuff(huff, out, outlen, cfast, shape);
            break;
        case LUT_FLAG_DATA:
            fasthuff(huff, out, outlen, dfast, shape);
            break;
    }

    return outlen;
}
