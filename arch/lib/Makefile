MACHINE := $(shell uname -m)

ifneq ($(wildcard $(MACHINE).*),)
rcrt1.o: $(MACHINE).o
	cp $^ $@
else
endif

all:
	@true

clean:
	$(RM) $(wildcard *.o)
