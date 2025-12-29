// plate_buckling.cpp

#define _USE_MATH_DEFINES // Für M_PI unter Windows

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <vector>
#include <iostream>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;

// Angepasste Funktion zur Berechnung der reinen Plattensteifigkeit D_plate (ohne Steifenbeiträge)
double calculate_D(double x, double y, double D_plate)
{
    return D_plate;
}

// Funktion zur numerischen Integration des Matrixelements K_ij (Plattenbeitrag)
double integrate_K_element_cpp(int m_i, int n_i, int m_j, int n_j,
                               double a, double b,
                               double D_plate, double nu,
                               double E)
{
    // Anzahl der Unterteilungen
    const int n_x = 100;
    const int n_y = 100;
    double dx = a / n_x;
    double dy = b / n_y;
    double integral = 0.0;

    for (int i = 0; i <= n_x; ++i)
    {
        double x = i * dx;
        for (int j = 0; j <= n_y; ++j)
        {
            double y = j * dy;

            // Berechnung der reinen Plattensteifigkeit D(x, y)
            double D_xy = calculate_D(x / a, y / b, D_plate);

            // Ansatzfunktionen und deren Ableitungen
            double sin_m_i_x = sin(m_i * M_PI * x / a);
            double sin_n_i_y = sin(n_i * M_PI * y / b);
            double sin_m_j_x = sin(m_j * M_PI * x / a);
            double sin_n_j_y = sin(n_j * M_PI * y / b);

            double cos_m_i_x = cos(m_i * M_PI * x / a);
            double cos_n_i_y = cos(n_i * M_PI * y / b);
            double cos_m_j_x = cos(m_j * M_PI * x / a);
            double cos_n_j_y = cos(n_j * M_PI * y / b);

            double d2phi_i_dx2 = -pow(m_i * M_PI / a, 2) * sin_m_i_x * sin_n_i_y;
            double d2phi_i_dy2 = -pow(n_i * M_PI / b, 2) * sin_m_i_x * sin_n_i_y;
            double d2phi_i_dxdy = (m_i * M_PI / a) * (n_i * M_PI / b) * cos_m_i_x * cos_n_i_y;

            double d2phi_j_dx2 = -pow(m_j * M_PI / a, 2) * sin_m_j_x * sin_n_j_y;
            double d2phi_j_dy2 = -pow(n_j * M_PI / b, 2) * sin_m_j_x * sin_n_j_y;
            double d2phi_j_dxdy = (m_j * M_PI / a) * (n_j * M_PI / b) * cos_m_j_x * cos_n_j_y;

            // Integrand mit allen Termen
            double integrand = D_xy * (d2phi_i_dx2 * d2phi_j_dx2 +
                                       d2phi_i_dy2 * d2phi_j_dy2 +
                                       2 * nu * d2phi_i_dx2 * d2phi_j_dy2 +
                                       2 * (1 - nu) * d2phi_i_dxdy * d2phi_j_dxdy);

            // Gewichte für Trapezregel
            double wx = (i == 0 || i == n_x) ? 0.5 : 1.0;
            double wy = (j == 0 || j == n_y) ? 0.5 : 1.0;

            integral += integrand * wx * wy;
        }
    }
    integral *= dx * dy;

    return integral;
}

double integrate_longitudinal_stiffener_energy_cpp(int m_i, int n_i, int m_j, int n_j,
                                                   double a, double b,
                                                   double E, double I_S,
                                                   double L_S, double x_stiffener)
{
    double x_s = x_stiffener;

    // Vorberechnung der konstanten Werte
    double sin_m_i_x = sin(m_i * M_PI * x_s / a);
    double sin_m_j_x = sin(m_j * M_PI * x_s / a);
    double coef_n_i = (n_i * M_PI / b);
    double coef_n_j = (n_j * M_PI / b);

    double constant_terms = pow(coef_n_i * coef_n_j, 2) * sin_m_i_x * sin_m_j_x;

    double A = coef_n_i;
    double B = coef_n_j;

    double integral_y = 0.0;

    if (n_i == n_j)
    {
        // Fall n_i == n_j
        integral_y = 0.5 * (L_S - sin(2 * A * L_S) / (2 * A));
    }
    else
    {
        // Fall n_i != n_j
        integral_y = 0.5 * (sin((A - B) * L_S) / (A - B) -
                            sin((A + B) * L_S) / (A + B));
    }

    double integral = E * I_S * constant_terms * integral_y;

    return integral;
}

