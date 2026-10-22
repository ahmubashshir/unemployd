include src/mk/helpers.mk

TARGET     ?=
VARIANT    ?=
archdirs   ?= yes
nowarnings ?= no
$(eval $(call validate-opt,archdirs,yes no,yes))
$(eval $(call validate-opt,nowarnings,yes no,no))

override TARGET := $(if $(TARGET),$(TARGET)-,)
CC      := $(TARGET)gcc
STRIP   := $(TARGET)strip

MACHINE := $(shell $(CC) -dumpmachine | ./arch/mk/filter)

ifeq ($(MACHINE),)
$(error Machine type is empty)
endif

OBJDIR  := build/$(MACHINE)$(if $(VARIANT),-$(VARIANT))
OBJS    := $(OBJDIR)/unemployd.o \
           $(OBJDIR)/nolibc.o \
           $(OBJDIR)/$(MACHINE).o
DEPS    := $(OBJS:.o=.d)
BIN     := $(if $(filter yes,$(archdirs)),$(OBJDIR),build)/unemployd
BINS    := $(BIN) $(BIN).stripped

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

$(BIN): src/discard.ld $(OBJS)
	$(LINK.o) $(OBJS) -o $@

$(OBJDIR)/%.o: src/%.c $(MAKEFILE_LIST) | $(OBJDIR)
	$(COMPILE.c) -o $@ $<

$(OBJDIR)/%.o: arch/%.S $(MAKEFILE_LIST) | $(OBJDIR)
	$(COMPILE.S) -o $@ $<

$(BIN).stripped: $(BIN)
	$(STRIP) $< -o $@

$(OBJDIR):
	@mkdir -p $@

clean:
	$(RM) -r $(BINS) $(OBJDIR)

clean-all:
	$(RM) -r build

.PHONY: all clean clean-all
