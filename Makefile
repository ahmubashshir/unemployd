TARGET  ?=
VARIANT ?=
CC      := $(TARGET)gcc
STRIP   := $(TARGET)strip
MACHINE := $(shell $(CC) -dumpmachine | ./arch/mk/filter)
ifeq ($(MACHINE),)
$(error Machine type is empty)
endif

BIN     := src/unemployd
OBJS    := src/unemployd.o src/nolibc.o arch/$(MACHINE).o

WARNOPTS := -Wall -Wextra -Wuninitialized -Wmaybe-uninitialized -Wno-unused-parameter
CFLAGS   += -Os -s -ffreestanding -fno-pie -fno-plt -Iinclude
ASFLAGS  +=  -fno-pie -fno-plt -Iinclude
CFLAGS   += $(WARNOPTS)
LDFLAGS  += -fuse-ld=bfd -static -no-pie \
            -nostdlib -nostartfiles \
            -Wl,-T,src/discard.ld \
            -Wl,--gc-sections \
            -Wl,-z,now \
            -Wl,--build-id=none

ifeq ($(MACHINE)/$(VARIANT),x86_64/v2)
	CFLAGS += -march=x86-64-v2
endif
CFLAGS   += -fno-stack-protector \
            -fno-asynchronous-unwind-tables \
            -fno-unwind-tables \
            -ffunction-sections \
            -fdata-sections \
            -fno-builtin \
            -Wa,--noexecstack


all: $(BIN).stripped

$(BIN): $(OBJS)

$(OBJS): Makefile
%.stripped: %
	$(STRIP) $< -o $@

clean:
	$(RM) $(BIN) $(BIN).stripped $(OBJS)

.PHONY: all clean crt1
