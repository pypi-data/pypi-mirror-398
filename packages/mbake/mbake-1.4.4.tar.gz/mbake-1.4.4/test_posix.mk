all:
ifdef BUILD_DOCS
  docs:
	mkdir -p docs/output
	find src -name "*.md" -type f
	grep -r "TODO" src/
	sed 's/old/new/g' input.txt > output.txt
	awk '{print $1}' data.txt
	sort names.txt | uniq > sorted_names.txt
	cat README.md | head -10
	printf "Processing %s\n" "files"
	diff old.txt new.txt
	tar -czf archive.tar.gz files/
	make clean
	yacc parser.y
	lex scanner.l
	strip binary
endif
