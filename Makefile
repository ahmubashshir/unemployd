include src/mk/helpers.mk

TARGET     ?=
VARIANT    ?=
nowarnings ?= no
$(eval $(call validate-opt,nowarnings,yes no,no))

override TARGET := $(if $(TARGET),$(TARGET)-,)
CC      := $(TARGET)gcc
STRIP   := $(TARGET)strip

MACHINE := $(shell $(CC) -dumpmachine | ./arch/mk/filter)

ifeq ($(MACHINE),)
$(error Machine type is empty)
endif

BIN     := src/unemployd
OBJS    := src/unemployd.o src/nolibc.o arch/$(MACHINE).o

COMMONS  := -fno-pie -fno-plt -Wa,--noexecstack
WARNOPTS := -Wall -Wextra -Wuninitialized -Wmaybe-uninitialized -Wno-unused-parameter

CPPFLAGS += -Iinclude
CFLAGS   += -Os -ffreestanding $(COMMONS)
ASFLAGS  += $(COMMONS)
LDFLAGS  += -fuse-ld=bfd -static -no-pie \
            -nostdlib -nostartfiles \
            -Wl,-T,src/discard.ld \
            -Wl,--gc-sections \
            -Wl,-z,now \
            -Wl,--build-id=none

ifeq ($(nowarnings),no)
CFLAGS   += $(WARNOPTS)
endif

-include arch/mk/$(MACHINE).mk
CFLAGS   += -fno-stack-protector \
            -fno-asynchronous-unwind-tables \
            -fno-unwind-tables \
            -ffunction-sections \
            -fdata-sections \
            -fno-builtin

all: $(BIN).stripped

$(BIN): $(OBJS)

$(OBJS): Makefile
%.stripped: %
	$(STRIP) $< -o $@

clean:
	$(RM) $(BIN) $(BIN).stripped $(OBJS)

.PHONY: all clean crt1
