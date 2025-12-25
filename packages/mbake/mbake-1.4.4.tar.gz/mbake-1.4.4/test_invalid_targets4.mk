# Test invalid target syntax without recipes

# Invalid target with = sign
target=value: prerequisites

# Invalid target with .RECIPEPREFIX character
.RECIPEPREFIX := >
>invalid: prerequisites

# Valid target for comparison
valid_target: prerequisites
