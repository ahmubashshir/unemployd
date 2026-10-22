ifneq ($(VARIANT),)
	CFLAGS += -march=x86-64-$(VARIANT)
endif
