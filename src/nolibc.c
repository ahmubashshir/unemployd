/* only syscall symbols from LSS are safe, avoid libc functions */
#include "common.h"
#include <stdint.h>

__attribute__((noreturn, used))
int __libc_start_main(
    int (*main) (int, char * *, char * *),
    int argc,
    char **argv,
    void (*init) (void),
    void (*fini) (void),
    void (*rtld_fini) (void),
    void (* stack_end))
{
	sys_exit_group(main(argc, argv, &argv[argc + 1]));
	__builtin_unreachable();
}

void *memset(void *dest, int c, size_t n)
{
	unsigned char *p = (unsigned char *)dest;

	while (n-- > 0)
		*p++ = (unsigned char)c;

	return dest;
}

int* __errno_location()
{
	static int _errno = 0;
	return &_errno;
}
