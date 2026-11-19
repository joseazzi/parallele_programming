#include <mpi.h>
#include <iostream>
#include <vector>
#include <iomanip>

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (size != 2) {
        if (rank == 0)
            std::cerr << "Error: exactly 2 MPI processes required\n";
        MPI_Finalize();
        return 1;
    }

    const int max_bytes = 16 * 1024 * 1024;
    std::vector<char> buffer(max_bytes, 'x');

    if (rank == 0) {
        std::cout << "bytes,rtt_seconds,one_way_seconds\n";
    }

    for (int bytes = 8; bytes <= max_bytes; bytes *= 2) {
        int repetitions = (bytes <= 65536) ? 20 : 10;

        // Warm-up communication
        for (int k = 0; k < 10; ++k) {
            if (rank == 0) {
                MPI_Send(buffer.data(), bytes, MPI_BYTE, 1, 0,
                         MPI_COMM_WORLD);
                MPI_Recv(buffer.data(), bytes, MPI_BYTE, 1, 0,
                         MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            } else {
                MPI_Recv(buffer.data(), bytes, MPI_BYTE, 0, 0,
                         MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                MPI_Send(buffer.data(), bytes, MPI_BYTE, 0, 0,
                         MPI_COMM_WORLD);
            }
        }

        MPI_Barrier(MPI_COMM_WORLD);
        double start = MPI_Wtime();

        for (int k = 0; k < repetitions; ++k) {
            if (rank == 0) {
                MPI_Send(buffer.data(), bytes, MPI_BYTE, 1, 0,
                         MPI_COMM_WORLD);
                MPI_Recv(buffer.data(), bytes, MPI_BYTE, 1, 0,
                         MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            } else {
                MPI_Recv(buffer.data(), bytes, MPI_BYTE, 0, 0,
                         MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                MPI_Send(buffer.data(), bytes, MPI_BYTE, 0, 0,
                         MPI_COMM_WORLD);
            }
        }

        if (rank == 0) {
            double elapsed = MPI_Wtime() - start;
            double rtt = elapsed / repetitions;

            std::cout << bytes << ","
                      << std::setprecision(12) << rtt << ","
                      << rtt / 2.0 << "\n";
        }
    }

    MPI_Finalize();
    return 0;
}
