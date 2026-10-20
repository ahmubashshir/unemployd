//@riscv64
#include "section.h"

_start:
	.option push
	.option norelax
		la      gp, __global_pointer$
	.option pop
		mv      t0, sp
		ld      a1, 0(t0) # argc
		addi    a2, t0, 8 # argv
		la      a0, main
		call    __libc_start_main
		unimp
