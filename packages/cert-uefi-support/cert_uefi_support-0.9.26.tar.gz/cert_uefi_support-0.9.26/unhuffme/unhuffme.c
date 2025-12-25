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
#include <stdio.h>
#include <fcntl.h>
#include <string.h>
#include <sys/stat.h>
#include <stdlib.h>
#include "pch_format.h"

int unhuff(unsigned char *huff, unsigned char *out, int outlen, int flags, int version);
void print_flash_desc(struct flash_descr *descr);
void print_flash_regions(struct flash_region *regions, int count);
void print_fpt_desc(struct MeFPT* fpt);
void print_manifest(struct MeManifestHeader *manifest);
void print_tag(struct TagHdr *tag);
void print_unpackres(struct MeModuleHdr2 *mhdr, char* res);
int checksha256(char *data, int size,unsigned char* targethash);

unsigned char *mapped;

int isvalid_flash_descr(struct flash_descr *fdesc){
    return fdesc->magic == FLASHMAGIC;
}
int isvalid_FPT(struct MeFPT *fpt)  {
    return fpt->magic == FPTMAGIC;
}
int isvalid_MeManifest(struct MeManifestHeader *manifest){
    return manifest->magic == MEMANIFEST2_MAGIC;
}
int isvalid_LUT(struct LutHdr *lhdr){
    return (lhdr->magic >> 8) == LUT_MAGIC;
}

char scratch[1<<24];
int dump_huff_module(struct MeModuleHdr2 *mhdr, struct LutHdr *glut, int version){
    unsigned int i, opos = 0;
    uint32_t va_base, cflags;
    uint32_t pos, endpos, outsize;
    unsigned char out[10240], *huff;
    char filename[4096];
    FILE* fp;

    pos = mhdr->base;
    endpos = pos + mhdr->size_uncompressed;
    va_base = glut->addrbase + 0x10000000;

    for(; pos < endpos; pos += glut->pagesize){
        i = (pos - va_base) / glut->pagesize;
        if (i >= glut->chunkcount || glut->entries[i].flags == LUT_FLAG_EMPTY)
            continue;

        huff = &mapped[glut->entries[i].addr];
        cflags = glut->entries[i].flags;

        unhuff(huff, out, glut->pagesize, cflags, version);
        outsize = glut->pagesize;
        if(endpos - pos < outsize)
            outsize = endpos - pos;

        memcpy(scratch + opos, out, outsize);
        opos += outsize;
    }

    snprintf(filename, 4096, "mod/%.*s-%08x.mod", 12, mhdr->name, mhdr->base + mhdr->size_uncompressed - opos);
    fp = fopen(filename, "w");
    fwrite(scratch, opos, 1, fp);
    fclose(fp);

    return checksha256(scratch, opos, mhdr->hash);
}

void dump_raw_module(struct MeModuleHdr2 *mhdr, char* base, char *fnameformat){
    char filename[4096];
    FILE* fout;

    snprintf(filename, 4096, fnameformat, mhdr->name, mhdr->base);
    fout = fopen(filename, "w");
    fwrite(&base[mhdr->fileoffset], mhdr->size_compressed, 1, fout);
    fclose(fout);

}
void dump_modules(struct MeManifestHeader *manifest, struct LutHdr* glut){
    struct LutHdr*  llut;
    struct MeModuleHdr2 *mhdr;
    int res;
    unsigned int i, first = 1;
    int version = manifest->majorversion;


    for(i = 0; i < manifest->nummodules; ++i){
        mhdr = &manifest->modules[i];
        switch(mhdr->flags >> 4 & 7) {
            case C_UNCOMPRESSED:
                dump_raw_module(mhdr, manifest->base, "mod/%s-%08x.mod");
                print_unpackres(mhdr, "plain");
                break;
            case C_LZMA:
                dump_raw_module(mhdr, manifest->base, "mod/%s-%08x.mod.lzma");
                print_unpackres(mhdr, "lzma");
                break;
            case C_HUFFMAN:
                llut = (void*) &manifest->base[mhdr->fileoffset];
                if(isvalid_LUT(llut) && first) {
                    first = 0;
                    glut = (void*) &llut->entries[llut->chunkcount];
                    if(!isvalid_LUT(glut))
                       glut = llut;
                    mapped -= &mapped[glut->huffstart] - (unsigned char*)&glut->entries[glut->chunkcount];
                }

                res = dump_huff_module(mhdr, glut, version);
                print_unpackres(mhdr, (res == 1) ? "[MATCH]" : "incomplete");

                break;
        }
    }
}


