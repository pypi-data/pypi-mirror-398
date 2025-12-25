/*unhuffme v.2.4 compiled from https://io.netgarage.org/me/*/

/*
 * Unhuffme by bla<blapost@gmail.com>
 *
 * based directly off of Igor Skochinsky's research
 */
#include <stdint.h>

#define FLASHMAGIC         0x0ff0a55a
#define FPTMAGIC           0x54504624   // $FPT
#define MEMANIFEST2_MAGIC  0x324e4d24   // $MN2
#define LUT_MAGIC          0x54554c     // LUT: lookup table
#define LLUT_MAGIC         0x54554c4c   // LLUT

#define LUT_FLAG_UNCOMPRESSED 0x00
#define LUT_FLAG_CODE  0x20
#define LUT_FLAG_EMPTY 0x40
#define LUT_FLAG_DATA  0x60

#define CHIPSET_PCH 0x20484350
#define CHIPSET_CPT 0x20545043

enum FlashRegions{
    region_descriptor,
    region_bios,
    region_me,
    region_GbE,
};
enum FPT_partition_type {
    PT_CODE,
    PT_BLOCKIO,
    PT_NVRAM,
    PT_GENERIC,
    PT_EFFS,
    PT_ROM,
};
enum Compression_type {
    C_UNCOMPRESSED,
    C_HUFFMAN,
    C_LZMA,
};

/* Describes how Flash memory is layed out
 */
struct flash_descr{
    uint32_t magic;

    uint16_t fcba:8, nc:2, :6;         //flash components base address
    uint16_t frba:8, nr:3, :5;         //flash region base address

    uint32_t flmap1;
    uint32_t flmap2;
    char *data[0];
}__attribute__((packed));
struct flash_region{
    uint16_t begin:13,:3;              //in 0x1000 byte pages
    uint16_t end:13,:3;
}__attribute__((packed));


/* Describes how the ME region of flash memory is partitioned
 */
struct FPT_partition {
    char name[4];
    char owner[4];
    uint32_t offset;
    uint32_t size;
    uint32_t tokensonstart;
    uint32_t maxtokens;
    uint32_t scratchsectors;
    uint32_t type:7, flags:25;
};
struct MeFPT{                          // ME partition table
    uint32_t magic; //$FPT
    uint32_t numentries;
    uint8_t bcdversion;
    uint8_t entrytype;
    uint8_t headerlen;
    uint8_t checksum;
    uint16_t flashcyclelifetime;
    uint16_t flashcyclelimit;
    uint32_t umasize;
    uint32_t flags;
    uint32_t padding[2];
    struct FPT_partition partitions[0];
}__attribute__((packed));


/*Describes what a partition contains
 */
struct MeModuleHdr2 {
    uint32_t magic;
    char name[16];
    uint8_t hash[32];
    uint32_t base;
    uint32_t fileoffset;
    uint32_t size_uncompressed;
    uint32_t size_compressed;
    uint32_t unknown2;
    uint32_t unknown3;
    uint32_t entrypoint;
    uint32_t flags;
    uint32_t unknown4[3];
} __attribute__((packed));
struct MeManifestHeader {
    char base[0];
    uint16_t moduletype;
    uint16_t modulesubtype;
    uint32_t headerlen;
    uint32_t headerversion;
    uint32_t flags;
    uint32_t modulevendor;
    uint32_t date;
    uint32_t size;
    uint32_t magic;            //$MN2
    uint32_t nummodules;
    uint16_t majorversion;
    uint16_t minorversion;
    uint16_t hotfixversion;
    uint16_t buildversion;
    uint32_t unknown1[19];
    uint32_t keysize;
    uint32_t scratchsize;
    uint32_t rsapubkey[64];
    uint32_t rsapubexp;
    uint32_t rsasig[64];
    char partitionname[12];
    struct MeModuleHdr2 modules[0];
} __attribute__((packed));

struct LutEntry {
    uint32_t addr:25;
    uint32_t flags:7;
} __attribute__((packed));
struct LutHdr{
    uint32_t magic;
    uint32_t chunkcount;
    uint32_t addrbase;
    uint32_t spibase;
    uint32_t hufflen;
    uint32_t huffstart;
    uint32_t flags;
    uint32_t unknown1[5];
    uint32_t pagesize;
    uint16_t majorversion;
    uint16_t minorversion;
    uint32_t chipset;
    char revision[4];
    struct LutEntry entries[0];
} __attribute__((packed));

struct TagHdr {
    char name[4];
    uint32_t field[0];
} __attribute__((packed));
struct TagGLT {
    char name[4];
    uint32_t len;
    uint32_t offset;
    uint32_t size;
} __attribute__((packed));
struct TagUDC {
    char name[4];
    uint32_t len;
    char type[4];
    char sha256hash[32];
    char pname[16];
    uint32_t offset;
    uint32_t size;
} __attribute__((packed));
