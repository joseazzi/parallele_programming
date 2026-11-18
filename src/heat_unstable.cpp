#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    try {
        int N = 100;
        int steps = -1;
        double r = 0.2;
        double T = -1.0;
        std::string simulation_case = "1";
        std::string decomp = "serial";
        std::string output;

        // Read command-line arguments
        for (int k = 1; k < argc; k += 2) {
            if (k + 1 >= argc)
                throw std::runtime_error("Missing option value");

            std::string option = argv[k];
            std::string value = argv[k + 1];

            if (option == "--N") N = std::stoi(value);
            else if (option == "--r") r = std::stod(value);
            else if (option == "--steps") steps = std::stoi(value);
            else if (option == "--T") T = std::stod(value);
            else if (option == "--case") simulation_case = value;
            else if (option == "--decomp") decomp = value;
            else if (option == "--out") output = value;
            else throw std::runtime_error("Unknown option: " + option);
        }

        if (N < 2)
            throw std::runtime_error("N must be >= 2");

        if (!std::isfinite(r) || r <=0.0)
            throw std::runtime_error(
                "Unstable or invalid r: must satisfy 0 < r <= 0.25"
            );

        if (simulation_case != "1" &&
            simulation_case != "2" &&
            simulation_case != "V")
            throw std::runtime_error("Case must be 1, 2 or V");

        if (decomp != "serial")
            throw std::runtime_error(
                "Only serial decomposition is implemented"
            );

        if (steps < -1)
            throw std::runtime_error("Invalid step count");

        if (T != -1.0 && (!std::isfinite(T) || T <= 0.0))
            throw std::runtime_error("T must be positive");

        if (steps >= 0 && T >= 0.0)
            throw std::runtime_error("Choose --steps or --T, not both");

        const double h = 1.0 / N;
        double dt = r * h * h;

        if (T >= 0.0) {
            double count = std::ceil(T / dt);
            if (count > std::numeric_limits<int>::max())
                throw std::runtime_error("Too many time steps");

            steps = static_cast<int>(count);
            dt = T / steps;
            r = dt / (h * h);
        } else if (steps < 0) {
            steps = 500;
        }

        const double final_time = steps * dt;
        const int width = N + 1;
        const std::size_t total =
            static_cast<std::size_t>(width) * width;

        std::vector<double> u(total, 0.0);
        std::vector<double> next(total, 0.0);

        auto index = [width](int i, int j) -> std::size_t {
            return static_cast<std::size_t>(j) * width + i;
        };

        const double pi = std::acos(-1.0);

        // Initialize the field
        if (simulation_case == "V") {
            for (int j = 1; j < N; ++j) {
                for (int i = 1; i < N; ++i) {
                    u[index(i, j)] =
                        std::sin(pi * i * h) *
                        std::sin(pi * j * h);
                }
            }
        } else {
            for (int k = 0; k <= N; ++k) {
                u[index(k, 0)] = 1.0;
                u[index(k, N)] = 1.0;

                if (simulation_case == "1") {
                    u[index(0, k)] = 1.0;
                    u[index(N, k)] = 1.0;
                }
            }
        }

        // In case 2, top and bottom own the corners.
        next = u;

        // Start timing: time-stepping only
        auto start = std::chrono::steady_clock::now();

        for (int step = 0; step < steps; ++step) {
            for (int j = 1; j < N; ++j) {
                for (int i = 1; i < N; ++i) {
                    next[index(i, j)] =
                        (1.0 - 4.0 * r) * u[index(i, j)]
                        + r * (
                            u[index(i + 1, j)] +
                            u[index(i - 1, j)] +
                            u[index(i, j + 1)] +
                            u[index(i, j - 1)]
                        );
                }
            }

            u.swap(next);
        }

        auto end = std::chrono::steady_clock::now();

        double elapsed =
            std::chrono::duration<double>(end - start).count();

        double err_inf = 0.0;
        double err_sum = 0.0;

        if (simulation_case == "V") {
            double factor = std::exp(-2.0 * pi * pi * final_time);

            for (int j = 0; j <= N; ++j) {
                for (int i = 0; i <= N; ++i) {
                    double exact =
                        std::sin(pi * i * h) *
                        std::sin(pi * j * h) * factor;

                    double error = std::abs(
                        u[index(i, j)] - exact
                    );

                    err_inf = std::max(err_inf, error);
                    err_sum += error * error;
                }
            }
        }

        // Optional raw binary output
        if (!output.empty()) {
            // Ubuntu ARM64 and x86-64 use little-endian here.
            std::ofstream file(output, std::ios::binary);

            if (!file)
                throw std::runtime_error(
                    "Cannot open output file"
                );

            for (double value : u) {
                file.write(
                    reinterpret_cast<const char*>(&value),
                    sizeof(double)
                );
            }

            if (!file)
                throw std::runtime_error("Output write failed");
        }

        // Summary
        std::cout << std::setprecision(12)
                  << "decomp=serial"
                  << " case=" << simulation_case
                  << " P=1"
                  << " N=" << N
                  << " steps=" << steps
                  << " r=" << r
                  << " T=" << final_time
                  << " t_total=" << elapsed
                  << " t_comp=" << elapsed
                  << " t_comm=0";

        if (simulation_case == "V") {
            std::cout << " err_inf=" << err_inf
                      << " err_l2=" << h * std::sqrt(err_sum);
        }

        std::cout << "\n";

        return 0;
    }
    catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
}
