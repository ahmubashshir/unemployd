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
		*(.gnu.warning)
	}
	/* Align the text segment.	*/
	. = ALIGN(CONSTANT (MAXPAGESIZE));
	/* Start of the Read Only Data region.	*/
	/* Adjust the address for the rodata segment.	We want to adjust up to
		 the same address within the page on the next page up.	*/
	. = SEGMENT_START("rodata-segment", ALIGN(CONSTANT (MAXPAGESIZE)) + (. & (CONSTANT (MAXPAGESIZE) - 1)));
	.rodata				 : { *(.rodata .rodata.* .gnu.linkonce.r.*) }
	.data					 :
	{
		*(.data .data.* .gnu.linkonce.d.*)
		SORT(CONSTRUCTORS)
	}
	_edata = .;
	PROVIDE (edata = .);
	. = ALIGN(ALIGNOF(NEXT_SECTION));
	__bss_start = .;
	.bss						:
	{
		*(.dynbss)
		*(.bss .bss.* .gnu.linkonce.b.*)
		*(COMMON)
		/* Align here to ensure that in the common case of there only being one
			 type of .bss section, the section occupies space up to _end.
			 Align after .bss to ensure correct alignment even if the
			 .bss section disappears because there are no input sections.
			 FIXME: Why do we need it? When there is no .bss section, we do not
			 pad the .data section.	*/
			. = ALIGN(. != 0 ? 64 / 8 : 1);
	}

	_end = .;
	PROVIDE (end = .);
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
	}
}