//_______________________________ INTEGRALLÖSUNG ANFANG_______________________________________________

// // Funktion zur Berechnung der Steifenenergie (Längssteifen)
// double integrate_longitudinal_stiffener_energy_cpp(int m_i, int n_i, int m_j, int n_j,
//                                                    double a, double b,
//                                                    double E, double I_S,
//                                                    double L_S, double x_stiffener)
// {
//     double integral = 0.0;

//     // Anzahl der Unterteilungen entlang der Steife
//     const int n_steps = 1000;
//     double dy = L_S / n_steps;

//     // Position der Längssteife
//     double x_s = x_stiffener; // Kann auch als Parameter übergeben werden

//     // Vorberechnung der konstanten Werte
//     double sin_m_i_x = sin(m_i * M_PI * x_s / a);
//     double sin_m_j_x = sin(m_j * M_PI * x_s / a);
//     double coef_n_i = pow(n_i * M_PI / b, 2);
//     double coef_n_j = pow(n_j * M_PI / b, 2);

//     for (int i = 0; i <= n_steps; ++i)
//     {
//         double y = i * dy;

//         double sin_n_i_y = sin(n_i * M_PI * y / b);
//         double sin_n_j_y = sin(n_j * M_PI * y / b);

//         double d2phi_i_dy2 = -coef_n_i * sin_m_i_x * sin_n_i_y;
//         double d2phi_j_dy2 = -coef_n_j * sin_m_j_x * sin_n_j_y;

//         double integrand = d2phi_i_dy2 * d2phi_j_dy2;

//         // Gewichte für die Trapezregel
//         double weight = 1.0;
//         if (i == 0 || i == n_steps)
//             weight = 0.5;

//         integral += integrand * weight;
//     }

//     integral *= E * I_S * dy;

//     return integral;
// }

// double integrate_transverse_stiffener_energy_cpp(int m_i, int n_i, int m_j, int n_j,
//                                                  double a, double b,
//                                                  double E, double I_T,
//                                                  double L_T, double y_stiffener)
// {
//     const int n_steps = 1000;
//     double dx = L_T / n_steps;
//     double y_s = y_stiffener; // Position der Quersteife

//     double sin_n_i_y = sin(n_i * M_PI * y_s / b);
//     double sin_n_j_y = sin(n_j * M_PI * y_s / b);

//     double integral = 0.0;

//     for (int i = 0; i <= n_steps; ++i)
//     {
//         double x = i * dx;

//         // Berechnung der Sinusfunktionen in x-Richtung
//         double sin_m_i_x = sin(m_i * M_PI * x / a);
//         double sin_m_j_x = sin(m_j * M_PI * x / a);

//         // Zweite Ableitungen der Basisfunktionen
//         double d2phi_i_dx2 = -pow(m_i * M_PI / a, 2) * sin_m_i_x * sin_n_i_y;
//         double d2phi_j_dx2 = -pow(m_j * M_PI / a, 2) * sin_m_j_x * sin_n_j_y;

//         double integrand = d2phi_i_dx2 * d2phi_j_dx2;

//         // Trapezregel: Gewichte
//         double weight = 1.0;
//         if (i == 0 || i == n_steps)
//             weight = 0.5;

//         integral += integrand * weight;
//     }

//     integral *= E * I_T * dx;

//     return integral;
// }

// double integrate_G_longi_stiffener_energy(int m_i, int n_i, int m_j, int n_j,
//                                           double a, double b,
//                                           double E, double A_L, double sig_i,
//                                           double L_T, double y_stiffener)
// {
//     const int n_steps = 1000;
//     double dx = L_T / n_steps;
//     double y_s = y_stiffener; // Position der Quersteife

//     double sin_n_i_y = sin(n_i * M_PI * y_s / b);
//     double sin_n_j_y = sin(n_j * M_PI * y_s / b);

//     double integral = 0.0;

//     for (int i = 0; i <= n_steps; ++i)
//     {
//         double x = i * dx;

