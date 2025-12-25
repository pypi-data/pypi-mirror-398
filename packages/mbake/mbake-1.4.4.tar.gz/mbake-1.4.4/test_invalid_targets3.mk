# Test invalid target syntax - try to use the targets

# Valid target first
valid_target: prerequisites
	@echo "Valid target works"

# Invalid target with = sign
target=value: prerequisites
	@echo "This should not work"

# Invalid target with .RECIPEPREFIX character  
.RECIPEPREFIX := >
>invalid: prerequisites
	@echo "This should not work"
