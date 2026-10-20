TARGET  ?=
VARIANT ?=
CC      := $(TARGET)gcc
STRIP   := $(TARGET)strip
BIN     := unemployd
MACHINE := $(shell $(CC) -dumpmachine | sed -f arch/filter.sed)
OBJS    := unemployd.o nolibc.o arch/$(MACHINE).o

ASFLAGS   +=  -fno-pie -fno-plt
CFLAGS    += -Os -s -ffreestanding \
				-fno-stack-protector \
				-fno-asynchronous-unwind-tables \
				-fno-unwind-tables -fno-pie -fno-plt \
				-ffunction-sections -fdata-sections \
				-fno-builtin \
				-Wa,--noexecstack
WARNFLAGS += -Wall -Wextra -Wuninitialized -Wmaybe-uninitialized -Wno-unused-parameter
CFLAGS    += $(WARNFLAGS)

LDFLAGS   += -Wl,--gc-sections -static -no-pie -fuse-ld=bfd \
				-nostdlib -nostartfiles \
				-Wl,--build-id=none \
				-Wl,-z,now -Wl,-T,discard.ld

ifeq ($(MACHINE)/$(VARIANT),x86_64/v2)
	CFLAGS += -march=x86-64-v2
endif

all: $(BIN).stripped

$(BIN): $(OBJS)

$(OBJS): Makefile
%.stripped: %
	$(STRIP) $< -o $@

clean:
	$(RM) $(BIN) $(BIN).stripped $(OBJS)

.PHONY: all clean crt1
