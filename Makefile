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
				-L arch/lib \
				-Wl,-z,now -Wl,-T,discard.ld

all: $(BIN).stripped

$(BIN): $(OBJS) | crt1

$(OBJS): Makefile
%.stripped: %
	$(STRIP) $< -o $@

clean:
	$(RM) $(BIN) $(BIN).stripped $(OBJS)
	@$(MAKE) -C arch/lib clean

crt1:
	@$(MAKE) CC="$(CC)" CFLAGS="$(CFLAGS)" -C arch/lib

.PHONY: all clean crt1
