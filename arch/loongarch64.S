//@loong64%ghcr.io/loong64/alpine:edge
#include "section.h"

_start:
	la.local $a0, main	// main
	ld.d	$a1, $sp, 0	// argc
	addi.d	$a2, $sp, 8	// argv

	bstrins.d $sp, $zero, 3, 0 // align stack to 16 bytes
	bl	  __libc_start_main
	break   0
