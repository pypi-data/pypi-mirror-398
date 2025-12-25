
# Test file for .PHONY detection

# These should be .PHONY (don't create files with target name):
.PHONY: format
format:
	echo 'format'

.PHONY: lint
lint:
	echo 'lint'

.PHONY: test
test:
	touch testing.txt

.PHONY: clean
clean:
	rm -f *.o

.PHONY: install
install:
	npm install

# These should NOT be .PHONY (create files with target name):
output:
	touch output

program:
	gcc -o program source.c

file.txt:
	cp input.txt file.txt

output.txt:
	echo 'content' > output.txt
