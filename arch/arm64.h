#pragma once

void abort()
{
	sys_exit_group(-1);
}
