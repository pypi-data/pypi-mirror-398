# Test if indented targets inside conditionals work with GNU Make
ifeq ($(TEST),1)
  target1: dependency1
	@echo "Target 1 with TEST=1"
else
  target1: dependency2
	@echo "Target 1 with TEST!=1"
endif

target2: dependency3
	@echo "Target 2 always"
