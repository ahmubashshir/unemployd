TARGET  ?=
CC      := $(TARGET)gcc
STRIP   := $(TARGET)strip
BIN     := unemployd
OBJS    := unemployd.o nolibc.o

CFLAGS    += -Os -s -ffreestanding \
				-fno-stack-protector \
				-fno-asynchronous-unwind-tables \
				-fno-unwind-tables -fno-pie \
				-ffunction-sections -fdata-sections \
				-fno-builtin \
				-Wa,--noexecstack

LDFLAGS   += -Wl,--gc-sections -static -no-pie -fuse-ld=bfd \
				-nostdlib -nostartfiles \
				-Wl,--build-id=none \
				-Wl,-z,now -Wl,-T,discard.ld
LOADLIBES += -l:crt1.o

all: $(BIN).stripped

$(BIN): $(OBJS)

$(OBJS): Makefile
%.stripped: %
	$(STRIP) $< -o $@

clean:
	$(RM) $(BIN) $(BIN).stripped $(OBJS)

.PHONY: all clean
