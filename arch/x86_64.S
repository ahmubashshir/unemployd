#include "section.h"

_start:
    xorl    %ebp, %ebp
    movq    (%rsp), %rsi       # argc
    leaq    8(%rsp), %rdx      # argv
    leaq    main(%rip), %rdi
    call    __libc_start_main
    ud2
    .size _start, .-_start
