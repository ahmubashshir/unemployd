/* vim: ft=c */
ENTRY(_start)
SECTIONS
{
	PROVIDE (__executable_start = SEGMENT_START("text-segment", 0x400000));
	. = SEGMENT_START("text-segment", 0x400000) + SIZEOF_HEADERS;
	.text					 :
	{
		*(.text.unlikely .text.*_unlikely .text.unlikely.*)
		*(.text.exit .text.exit.*)
		*(.text.startup .text.startup.*)
		*(.text.hot .text.hot.*)
		*(SORT(.text.sorted.*))
		*(.text .stub .text.* .gnu.linkonce.t.*)
	}
	. = ALIGN(CONSTANT (MAXPAGESIZE));

	. = SEGMENT_START("rodata-segment", ALIGN(CONSTANT (MAXPAGESIZE)) + (. & (CONSTANT (MAXPAGESIZE) - 1)));
	.rodata				 : { *(.rodata .rodata.* .gnu.linkonce.r.*) }
	PROVIDE(__global_pointer$ = . + 0x800);
	.data					 :
	{
		*(.data .data.* .gnu.linkonce.d.*)
		SORT(CONSTRUCTORS)
	}
	. = ALIGN(ALIGNOF(NEXT_SECTION));

	.bss						:
	{
		*(.dynbss)
		*(.bss .bss.* .gnu.linkonce.b.*)
		*(COMMON)
		. = ALIGN(. != 0 ? 64 / 8 : 1);
	}

	/DISCARD/ : {
		*(.note.GNU-stack)
		*(.gnu_debuglink)
		*(.gnu.lto_*)
		*(.gnu_object_only)
		*(.note.*)
		*(.eh_frame)
		*(.eh_frame_hdr)
		*(.sframe)
		*(.comment)
		*(.tbss .tbss.* .gnu.linkonce.tb.*)
		*(.*.attributes)
		*(.got .got.*)
	}
}
