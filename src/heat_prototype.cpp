#include <iostream>
#include <vector>
#include <iomanip>
#include <utility>

int main() {

    // Parametres de la simulation
    const int N = 4;
    const double r = 0.2;
    const int steps = 100;

    // Deux tableaux pour les temperatures
    std::vector<double> u((N + 1) * (N + 1), 0.0);
    std::vector<double> next = u;

    // Convertir (i,j) en indice du tableau
    auto index = [N](int i, int j) {
        return j * (N + 1) + i;
    };

    // Initialiser les quatre bords a 1
    for (int k = 0; k <= N; ++k) {
        u[index(k, 0)] = 1.0;
        u[index(k, N)] = 1.0;
        u[index(0, k)] = 1.0;
        u[index(N, k)] = 1.0;
    }

    next = u;

    // Simulation de la diffusion thermique
    for (int step = 0; step < steps; ++step) {

        // Calculer les nouvelles temperatures
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

        // Echanger les tableaux sans les copier
        u.swap(next);
    }

    // Afficher les temperatures finales
    std::cout << "Temperatures apres "
              << steps << " etapes :\n\n";

    for (int j = N; j >= 0; --j) {
        for (int i = 0; i <= N; ++i) {
            std::cout << std::fixed
                      << std::setprecision(4)
                      << u[index(i, j)] << " ";
        }
        std::cout << "\n";
    }

    return 0;
}
