#include "common.h"

int main(void)
{
	struct kernel_sigset_t mask = {};
	sys_sigemptyset(&mask);
	sys_sigaddset(&mask, SIGTERM);
	sys_sigaddset(&mask, SIGINT);

	if (sys_sigprocmask(SIG_BLOCK, &mask, NULL) < 0)
		return 1;

	siginfo_t si = {};
	while(sys_sigtimedwait(&mask, &si, NULL) < 0
	      ? errno == EINTR
	      : si.si_signo != SIGINT && si.si_signo != SIGTERM
	     );

	return 0;
}
