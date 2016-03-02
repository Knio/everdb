#include <cstdio>
#include <stdint.h>

int main() {
    printf("Hello World\n");
    return 0;
}


#define BLOCK_BITS (12) // 4096
#define BLOCK_SIZE (1 << BLOCK_BITS)
#define BLOCK_MASK (BLOCK_SIZE - 1)

#define INDEX_BITS (10)
#define INDEX_SIZE (1 << INDEX_BITS)
#define INDEX_MASK (INDEX_SIZE - 1)

#define LEVEL_ONE (512)

#define INDEX0(index) (LEVEL_ONE + ((index - LEVEL_ONE) >> INDEX_BITS))
#define INDEX1(index) ((index - LEVEL_ONE) & INDEX_MASK)

#define BLOCK(root, index) (&root[index * BLOCK_SIZE])

typedef char * const block;
typedef uint32_t uint;

struct page_header {
    uint blocks;
    uint checksum;
};


// get the host index of a relative index in a page table
uint get_host_index(block root, const uint page, const uint index) {
    block pt = BLOCK(root, page);
    const page_header &ph = *((page_header*) (pt + BLOCK_SIZE - sizeof page_header));

    if (ph.blocks < index) {
        return -1;
    }

    if (ph.blocks == 0) {
        // small block
        return page;
    }

    uint * block_ptrs = ((uint*)pt);
    if (index <= LEVEL_ONE) {
        // level 1 large block
        return block_ptrs[index];
    }
    // level 2 large block
    block l1 = BLOCK(root, INDEX0(index));
    block_ptrs = ((uint*)l1);
    return block_ptrs[INDEX1(index)];
}

