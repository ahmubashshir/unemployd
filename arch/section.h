#pragma once
#if defined(__arm__) || defined(__aarch64__)
#	define TAG(tag) % ## tag
#else
#	define TAG(tag) @ ## tag
#endif
	.section .text.startup,"ax",TAG(progbits)
	.globl _start
	.type _start, TAG(function)