//         // Berechnung der Sinusfunktionen in x-Richtung
//         double cos_m_i_x = cos(m_i * M_PI * x / a);
//         double cos_m_j_x = cos(m_j * M_PI * x / a);

//         // Zweite Ableitungen der Basisfunktionen
//         double d2phi_i_dx = m_i * M_PI / a * cos_m_i_x * sin_n_i_y;
//         double d2phi_j_dx = m_j * M_PI / a * cos_m_j_x * sin_n_j_y;

//         double integrand = d2phi_i_dx * d2phi_j_dx;

//         // Trapezregel: Gewichte
//         double weight = 1.0;
//         if (i == 0 || i == n_steps)
//             weight = 0.5;

//         integral += integrand * weight;
//     }

//     integral *= A_L * sig_i * dx;

//     return integral;
// }

//_______________________________ INTEGRALLÖSUNG ENDE_______________________________________________

double integrate_transverse_stiffener_energy_cpp(int m_i, int n_i, int m_j, int n_j,
                                                 double a, double b,
                                                 double E, double I_T,
                                                 double L_T, double y_stiffener)
{
    // Analytisch integrierte Funktionen für die Längssteifen.

    double y_s = y_stiffener;

    double sin_n_i_y = sin(n_i * M_PI * y_s / b);
    double sin_n_j_y = sin(n_j * M_PI * y_s / b);

    double k_i = m_i * M_PI / a;
    double k_j = m_j * M_PI / a;

    double K = pow(k_i * k_j, 2) * sin_n_i_y * sin_n_j_y;

    double integral;

    if (m_i != m_j)
    {
        double alpha = (k_i - k_j);
        double beta = (k_i + k_j);

        double term1 = sin(alpha * L_T) / alpha;
        double term2 = sin(beta * L_T) / beta;

        integral = (term1 - term2) * (K / 2.0);
    }
    else
    {
        double term1 = L_T / 2.0;
        double term2 = sin(2 * k_i * L_T) / (4 * k_i);

        integral = (term1 - term2) * K;
    }

    integral *= E * I_T;

    return integral;
}

double integrate_G_longi_stiffener_energy(int m_i, int n_i, int m_j, int n_j,
                                          double a, double b,
                                          double E, double A_L, double sig_i,
                                          double L_T, double y_stiffener)
{
    double y_s = y_stiffener;

    // Vorberechnung der konstanten Werte
    double sin_n_i_y = sin(n_i * M_PI * y_s / b);
    double sin_n_j_y = sin(n_j * M_PI * y_s / b);

    double coef_m_i = m_i * M_PI / a;
    double coef_m_j = m_j * M_PI / a;

    double constant_terms = coef_m_i * coef_m_j * sin_n_i_y * sin_n_j_y;

    double integral_x = 0.0;

    if (m_i == m_j)
    {
        // Fall m_i == m_j
        double term1 = L_T / 2.0;
        double term2 = sin(2.0 * m_i * M_PI * L_T / a) * (a / (4.0 * M_PI * m_i));
        integral_x = term1 + term2;
    }
    else
    {
        // Fall m_i != m_j
        double delta_m = m_i - m_j;
        double sum_m = m_i + m_j;

        double term1 = sin(delta_m * M_PI * L_T / a) / (2.0 * delta_m * M_PI / a);
        double term2 = sin(sum_m * M_PI * L_T / a) / (2.0 * sum_m * M_PI / a);

        integral_x = term1 + term2;
    }

    double integral = A_L * sig_i * constant_terms * integral_x;

    return integral;
}

