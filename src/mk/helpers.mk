define validate-opt
ifneq ($$(filter $$($(1)),$(2)),$$($(1)))
$$(warning '$(1)' must be one of [$(2)]; defaulting to $(3))
override $(1) := $(3)
endif
endef
