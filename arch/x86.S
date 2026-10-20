//@386
#include "section.h"

_start:
	xorl	%ebp, %ebp
	movl	(%esp), %ebx	// argc
	leal	4(%esp), %edx	// argv
	pushl	%edx	// argv
	pushl	%ebx	// argc
	pushl	$main	// main

	call	__libc_start_main
	ud2
