#pragma once
    mov     fp, #0
    mov     lr, #0

    mov     r4, sp              @ preserve initial stack pointer
    ldr     r1, [r4]            @ argc
    add     r2, r4, #4           @ argv

    ldr     r0, =main            @ main
    bl      __libc_start_main
    udf     #0
