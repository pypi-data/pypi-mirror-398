.PHONY: ALL
TARGETLIB = libcxf.a
TARGETLIB_CPP = cxf
TARGETDYN=cxf.so
SRC=$(wildcard loaderz/*.cpp) $(wildcard loaderz/**/*.cpp)
OBJ=$(SRC:.cpp=.o)
ALL:cpp_depend $(TARGETLIB) $(TARGETDYN)
	echo "$(SRC)"

$(TARGETDYN):$(OBJ)
	g++ -O3 -fPIC -shared -o $@ $^ -static-libstdc++ -static-libgcc
$(TARGETLIB): $(OBJ)
	ar -rc $@ $^
test: $(OBJ)
	g++ -O3 $^ -o $@
%.o:%.cpp
	g++ -O3 -fPIC -Wall -g -c $< -o $@

cpp_depend:
	g++ -MM $(SRC) > cpp_depend

include cpp_depend

clean:
	rm $(OBJ) cpp_depend

wclean:
	del cpp_depend
	del loaderz\*.o
	del loaderz\deal\*.o