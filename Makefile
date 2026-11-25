
CXX = g++
MPICXX = mpic++

CXXFLAGS = -O2 -std=c++17 -ffp-contract=off
MPIFLAGS = $(CXXFLAGS)

.PHONY: all clean

all: heat_serial heat_unstable heat_strips heat_blocks pingpong hello_mpi

heat_serial: src/heat_serial.cpp
	$(CXX) $(CXXFLAGS) $< -o $@

heat_unstable: src/heat_unstable.cpp
	$(CXX) $(CXXFLAGS) $< -o $@

heat_strips: src/parallel/heat_strips.cpp
	$(MPICXX) $(MPIFLAGS) $< -o $@

heat_blocks: src/parallel/heat_blocks.cpp
	$(MPICXX) $(MPIFLAGS) $< -o $@

pingpong: pingpong.cpp
	$(MPICXX) $(MPIFLAGS) $< -o $@

hello_mpi: hello_mpi.cpp
	$(MPICXX) $(MPIFLAGS) $< -o $@

clean:
	rm -f heat_serial heat_unstable heat_strips heat_blocks pingpong hello_mpi
