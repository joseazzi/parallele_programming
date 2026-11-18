#include <mpi.h>
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int rank, P;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &P);

    try {
        int N = 100, steps = -1;
        double r = 0.2, T = -1.0;
        std::string test_case = "1";
        std::string decomp = "strips";
        std::string output;

        // Command-line arguments
        for (int k = 1; k < argc; k += 2) {
            if (k + 1 >= argc)
                throw std::runtime_error("Missing option value");

            std::string key = argv[k];
            std::string val = argv[k + 1];

            if (key == "--N") N = std::stoi(val);
            else if (key == "--r") r = std::stod(val);
            else if (key == "--steps") steps = std::stoi(val);
            else if (key == "--T") T = std::stod(val);
            else if (key == "--case") test_case = val;
            else if (key == "--out") output = val;
            else if (key == "--decomp") decomp = val;
            else throw std::runtime_error("Unknown option");
        }

        if (N < 2 || P > N - 1)
            throw std::runtime_error("Require N >= 2 and P <= N-1");

        if (!std::isfinite(r) || r <= 0 || r > 0.25)
            throw std::runtime_error("Unstable r: require 0 < r <= 0.25");

        if (test_case != "1" && test_case != "2" && test_case != "V")
            throw std::runtime_error("Invalid case");

        if (decomp != "strips")
            throw std::runtime_error("Use --decomp strips");

        if (steps < -1 || (T != -1.0 && (!std::isfinite(T) || T <= 0)))
            throw std::runtime_error("Invalid time parameters");

        if (steps >= 0 && T >= 0)
            throw std::runtime_error("Choose steps or T");

        double h = 1.0 / N;
        double dt = r * h * h;

        if (T >= 0) {
            double count = std::ceil(T / dt);
            if (count > std::numeric_limits<int>::max())
                throw std::runtime_error("Too many steps");
            steps = static_cast<int>(count);
            dt = T / steps;
            r = dt / (h * h);
        } else if (steps < 0) {
            steps = 500;
        }

        double final_time = steps * dt;
        const int W = N + 1;
        const double pi = std::acos(-1.0);

        // Divide N-1 interior rows among ranks
        int base = (N - 1) / P;
        int remainder = (N - 1) % P;

        int local_rows = base + (rank < remainder ? 1 : 0);
        int first_row = 1 + rank * base + std::min(rank, remainder);

        // Two additional ghost rows
        std::vector<double> u((local_rows + 2) * W, 0.0);
        std::vector<double> next = u;

        auto idx = [W](int i, int j) {
            return j * W + i;
        };

        // Initialize locally owned rows
        for (int j = 1; j <= local_rows; ++j) {
            int global_j = first_row + j - 1;

            if (test_case == "V") {
                for (int i = 1; i < N; ++i) {
                    u[idx(i,j)] =
                        std::sin(pi * i * h) *
                        std::sin(pi * global_j * h);
                }
            } else if (test_case == "1") {
                u[idx(0,j)] = 1.0;
                u[idx(N,j)] = 1.0;
            }
        }

        // Physical boundary ghost rows
        if (rank == 0 && test_case != "V") {
            for (int i = 0; i <= N; ++i)
                u[idx(i,0)] = 1.0;
        }

        if (rank == P - 1 && test_case != "V") {
            for (int i = 0; i <= N; ++i)
                u[idx(i,local_rows+1)] = 1.0;
        }

        next = u;

        int down = rank == 0 ? MPI_PROC_NULL : rank - 1;
        int up = rank == P - 1 ? MPI_PROC_NULL : rank + 1;

        double t_comm = 0.0, t_comp = 0.0;

        MPI_Barrier(MPI_COMM_WORLD);
        double start = MPI_Wtime();

        for (int step = 0; step < steps; ++step) {

            // Exchange halo rows
            double begin = MPI_Wtime();

            MPI_Sendrecv(
                &u[idx(0,local_rows)], W, MPI_DOUBLE, up, 10,
                &u[idx(0,0)], W, MPI_DOUBLE, down, 10,
                MPI_COMM_WORLD, MPI_STATUS_IGNORE
            );

            MPI_Sendrecv(
                &u[idx(0,1)], W, MPI_DOUBLE, down, 11,
                &u[idx(0,local_rows+1)], W, MPI_DOUBLE, up, 11,
                MPI_COMM_WORLD, MPI_STATUS_IGNORE
            );

            t_comm += MPI_Wtime() - begin;

            // Compute local temperatures
            begin = MPI_Wtime();

            for (int j = 1; j <= local_rows; ++j) {
                for (int i = 1; i < N; ++i) {
                    next[idx(i,j)] =
                        (1.0 - 4.0*r) * u[idx(i,j)]
                        + r * (
                            u[idx(i+1,j)] +
                            u[idx(i-1,j)] +
                            u[idx(i,j+1)] +
                            u[idx(i,j-1)]
                        );
                }
            }

            t_comp += MPI_Wtime() - begin;
            u.swap(next);
        }

        double elapsed = MPI_Wtime() - start;

        // Maximum timing across ranks
        double max_total = 0, max_comm = 0, max_comp = 0;

        MPI_Reduce(&elapsed, &max_total, 1, MPI_DOUBLE,
                   MPI_MAX, 0, MPI_COMM_WORLD);
        MPI_Reduce(&t_comm, &max_comm, 1, MPI_DOUBLE,
                   MPI_MAX, 0, MPI_COMM_WORLD);
        MPI_Reduce(&t_comp, &max_comp, 1, MPI_DOUBLE,
                   MPI_MAX, 0, MPI_COMM_WORLD);

        // Prepare Gatherv metadata
        std::vector<int> counts(P), displs(P);

        for (int p = 0; p < P; ++p) {
            int rows = base + (p < remainder ? 1 : 0);
            int first = 1 + p * base + std::min(p, remainder);
            counts[p] = rows * W;
            displs[p] = (first - 1) * W;
        }

        std::vector<double> full;

        if (rank == 0) {
            full.assign(static_cast<std::size_t>(W) * W, 0.0);

            if (test_case != "V") {
                for (int k = 0; k <= N; ++k) {
                    full[k] = 1.0;
                    full[N*W+k] = 1.0;

                    if (test_case == "1") {
                        full[k*W] = 1.0;
                        full[k*W+N] = 1.0;
                    }
                }
            }
        }

        // Collect all interior rows on rank 0
        MPI_Gatherv(
            &u[idx(0,1)], local_rows * W, MPI_DOUBLE,
            rank == 0 ? full.data() + W : nullptr,
            counts.data(), displs.data(), MPI_DOUBLE,
            0, MPI_COMM_WORLD
        );

        if (rank == 0) {
            double err_inf = 0.0;
            double err_sum = 0.0;

            if (test_case == "V") {
                double factor = std::exp(-2.0*pi*pi*final_time);

                for (int j = 0; j <= N; ++j) {
                    for (int i = 0; i <= N; ++i) {
                        double exact =
                            std::sin(pi*i*h) *
                            std::sin(pi*j*h) * factor;

                        double error = std::abs(
                            full[j*W+i] - exact
                        );

                        err_inf = std::max(err_inf, error);
                        err_sum += error * error;
                    }
                }
            }

            if (!output.empty()) {
                std::ofstream file(output, std::ios::binary);
                if (!file)
                    throw std::runtime_error("Cannot open output");

                file.write(
                    reinterpret_cast<const char*>(full.data()),
                    static_cast<std::streamsize>(
                        full.size() * sizeof(double)
                    )
                );

                if (!file)
                    throw std::runtime_error("Output write failed");
            }

            std::cout << std::setprecision(12)
                      << "decomp=strips"
                      << " case=" << test_case
                      << " P=" << P
                      << " N=" << N
                      << " steps=" << steps
                      << " r=" << r
                      << " T=" << final_time
                      << " t_total=" << max_total
                      << " t_comp=" << max_comp
                      << " t_comm=" << max_comm;

            if (test_case == "V")
                std::cout << " err_inf=" << err_inf
                          << " err_l2=" << h*std::sqrt(err_sum);

            std::cout << std::endl;
        }

        MPI_Finalize();
        return 0;

    } catch (const std::exception& e) {
        std::cerr << "Rank " << rank << ": " << e.what() << "\n";
        MPI_Abort(MPI_COMM_WORLD, 1);
        return 1;
    }
}
