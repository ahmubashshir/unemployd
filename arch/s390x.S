//@s390x
#include "section.h"

_start:
	lgr		%r8, %r15    # original stack_end
	lg		%r3, 0(%r15) # argc
	la		%r4, 8(%r15) # argv
	larl	%r2, main

	brasl	%r14, __libc_start_main
	.word	0