// Funktion zur numerischen Integration des Matrixelements G_ij mit Simpson-Methode
double integrate_G_element_cpp(int m_i, int n_i, int m_j, int n_j,
                               double dphi_i_dx, double dphi_i_dy,
                               double dphi_j_dx, double dphi_j_dy,
                               double a, double b,
                               double Nx0, double Nx1, double Ny0, double Ny1, double Nxy)
{
    // Anzahl der Unterteilungen in x- und y-Richtung (müssen gerade sein)
    int n_x = 100;
    int n_y = 100;

    // Sicherstellen, dass n_x und n_y gerade sind
    if (n_x % 2 != 0)
        n_x += 1;
    if (n_y % 2 != 0)
        n_y += 1;

    double dx = a / n_x;
    double dy = b / n_y;

    double integral = 0.0;

    for (int i = 0; i <= n_x; ++i)
    {
        double x = i * dx;

        double sin_m_i_x = sin(m_i * M_PI * x / a);
        double cos_m_i_x = cos(m_i * M_PI * x / a);
        double sin_m_j_x = sin(m_j * M_PI * x / a);
        double cos_m_j_x = cos(m_j * M_PI * x / a);

        // Gewichte für Simpson-Regel in x-Richtung
        double wx;
        if (i == 0 || i == n_x)
            wx = 1.0;
        else if (i % 2 == 0)
            wx = 2.0;
        else
            wx = 4.0;

        for (int j = 0; j <= n_y; ++j)
        {
            double y = j * dy;

            // Korrekte Definition von Nx und Ny
            double Nx = Nx0 + Nx1 / b * y;
            double Ny = Ny0 + Ny1 / a * x;

            // Gewichte für Simpson-Regel in y-Richtung
            double wy;
            if (j == 0 || j == n_y)
                wy = 1.0;
            else if (j % 2 == 0)
                wy = 2.0;
            else
                wy = 4.0;

            // Ansatzfunktionen und deren Ableitungen
            double sin_n_i_y = sin(n_i * M_PI * y / b);
            double cos_n_i_y = cos(n_i * M_PI * y / b);
            double sin_n_j_y = sin(n_j * M_PI * y / b);
            double cos_n_j_y = cos(n_j * M_PI * y / b);

            double phi_i_dx = dphi_i_dx * cos_m_i_x * sin_n_i_y;
            double phi_i_dy = dphi_i_dy * sin_m_i_x * cos_n_i_y;
            double phi_j_dx = dphi_j_dx * cos_m_j_x * sin_n_j_y;
            double phi_j_dy = dphi_j_dy * sin_m_j_x * cos_n_j_y;

            // Beiträge zur geometrischen Steifigkeit
            double term_x = Nx * phi_i_dx * phi_j_dx;
            double term_y = Ny * phi_i_dy * phi_j_dy;
            double term_xy = Nxy * (phi_i_dx * phi_j_dy + phi_i_dy * phi_j_dx);

            double integrand = (term_x + term_y + term_xy);

            integral += integrand * wx * wy;
        }
    }

    integral *= (dx * dy) / 9.0;

    return integral;
}

