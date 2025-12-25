/*unhuffme v.2.4 compiled from https://io.netgarage.org/me/*/

/*
 * Unhuffme by bla<blapost@gmail.com>
 *
 * Copyright (C) 2015-2015 bla <blapost@gmail.com>
 * All rights reserved.
 */
#include "pch_format.h"
#include <stdio.h>
#include <ctype.h>
#include <stdarg.h>

void __print(char *fmt, ...) {
    va_list arg;
    va_start(arg, fmt);
    vfprintf(stdout, fmt, arg);
    va_end(arg);
}


void print_flash_desc(struct flash_descr *descr){
    __print("number of flash regions: %d\n", 1 + descr->nr);
}
void print_flash_regions(struct flash_region *regions, int count){
    int i;
    for(i = 0; i <= count ; ++i){
        __print("\tregion: %d in range: %08x-%08x\n", i, regions[i].end << 12 |0xfff, regions[i].begin << 12);
    }
}
void print_fpt_desc(struct MeFPT* fpt){
    unsigned int i, j;
    unsigned char c;

    __print("\nFlash partition table (%d entries):\n", fpt->numentries);
    for(i = 0; i < fpt->numentries; ++i){
        __print("\tpartition:  ");
        for(j = 0; j < 4; j++){
            c = fpt->partitions[i].name[j];
            __print("%c", isprint(c)? c:'_');
        }
        __print("(type:%x) ", fpt->partitions[i].type);
        __print("at %08x, ", fpt->partitions[i].offset);
        __print("size:%x\n", fpt->partitions[i].size);
    }
    __print("\n");
}
void print_manifest(struct MeManifestHeader *manifest){
    const char* comptype[] = {"uncompressed", "huffman", "lzma"};
    int major = manifest->majorversion;
    int minor = manifest->minorversion;
    int hotfix = manifest->hotfixversion;
    int build = manifest->buildversion;
    unsigned int i;

    __print("Code partition: %.*s", 12, manifest->partitionname);
    __print("(%d modules, v%d.%d.%d.%d)\n", manifest->nummodules, major, minor, hotfix, build);
    for(i = 0; i < manifest->nummodules; ++i){
        char *name = manifest->modules[i].name;
        int cflags = manifest->modules[i].flags >> 4 & 7;
        int offset = manifest->modules[i].fileoffset;
        int ldaddr = manifest->modules[i].base;
        int size = manifest->modules[i].size_uncompressed;
        __print("\t\t%2d %16s %8s at:%8x va:%8x+%x\n", i, name, comptype[cflags], offset, ldaddr, size);
    }
    __print("\n");
}
void print_tag(struct TagHdr *tag){
    __print("TAG %.*s %d\n", 4, tag->name, tag->field[0]);
}
void print_unpackres(struct MeModuleHdr2 *mhdr, char* res){
    int j;
    __print("%14.*s\t", 12,mhdr->name);
    for(j = 0; j < 32; j++)
         __print("%02x", mhdr->hash[31 - j]);

    __print(" %s\n", res);
}
