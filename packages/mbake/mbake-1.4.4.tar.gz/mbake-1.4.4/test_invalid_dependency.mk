# Test invalid target as dependency
valid_target: target=value
	@echo "Valid target depends on invalid target"

# Invalid target
target=value: prerequisites
	@echo "This should not work"
