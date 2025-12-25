# Test using invalid target
valid_target: prerequisites
	@echo "Valid target works"

# Invalid target
target=value: prerequisites
	@echo "This should not work"

# Try to use the invalid target
all: target=value
	@echo "Trying to use invalid target"
