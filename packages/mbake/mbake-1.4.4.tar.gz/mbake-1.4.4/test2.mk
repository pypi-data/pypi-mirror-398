# Test file for .SECONDARY without prerequisites
# This should not generate a warning after the fix

.SECONDARY:

# Test other special targets that can also be used without prerequisites
.PRECIOUS:
.INTERMEDIATE:

# Regular targets
all: main.o
	$(CC) -o main main.o

main.o: main.c
	$(CC) -c main.c

clean:
	rm -f *.o main
