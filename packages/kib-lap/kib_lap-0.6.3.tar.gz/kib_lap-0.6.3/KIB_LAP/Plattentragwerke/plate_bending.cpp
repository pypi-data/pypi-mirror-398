// plate_bending.cpp

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include <vector>
#include <cmath> // Für pow und trigonometrische Funktionen
#include "Functions.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace py = pybind11;

// Stiffeners
// The stiffener methods are currently written for navier boundary conditions ONLY!

double integrate_longitudinal_stiffener_energy_cpp(int m_i, int n_i, int m_j, int n_j,
                                                   double a, double b,
                                                   double E, double I_S,
                                                   double L_S, double x_stiffener)
{
    double integral = 0.0;

    // Anzahl der Unterteilungen entlang der Steife
    const int n_steps = 1000;
    double dy = L_S / n_steps;

    // Position der Längssteife
    double x_s = x_stiffener; // Kann auch als Parameter übergeben werden

    // Vorberechnung der konstanten Werte
    double sin_m_i_x = sin(m_i * M_PI * x_s / a);
    double sin_m_j_x = sin(m_j * M_PI * x_s / a);
    double coef_n_i = pow(n_i * M_PI / b, 2);
    double coef_n_j = pow(n_j * M_PI / b, 2);

    auto nf = NumericFunctions();

    for (int i = 0; i <= n_steps; ++i)
    {
        double y = i * dy;

        double d2phi_i_dy2 = nf.function_1(x_s, m_i) * nf.function_2yy(y, n_i);
        double d2phi_j_dy2 = nf.function_1(x_s, m_j) * nf.function_2yy(y, n_j);

        double integrand = d2phi_i_dy2 * d2phi_j_dy2;

        // Gewichte für die Trapezregel
        double weight = 1.0;
        if (i == 0 || i == n_steps)
            weight = 0.5;

        integral += integrand * weight;
    }

    integral *= E * I_S * dy;

    return integral;
}

double integrate_transverse_stiffener_energy_cpp(int m_i, int n_i, int m_j, int n_j,
                                                 double a, double b,
                                                 double E, double I_T,
                                                 double L_T, double y_stiffener)
{
    const int n_steps = 1000;
    double dx = L_T / n_steps;
    double y_s = y_stiffener; // Position der Quersteife

    double integral = 0.0;
    auto nf = NumericFunctions();

    for (int i = 0; i <= n_steps; ++i)
    {
        double x = i * dx;

        // Zweite Ableitungen der Basisfunktionen
        double d2phi_i_dx2 = nf.function_1xx(x, m_i) * nf.function_2(y_s, n_i);
        double d2phi_j_dx2 = nf.function_1xx(x, m_j) * nf.function_2(y_s, n_j);

        double integrand = d2phi_i_dx2 * d2phi_j_dx2;

        // Trapezregel: Gewichte
        double weight = 1.0;
        if (i == 0 || i == n_steps)
            weight = 0.5;

        integral += integrand * weight;
    }

    integral *= E * I_T * dx;

    return integral;
}

std::vector<double> create_discretized_list(double start, double end, int num_intervals)
{
    std::vector<double> list;
    double step = (end - start) / num_intervals;
    for (int i = 0; i <= num_intervals; ++i)
    {
        list.push_back(start + i * step);
    }
    return list;
}

