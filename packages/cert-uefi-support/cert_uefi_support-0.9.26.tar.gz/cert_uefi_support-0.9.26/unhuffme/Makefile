# unhuffme v.2.4 compiled from https://io.netgarage.org/me/

CC=gcc
CFLAGS=-O3 -Wall
LDFLAGS=
DEPS = pch_format.h
OBJ = unhuffme.o dict_cpt_1.o dict_cpt_2.o dict_pch_1.o dict_pch_2.o huffman.o prettyprint.o sha256.o

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

unhuffme: $(OBJ)
	gcc -o $@ $^ $(LDFLAGS)


clean:
	rm -rf unhuffme *.o
