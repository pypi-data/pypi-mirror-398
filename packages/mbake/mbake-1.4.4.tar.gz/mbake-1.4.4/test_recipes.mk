all:
ifdef DEBUG
  build:
	@echo "Building in debug mode"
	gcc -g -o myapp main.c
	mkdir -p output
	cp myapp output/
	./myapp --test
	python3 setup.py build
	npm install
	$(CC) $(CFLAGS) -o $@ $<
	echo "Build complete" > build.log
	if [ -f myapp ]; then echo "Success"; fi
	for file in *.o; do rm $$file; done
endif
