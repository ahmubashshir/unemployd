#include "section.h"

_start:
	mov	 x29, xzr
	mov	 x30, xzr

	ldr	 x1, [sp]		   // argc
	add	 x2, sp, #8		 // argv
	adrp	x0, main
	add	 x0, x0, :lo12:main

	bl	  __libc_start_main
	brk	 #0
