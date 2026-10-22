define validate-opt
ifneq ($$(filter $$($(1)),$(2)),$$($(1)))
$$(warning '$(1)' must be one of [$(2)]; defaulting to $(3))
override $(1) := $(3)
endif
endef

<<<<<< := echo
ifneq ($(shell eval 'echo -e'),-e)
<<<<<< += -e
endif

define rwildcard
$(foreach d,\
	$(wildcard $(1)/*),\
	$(call rwildcard,$d,$(2))\
	$(filter $(subst *,%,$(2)),$d)\
)
endef

define <space>
 \
endef

define message
$(if $(strip $(3)),
	$(if $(filter yes,$(verbose)),
		true,
		$(<<<<<<)) \
	"$(1) \
	$(subst $(<space>)\
		,\n        $(2) \
		,$(strip $(3)))")
endef

define shtrace
test "$(V)" -gt 0 && set -x;
endef
