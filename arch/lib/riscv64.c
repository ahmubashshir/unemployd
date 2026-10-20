__attribute__((naked, noreturn, used, section(".text.startup._start")))
void _start(void)
{
	__asm__ volatile (
	    ".option push\n"
	    ".option norelax\n"
	    "	la	gp, __global_pointer$\n"
	    ".option pop\n"
	    "  mv      t0, sp\n"
	    "  ld      a1, 0(t0) # argc\n"
	    "  addi    a2, t0, 8 # argv\n"
	    "  la      a0, main\n"
	    "  li      a3, 0 # init\n"
	    "  li      a4, 0 # fini\n"
	    "  li      a5, 0 # rtld_fini\n"
	    "  mv      a6, t0 # stack_end\n"
	    "  call    __libc_start_main\n"
	    "  unimp\n"
	);
}
