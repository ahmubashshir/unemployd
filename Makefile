TARGET     ?=
VARIANT    ?=
archdirs   ?= yes
nowarnings ?= no
verbose    ?= no
# V=1 overrides verbose=no
V          ?= 0

include src/mk/helpers.mk
### Makefile start ####
override TARGET := $(if $(TARGET),$(TARGET)-,)
CC      := $(TARGET)gcc
STRIP   := $(TARGET)strip

MACHINE := $(shell $(CC) -dumpmachine | ./arch/mk/filter)

ifeq ($(MACHINE),)
$(error Machine type is empty)
endif

$(eval $(call validate-opt,V,0 1,0))
$(eval $(call validate-opt,verbose,yes no,no))
ifeq ($(V),1)
override verbose := yes
endif

$(eval $(call validate-opt,archdirs,yes no,yes))
OBJDIR  := build/$(MACHINE)$(if $(VARIANT),-$(VARIANT))
OBJS    := $(OBJDIR)/unemployd.o \
           $(OBJDIR)/nolibc.o \
           $(OBJDIR)/$(MACHINE).o
DEPS    := $(OBJS:.o=.d)
BIN     := $(if $(filter yes,$(archdirs)),$(OBJDIR),build)/unemployd
BINS    := $(BIN) $(BIN).stripped

COMMONS  := -fno-pie -fno-plt -Wa,--noexecstack
WARNOPTS := -Wall -Wextra -Wuninitialized -Wmaybe-uninitialized -Wno-unused-parameter

CPPFLAGS += -Iinclude -MMD -MP
CFLAGS   += -Os -ffreestanding $(COMMONS)
ASFLAGS  += $(COMMONS)
LDFLAGS  += -fuse-ld=bfd -static -no-pie \
            -nostdlib -nostartfiles \
            -Wl,-T,src/discard.ld \
            -Wl,--gc-sections \
            -Wl,-z,now \
            -Wl,--build-id=none

$(eval $(call validate-opt,nowarnings,yes no,no))
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
	@$(call message,LINK   -o,+,$(@) $(^))
	@$(shtrace)$(LINK.o) $(OBJS) -o $@

$(OBJDIR)/%.o: src/%.c $(MAKEFILE_LIST) | $(OBJDIR)
	@$(call message,  CC   -o,+,$(@) $(<))
	@$(shtrace)$(COMPILE.c) -o $@ $<

$(OBJDIR)/%.o: arch/%.S $(MAKEFILE_LIST) | $(OBJDIR)
	@$(call message,  AS   -o,+,$(@) $(<))
	@$(shtrace)$(COMPILE.S) -o $@ $<

$(BIN).stripped: $(BIN)
	@$(call message,STRIP  -o,+,$(@) $(<))
	@$(shtrace)$(STRIP) $< -o $@

$(OBJDIR):
	@mkdir -p $@

clean:
	@$(call message,CLEAN   -,-,$(call rwildcard,$(OBJDIR),*))
	@$(shtrace) $(RM) -r $(BINS) $(OBJDIR)

clean-all:
	@$(call message,CLEAN   -,-,$(call rwildcard,build,*))
	@$(shtrace)$(RM) -r build

.PHONY: all clean clean-all

-include $(DEPS) # include deps last; they're not that important
