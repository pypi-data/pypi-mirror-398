chaos:
	@echo test
ifeq ($(VAR), value)
  ifeq ($(VAR2), value2)
	@echo nested
  endif
endif
