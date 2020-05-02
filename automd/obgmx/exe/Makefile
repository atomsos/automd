.PHONY: all



all: test



test:
	cd tests; for i in *; do echo $$i; ../obgmx $$i; done

clean:
	rm -f obgmx.top obgmx.itp obgmx.ffout tests/obgmx.top tests/obgmx.itp tests/obgmx.ffout