int parse_update_format(){
    struct MeManifestHeader *manifest, *updman;
    struct TagHdr *tag, *tagstart, *tagend;
    struct TagUDC *udc;
    struct TagGLT *glt;
    struct LutHdr *glut = 0;

    updman = (void*)mapped;
    if(!isvalid_MeManifest(updman))
        return -1;
    print_manifest(updman);
    dump_modules(updman, 0);

    tagstart = (void*) &updman->modules[updman->nummodules];
    tagend = (void*)&updman->base[updman->size * 4];
    for(tag = tagstart; tag < tagend; tag += tag->field[0]) {
        if(strncmp(tag->name, "$UDC",4))
            continue;

        udc = (void*) tag;
        manifest = (void*) &udc->name[udc->offset];

        if(!isvalid_MeManifest(manifest))
            return -1;
        print_manifest(manifest);
    }

    for(tag = tagstart; tag < tagend; tag += tag->field[0]){
        if(strncmp(tag->name, "$GLT",4))
            continue;

        glt = (void*) tag;
        if(!glt->offset || !glt->size)
            continue;

        glut = (void*) &glt->name[glt->offset];
        if(!isvalid_LUT(glut))
            return -1;
    }

    for(tag = tagstart; tag < tagend; tag += tag->field[0]) {
        if(strncmp(tag->name, "$UDC",4))
            continue;

        udc = (void*) tag;
        manifest = (void*) &udc->name[udc->offset];
        dump_modules(manifest, glut);
    }
    return 0;
}


int parse_full_format(struct MeFPT *fpt){
    struct MeManifestHeader *manifest;
    struct LutHdr *glut = 0;
    unsigned int i;

    if(!isvalid_FPT(fpt))
        return -1;
    print_fpt_desc(fpt);

    for(i = 0; i < fpt->numentries; ++i){
        if(fpt->partitions[i].type != PT_CODE)
            continue;

        manifest = (void*) &mapped[fpt->partitions[i].offset];
        if(!isvalid_MeManifest(manifest))
            return -1;
        print_manifest(manifest);
    }

    for(i = 0; i < fpt->numentries; ++i){
        if(strncmp(fpt->partitions[i].name, "GLUT", 4))
            continue;

        glut = (void*) &mapped[fpt->partitions[i].offset];
        if(!isvalid_LUT(glut))
            return -1;
    }


    for(i = 0; i < fpt->numentries; ++i){
        if(fpt->partitions[i].type != PT_CODE)
            continue;

        manifest = (void*) &mapped[fpt->partitions[i].offset];
        if(!isvalid_MeManifest(manifest))
            return -1;

        dump_modules(manifest, glut);
    }
    return 0;
}

int processfile(char *data, unsigned int size){
    struct flash_descr *fdesc;
    struct flash_region *regions;
    struct MeFPT *fpt;
    struct MeManifestHeader *manifest;
    unsigned char *start, *stop, *scan;

    mapped = (unsigned char*)data;

    fdesc = (void*) mapped + 16;
    if(isvalid_flash_descr(fdesc)) {
        regions = (void*) &mapped[fdesc->frba << 4];
        print_flash_desc(fdesc);
        print_flash_regions(regions, fdesc->nr);
        mapped = &mapped[regions[region_me].begin << 12];
    }

    fpt = (void*)mapped + 16;
    if (isvalid_FPT(fpt))
        return parse_full_format(fpt);

    manifest = (void*) mapped;
    if(isvalid_MeManifest(manifest) && !strcmp(manifest->partitionname, "UPDP"))
            return parse_update_format();

    printf("Failed to detect file format, scanning for manifests.\n");
    start = (void*)mapped;
    stop = start + size;
    for(scan = start; scan < stop; scan += 4){
        manifest = (void*) scan;
        if (isvalid_MeManifest(manifest)) {
            print_manifest(manifest);
            dump_modules(manifest, 0);
        }
    }
    return 0;
}

char usage[] =
    "This program will unpack the code from ME versions 6,7,8,9,10\n"
    "The output will be stored in a subdirectory mod/\n"
    "If you encounter an image that does not unpack cleanly\n"
    "(some MATCHed modules, and some incomplete ones which aren't VE_FW_NAND)\n"
    "please provide a copy.\n\n"
    "Indispensable help by:\n"
    "\tIgor Skochinsky\n"
    "\tphcoder\n"
    "\tCorey Kallenberg\n"
    "\tXeno Kovah\n"
    "\tRafal Wojtczuk\n";



int main(int argc, char **argv){
    FILE*fp;
    struct stat filestats;
    char *data, *fname;
    int ret = -1;

    if(argc < 2){
        fprintf(stderr, "unhuffme by bla <blapost@gmail.com>\n");
        fprintf(stderr, "                       version: 2.4\n\n");
        fprintf(stderr, "\tUSAGE: %s [file]\n\n", argv[0]);
        fprintf(stderr, "%s", usage);
        return -1;
    }

    mkdir("mod", 0755);

    fname = argv[1];
    stat(fname, &filestats);
    fp = fopen(fname, "rb");
    if(!fp){
        fprintf(stderr, "Cannot open file %s\n", fname);
        return -1;
    }
    data = malloc(filestats.st_size);
    if(data == 0)
        return -1;
    if(fread(data, filestats.st_size, 1, fp) != 1)
        goto out;
    fclose(fp);

    ret = processfile(data, filestats.st_size);

out:
    free(data);
    return ret;
}