std::vector<std::vector<double>> assemble_stiffness_matrix(
    double D_11, double D_22, double D_12, double D_66,
    int reihen, int n_inte, double a, double b, const std::string &support,
    double E,
    py::array_t<double> x_s_positions,
    py::array_t<double> I_s_values,
    py::array_t<double> y_s_positions,
    py::array_t<double> I_t_values)
{
    NumericFunctions nf(a, b, support);

    std::vector<double> list_a = create_discretized_list(0.0, a, n_inte);
    std::vector<double> list_b = create_discretized_list(0.0, b, n_inte);

    int matrix_size = reihen * reihen;
    std::vector<std::vector<double>> matrix(matrix_size, std::vector<double>(matrix_size, 0.0));

    auto x_s_positions_unchecked = x_s_positions.unchecked<1>();
    auto I_s_values_unchecked = I_s_values.unchecked<1>();

    auto y_s_positions_unchecked = y_s_positions.unchecked<1>();
    auto I_t_values_unchecked = I_t_values.unchecked<1>();

    // Extrahieren der Unterzugpositionen und -werte in Vektoren
    std::vector<double> x_s_positions_vec(x_s_positions.size());
    std::vector<double> I_s_values_vec(I_s_values.size());

    for (size_t i = 0; i < x_s_positions.size(); ++i)
    {
        x_s_positions_vec[i] = x_s_positions_unchecked(i);
        I_s_values_vec[i] = I_s_values_unchecked(i);
    }

    std::vector<double> y_s_positions_vec(y_s_positions.size());
    std::vector<double> I_t_values_vec(I_t_values.size());

    for (size_t i = 0; i < y_s_positions.size(); ++i)
    {
        y_s_positions_vec[i] = y_s_positions_unchecked(i);
        I_t_values_vec[i] = I_t_values_unchecked(i);
    }

    // Generierung der Steifigkeitsmatrix
    for (int m = 1; m <= reihen; ++m)
    {
        for (int n = 1; n <= reihen; ++n)
        {
            for (int p = 1; p <= reihen; ++p)
            {
                for (int q = 1; q <= reihen; ++q)
                {
                    double lambda_x22_pm = NumericalIntegration::integrate_product(
                        [&nf](double x, int p)
                        { return nf.function_1xx(x, p); },
                        [&nf](double x, int m)
                        { return nf.function_1xx(x, m); },
                        list_a, p, m);

                    double lambda_x22_mp = NumericalIntegration::integrate_product(
                        [&nf](double x, int m)
                        { return nf.function_1xx(x, m); },
                        [&nf](double x, int p)
                        { return nf.function_1xx(x, p); },
                        list_a, m, p);

                    double lambda_y00_nq = NumericalIntegration::integrate_product(
                        [&nf](double y, int n)
                        { return nf.function_2(y, n); },
                        [&nf](double y, int q)
                        { return nf.function_2(y, q); },
                        list_b, n, q);

                    double lambda_y00_qn = NumericalIntegration::integrate_product(
                        [&nf](double y, int q)
                        { return nf.function_2(y, q); },
                        [&nf](double y, int n)
                        { return nf.function_2(y, n); },
                        list_b, q, n);

                    double lambda_x00_mp = NumericalIntegration::integrate_product(
                        [&nf](double x, int m)
                        { return nf.function_1(x, m); },
                        [&nf](double x, int p)
                        { return nf.function_1(x, p); },
                        list_a, m, p);

                    double lambda_x00_pm = NumericalIntegration::integrate_product(
                        [&nf](double x, int p)
                        { return nf.function_1(x, p); },
                        [&nf](double x, int m)
                        { return nf.function_1(x, m); },
                        list_a, p, m);

                    double lambda_y22_nq = NumericalIntegration::integrate_product(
                        [&nf](double y, int n)
                        { return nf.function_2yy(y, n); },
                        [&nf](double y, int q)
                        { return nf.function_2yy(y, q); },
                        list_b, n, q);

                    double lambda_y22_qn = NumericalIntegration::integrate_product(
                        [&nf](double y, int q)
                        { return nf.function_2yy(y, q); },
                        [&nf](double y, int n)
                        { return nf.function_2yy(y, n); },
                        list_b, q, n);

                    double lambda_x20_mp = NumericalIntegration::integrate_product(
                        [&nf](double x, int m)
                        { return nf.function_1xx(x, m); },
                        [&nf](double x, int p)
                        { return nf.function_1(x, p); },
                        list_a, m, p);

                    double lambda_x20_pm = NumericalIntegration::integrate_product(
                        [&nf](double x, int p)
                        { return nf.function_1xx(x, p); },
                        [&nf](double x, int m)
                        { return nf.function_1(x, m); },
                        list_a, p, m);

                    double lambda_y02_nq = NumericalIntegration::integrate_product(
                        [&nf](double y, int n)
                        { return nf.function_2(y, n); },
                        [&nf](double y, int q)
                        { return nf.function_2yy(y, q); },
                        list_b, n, q);

                    double lambda_y02_qn = NumericalIntegration::integrate_product(
                        [&nf](double y, int q)
                        { return nf.function_2(y, q); },
                        [&nf](double y, int n)
                        { return nf.function_2yy(y, n); },
                        list_b, q, n);

                    double lambda_x11_mp = NumericalIntegration::integrate_product(
                        [&nf](double x, int m)
                        { return nf.function_1x(x, m); },
                        [&nf](double x, int p)
                        { return nf.function_1x(x, p); },
                        list_a, m, p);

                    double lambda_x11_pm = NumericalIntegration::integrate_product(
                        [&nf](double x, int p)
                        { return nf.function_1x(x, p); },
                        [&nf](double x, int m)
                        { return nf.function_1x(x, m); },
                        list_a, p, m);

                    double lambda_y11_nq = NumericalIntegration::integrate_product(
                        [&nf](double y, int n)
                        { return nf.function_2y(y, n); },
                        [&nf](double y, int q)
                        { return nf.function_2y(y, q); },
                        list_b, n, q);

                    double lambda_y11_qn = NumericalIntegration::integrate_product(
                        [&nf](double y, int q)
                        { return nf.function_2y(y, q); },
                        [&nf](double y, int n)
                        { return nf.function_2y(y, n); },
                        list_b, q, n);

                    double value = 0.0;

                    if (m == p)
                    {
                        value =
                            0.5 * D_11 * (lambda_x22_mp * lambda_y00_nq + lambda_x22_pm * lambda_y00_qn) +
                            0.5 * D_22 * (lambda_x00_mp * lambda_y22_nq + lambda_x00_pm * lambda_y22_qn) +
                            D_12 * (lambda_x20_mp * lambda_y02_nq + lambda_x20_pm * lambda_y02_qn) +
                            2 * D_66 * (lambda_x11_pm * lambda_y11_nq + lambda_x11_mp * lambda_y11_nq);
                    }
                    else
                    {
                        value =
                            0.5 * D_11 * (lambda_x22_mp * lambda_y00_nq + lambda_x22_pm * lambda_y00_qn) +
                            0.5 * D_22 * (lambda_x00_mp * lambda_y22_nq + lambda_x00_pm * lambda_y22_qn) +
                            D_12 * (lambda_x20_mp * lambda_y02_nq + lambda_x20_pm * lambda_y02_qn) +
                            2 * D_66 * (lambda_x11_mp * lambda_y11_nq + lambda_x11_pm * lambda_y11_qn);
                    }
                    for (size_t r = 0; r < x_s_positions_vec.size(); ++r)
                    {
                        // Angenommen L_S ist immer b oder Sie haben einen festen Wert:
                        double L_S = b;
                        double stiffener_long = integrate_longitudinal_stiffener_energy_cpp(
                            m, n, p, q,
                            a, b, E, I_s_values_vec[r],
                            L_S, x_s_positions_vec[r]);
                        value += stiffener_long;
                    }

                    for (size_t r = 0; r < y_s_positions_vec.size(); ++r)
                    {
                        double L_T = a; // oder ein anderer Wert, je nach Definition
                        double stiffener_trans = integrate_transverse_stiffener_energy_cpp(
                            m, n, p, q,
                            a, b, E, I_t_values_vec[r],
                            L_T, y_s_positions_vec[r]);
                        value += stiffener_trans;
                    }

                    if (std::abs(value) < 1e-9)
                    {
                        value = 0.0;
                    }

                    int row = n - 1 + reihen * (m - 1);
                    int col = q - 1 + reihen * (p - 1);
                    matrix[row][col] = value;
                }
            }
        }
    }

    return matrix;
}

PYBIND11_MODULE(plate_bending_cpp, m)
{
    m.doc() = "pybind11 Modul zur Assemblierung der Steifigkeitsmatrix für Plattenbiegung";

    m.def("assemble_stiffness_matrix", &assemble_stiffness_matrix,
          "Assemblierung der Steifigkeitsmatrix inklusive Unterzüge",
          py::arg("D_11"), py::arg("D_22"), py::arg("D_12"), py::arg("D_66"),
          py::arg("reihen"), py::arg("n_inte"), py::arg("a"), py::arg("b"), py::arg("support"),
          py::arg("E"),
          py::arg("x_s_positions"),
          py::arg("I_s_values"),
          py::arg("y_s_positions"),
          py::arg("I_t_values"));
}