#ifndef __COMMON_SHIM_H__
#define __COMMON_SHIM_H__
#define _GNU_SOURCE
#include "LSS/linux_syscall_support.h"

#ifdef _NOLIBC_IMPL
#	define NORETURN __attribute__((noreturn, used))
#	if defined(__aarch64__)
#		include "arch/arm64.h"
#	endif
#endif

#endif /* __COMMON_SHIM_H__ */
