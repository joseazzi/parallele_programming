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
        std::string decomp = "blocks";
        std::string output;

        // Read command-line options
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

        if (N < 2 || P > (N-1)*(N-1))
            throw std::runtime_error("Invalid grid or process count");

        if (!std::isfinite(r) || r <= 0.0 || r > 0.25)
            throw std::runtime_error("Require 0 < r <= 0.25");

        if (test_case != "1" && test_case != "2" &&
            test_case != "V")
            throw std::runtime_error("Invalid case");

        if (decomp != "blocks")
            throw std::runtime_error("Use --decomp blocks");

        if (steps < -1 || (T != -1.0 &&
            (!std::isfinite(T) || T <= 0.0)))
            throw std::runtime_error("Invalid time parameters");

        if (steps >= 0 && T >= 0.0)
            throw std::runtime_error("Choose steps or T");

        const double h = 1.0 / N;
        double dt = r * h * h;

        if (T >= 0.0) {
            double count = std::ceil(T / dt);
            if (count > std::numeric_limits<int>::max())
                throw std::runtime_error("Too many steps");

            steps = static_cast<int>(count);
            dt = T / steps;
            r = dt / (h*h);
        } else if (steps < 0) {
            steps = 500;
        }

        const double final_time = steps * dt;
        const double pi = std::acos(-1.0);

        // Create a 2D Cartesian process grid.
        // Dimension 0: rows (y), dimension 1: columns (x).
        int dims[2] = {0, 0};
        MPI_Dims_create(P, 2, dims);

        if (dims[0] > N-1 || dims[1] > N-1)
            throw std::runtime_error("Too many process-grid rows/columns");

        int periods[2] = {0, 0};
        MPI_Comm cart;

        MPI_Cart_create(
            MPI_COMM_WORLD, 2, dims, periods, 0, &cart
        );

        int coords[2];
        MPI_Cart_coords(cart, rank, 2, coords);

        // Cartesian neighbours
        int down, up, left, right;
        MPI_Cart_shift(cart, 0, 1, &down, &up);
        MPI_Cart_shift(cart, 1, 1, &left, &right);

        // Split a direction as evenly as possible.
        auto partition = [](int total, int parts, int coord) {
            int base = total / parts;
            int extra = total % parts;
            int count = base + (coord < extra ? 1 : 0);
            int first = 1 + coord*base + std::min(coord, extra);
            return std::pair<int,int>(first, count);
        };

        auto ypart = partition(N-1, dims[0], coords[0]);
        auto xpart = partition(N-1, dims[1], coords[1]);

        int first_y = ypart.first;
        int ny = ypart.second;
        int first_x = xpart.first;
        int nx = xpart.second;

        // Local block plus ghost layers on four sides.
        const int W = nx + 2;

        std::vector<double> u(
            static_cast<std::size_t>(ny+2)*W, 0.0
        );
        std::vector<double> next = u;

        auto idx = [W](int i, int j) {
            return j*W+i;
        };

        // Initial condition
        if (test_case == "V") {
            for (int j = 1; j <= ny; ++j) {
                int gy = first_y+j-1;

                for (int i = 1; i <= nx; ++i) {
                    int gx = first_x+i-1;
                    u[idx(i,j)] =
                        std::sin(pi*gx*h)*std::sin(pi*gy*h);
                }
            }
        }

        // Fixed physical boundary ghost cells
        if (test_case != "V") {
            if (down == MPI_PROC_NULL) {
                for (int i = 1; i <= nx; ++i)
                    u[idx(i,0)] = 1.0;
            }

            if (up == MPI_PROC_NULL) {
                for (int i = 1; i <= nx; ++i)
                    u[idx(i,ny+1)] = 1.0;
            }

            if (test_case == "1") {
                if (left == MPI_PROC_NULL) {
                    for (int j = 1; j <= ny; ++j)
                        u[idx(0,j)] = 1.0;
                }

                if (right == MPI_PROC_NULL) {
                    for (int j = 1; j <= ny; ++j)
                        u[idx(nx+1,j)] = 1.0;
                }
            }
        }

        next = u;

        // Derived MPI datatype for non-contiguous columns
        MPI_Datatype column_type;

        MPI_Type_vector(
            ny, 1, W, MPI_DOUBLE, &column_type
        );
        MPI_Type_commit(&column_type);

        double t_comp = 0.0;
        double t_comm = 0.0;

        MPI_Barrier(cart);
        double start = MPI_Wtime();

        for (int step = 0; step < steps; ++step) {

            double begin = MPI_Wtime();

            // Exchange upper/lower halo rows
            MPI_Sendrecv(
                &u[idx(1,ny)], nx, MPI_DOUBLE, up, 10,
                &u[idx(1,0)], nx, MPI_DOUBLE, down, 10,
                cart, MPI_STATUS_IGNORE
            );

            MPI_Sendrecv(
                &u[idx(1,1)], nx, MPI_DOUBLE, down, 11,
                &u[idx(1,ny+1)], nx, MPI_DOUBLE, up, 11,
                cart, MPI_STATUS_IGNORE
            );

            // Exchange left/right halo columns
            MPI_Sendrecv(
                &u[idx(nx,1)], 1, column_type, right, 20,
                &u[idx(0,1)], 1, column_type, left, 20,
                cart, MPI_STATUS_IGNORE
            );

            MPI_Sendrecv(
                &u[idx(1,1)], 1, column_type, left, 21,
                &u[idx(nx+1,1)], 1, column_type, right, 21,
                cart, MPI_STATUS_IGNORE
            );

            t_comm += MPI_Wtime()-begin;

            begin = MPI_Wtime();

            // Update all owned interior nodes
            for (int j = 1; j <= ny; ++j) {
                for (int i = 1; i <= nx; ++i) {
                    next[idx(i,j)] =
                        (1.0-4.0*r)*u[idx(i,j)]
                        + r*(
                            u[idx(i+1,j)] +
                            u[idx(i-1,j)] +
                            u[idx(i,j+1)] +
                            u[idx(i,j-1)]
                        );
                }
            }

            t_comp += MPI_Wtime()-begin;
            u.swap(next);
        }

        double t_total = MPI_Wtime()-start;

        double max_total=0, max_comp=0, max_comm=0;

        MPI_Reduce(&t_total, &max_total, 1, MPI_DOUBLE,
                   MPI_MAX, 0, cart);
        MPI_Reduce(&t_comp, &max_comp, 1, MPI_DOUBLE,
                   MPI_MAX, 0, cart);
        MPI_Reduce(&t_comm, &max_comm, 1, MPI_DOUBLE,
                   MPI_MAX, 0, cart);

        // Pack each process's owned nodes
        std::vector<double> packed(nx*ny);

        for (int j = 0; j < ny; ++j)
            for (int i = 0; i < nx; ++i)
                packed[j*nx+i] = u[idx(i+1,j+1)];

        // Collect packed blocks on rank 0
        std::vector<int> counts(P), displs(P);
        int offset = 0;

        for (int p = 0; p < P; ++p) {
            int c[2];
            MPI_Cart_coords(cart, p, 2, c);

            auto yp = partition(N-1, dims[0], c[0]);
            auto xp = partition(N-1, dims[1], c[1]);

            counts[p] = xp.second*yp.second;
            displs[p] = offset;
            offset += counts[p];
        }

        std::vector<double> gathered;
        if (rank == 0)
            gathered.resize(offset);

        MPI_Gatherv(
            packed.data(), nx*ny, MPI_DOUBLE,
            rank == 0 ? gathered.data() : nullptr,
            counts.data(), displs.data(), MPI_DOUBLE,
            0, cart
        );

        if (rank == 0) {
            int G = N+1;
            std::vector<double> full(
                static_cast<std::size_t>(G)*G, 0.0
            );

            // Reconstruct physical boundaries
            if (test_case != "V") {
                for (int k = 0; k <= N; ++k) {
                    full[k] = 1.0;
                    full[N*G+k] = 1.0;

                    if (test_case == "1") {
                        full[k*G] = 1.0;
                        full[k*G+N] = 1.0;
                    }
                }
            }

            // Unpack all rectangular blocks
            for (int p = 0; p < P; ++p) {
                int c[2];
                MPI_Cart_coords(cart, p, 2, c);

                auto yp = partition(N-1, dims[0], c[0]);
                auto xp = partition(N-1, dims[1], c[1]);

                int fy = yp.first, py = yp.second;
                int fx = xp.first, px = xp.second;

                for (int j = 0; j < py; ++j) {
                    for (int i = 0; i < px; ++i) {
                        full[(fy+j)*G+fx+i] =
                            gathered[displs[p]+j*px+i];
                    }
                }
            }

            // Verification against exact solution
            double err_inf = 0.0;
            double err_sum = 0.0;

            if (test_case == "V") {
                double factor =
                    std::exp(-2.0*pi*pi*final_time);

                for (int j = 0; j <= N; ++j) {
                    for (int i = 0; i <= N; ++i) {
                        double exact =
                            std::sin(pi*i*h) *
                            std::sin(pi*j*h) * factor;

                        double error =
                            std::abs(full[j*G+i]-exact);

                        err_inf = std::max(err_inf,error);
                        err_sum += error*error;
                    }
                }
            }

            // Save the complete field
            if (!output.empty()) {
                std::ofstream file(output,std::ios::binary);

                if (!file)
                    throw std::runtime_error("Cannot open output");

                file.write(
                    reinterpret_cast<const char*>(full.data()),
                    static_cast<std::streamsize>(
                        full.size()*sizeof(double)
                    )
                );

                if (!file)
                    throw std::runtime_error("Output write failed");
            }

            std::cout << std::setprecision(12)
                      << "decomp=blocks"
                      << " case=" << test_case
                      << " P=" << P
                      << " N=" << N
                      << " steps=" << steps
                      << " r=" << r
                      << " T=" << final_time
                      << " t_total=" << max_total
                      << " t_comp=" << max_comp
                      << " t_comm=" << max_comm;

            if (test_case == "V") {
                std::cout << " err_inf=" << err_inf
                          << " err_l2=" << h*std::sqrt(err_sum);
            }

            std::cout << std::endl;
        }

        MPI_Type_free(&column_type);
        MPI_Comm_free(&cart);
        MPI_Finalize();
        return 0;

    } catch (const std::exception& e) {
        std::cerr << "Rank " << rank
                  << ": " << e.what() << "\n";
        MPI_Abort(MPI_COMM_WORLD,1);
        return 1;
    }
}