// Funktion zur Assemblierung der Matrizen K und G mit Berücksichtigung von Längs- und Quersteifen
void assemble_matrices_with_stiffeners_cpp(py::array_t<int> m_list,
                                           py::array_t<int> n_list,
                                           double a, double b,
                                           double Nx0, double Nx1, double Ny0, double Ny1, double Nxy,
                                           double E, double t, double nu,
                                           py::array_t<double> x_s_positions,
                                           py::array_t<double> I_s_values,
                                           py::array_t<double> A_s_values,
                                           py::array_t<double> y_s_positions,
                                           py::array_t<double> I_t_values,
                                           py::array_t<double> A_t_values,
                                           py::array_t<double> K_flat,
                                           py::array_t<double> G_flat)
{
    auto m_list_unchecked = m_list.unchecked<1>();
    auto n_list_unchecked = n_list.unchecked<1>();
    auto K_flat_unchecked = K_flat.mutable_unchecked<1>();
    auto G_flat_unchecked = G_flat.mutable_unchecked<1>();

    auto x_s_positions_unchecked = x_s_positions.unchecked<1>();
    auto I_s_values_unchecked = I_s_values.unchecked<1>();
    auto A_s_values_unchecked = A_s_values.unchecked<1>();

    auto y_s_positions_unchecked = y_s_positions.unchecked<1>();
    auto I_t_values_unchecked = I_t_values.unchecked<1>();
    auto A_t_values_unchecked = A_t_values.unchecked<1>();

    double sig_i = 0;

    // Extrahieren der Steifenpositionen und -werte in Vektoren
    std::vector<double> x_s_positions_vec(x_s_positions.size());
    std::vector<double> I_s_values_vec(I_s_values.size());
    std::vector<double> A_s_values_vec(A_s_values.size());

    for (size_t i = 0; i < x_s_positions.size(); ++i)
    {
        x_s_positions_vec[i] = x_s_positions_unchecked(i);
        I_s_values_vec[i] = I_s_values_unchecked(i);
        A_s_values_vec[i] = A_s_values_unchecked(i);
    }

    std::vector<double> y_s_positions_vec(y_s_positions.size());
    std::vector<double> I_t_values_vec(I_t_values.size());
    std::vector<double> A_t_values_vec(A_t_values.size());

    for (size_t i = 0; i < y_s_positions.size(); ++i)
    {
        y_s_positions_vec[i] = y_s_positions_unchecked(i);
        I_t_values_vec[i] = I_t_values_unchecked(i);
        A_t_values_vec[i] = A_t_values_unchecked(i);
    }

    int num_terms = static_cast<int>(m_list.size());
    double D_plate = E * pow(t, 3) / (12 * (1 - nu * nu));

#pragma omp parallel for
    for (int idx_i = 0; idx_i < num_terms; ++idx_i)
    {
        int m_i = m_list_unchecked(idx_i);
        int n_i = n_list_unchecked(idx_i);

        double dphi_i_dx = m_i * M_PI / a;
        double dphi_i_dy = n_i * M_PI / b;

        for (int idx_j = 0; idx_j < num_terms; ++idx_j)
        {
            int m_j = m_list_unchecked(idx_j);
            int n_j = n_list_unchecked(idx_j);
            int idx = idx_i * num_terms + idx_j;

            // Steifigkeitsmatrix K (Plattenbeitrag)
            double K_ij = integrate_K_element_cpp(
                m_i, n_i, m_j, n_j,
                a, b,
                D_plate, nu,
                E);

            // Integration der Steifenenergie (Längssteifen)
            for (size_t s = 0; s < x_s_positions_vec.size(); ++s)
            {
                double I_S = I_s_values_vec[s];
                double L_S = b; // Länge der Längssteife entlang y-Richtung
                double x_stiff = x_s_positions_vec[s];
                K_ij += integrate_longitudinal_stiffener_energy_cpp(
                    m_i, n_i, m_j, n_j,
                    a, b,
                    E, I_S,
                    L_S, x_stiff);
            }

            // Integration der Steifenenergie (Quersteifen)
            for (size_t r = 0; r < y_s_positions_vec.size(); ++r)
            {
                double I_T = I_t_values_vec[r];
                double y_stiff = y_s_positions_vec[r];
                double L_T = a; // Länge der Quersteife entlang x-Richtung

                K_ij += integrate_transverse_stiffener_energy_cpp(
                    m_i, n_i, m_j, n_j,
                    a, b,
                    E, I_T,
                    L_T, y_stiff);
            }

            K_flat_unchecked(idx) = K_ij;

            // Geometrische Steifigkeitsmatrix G
            double dphi_j_dx = m_j * M_PI / a;
            double dphi_j_dy = n_j * M_PI / b;

            double G_ij = integrate_G_element_cpp(
                m_i, n_i, m_j, n_j,
                dphi_i_dx, dphi_i_dy, dphi_j_dx, dphi_j_dy,
                a, b, Nx0, Nx1, Ny0, Ny1, Nxy);

            // Integration der Steifenenergie (Längssteifen)
            for (size_t r = 0; r < y_s_positions_vec.size(); ++r)
            {
                double A_L = A_t_values_vec[r];
                double y_stiff = y_s_positions_vec[r];
                double L_T = a; // Länge der Quersteife entlang x-Richtung

                double sig_i_l = (Nx0 + Nx1 * y_stiff / b) / t;

                G_ij += integrate_G_longi_stiffener_energy(
                    m_i, n_i, m_j, n_j,
                    a, b,
                    E, A_L, sig_i_l, L_T, y_stiff);
            }

            G_flat_unchecked(idx) = G_ij;
        }
    }
}

// Pybind11-Moduldefinition
PYBIND11_MODULE(plate_buckling_cpp, m)
{
    m.def("assemble_matrices_with_stiffeners_cpp", &assemble_matrices_with_stiffeners_cpp,
          "Assemblierung der Matrizen K und G mit Berücksichtigung von Längs- und Quersteifen");
}
