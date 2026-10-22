//@ppc64le
#include "section.h"

_start:
	mr		31, 1
	stdu	1, -32(1)	  # allocate stack frame (32 bytes)

	ld		4, 0(31)	   # argc from original SP
	addi	5, 31, 8	   # argv from original SP

	lis		3, main@ha
	addi	3, 3, main@l

	bl		__libc_start_main
	trap
