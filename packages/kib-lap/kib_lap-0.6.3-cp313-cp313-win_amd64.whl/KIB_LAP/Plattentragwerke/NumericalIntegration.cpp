// NumericalIntegration.cpp

#include "NumericalIntegration.h"

double NumericalIntegration::integrate_product(
    const std::function<double(double, int)> &func1,
    const std::function<double(double, int)> &func2,
    const std::vector<double> &points,
    int index1,
    int index2)
{
    // Trapezregel für die numerische Integration
    double sum = 0.0;
    for (size_t i = 0; i < points.size() - 1; ++i)
    {
        double x0 = points[i];
        double x1 = points[i + 1];
        double f0 = func1(x0, index1) * func2(x0, index2);
        double f1 = func1(x1, index1) * func2(x1, index2);
        sum += 0.5 * (f0 + f1) * (x1 - x0);
    }
    return sum;
}
