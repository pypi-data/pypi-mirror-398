// Functions.cpp

#include "Functions.h"
#include <cmath>
#include <iostream>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

NumericFunctions::NumericFunctions(double a, double b, const std::string &support)
    : a_(a), b_(b), support_(support)
{
}

double NumericFunctions::function_1(double x, int m)
{
    if (support_ == "hhhh")
    {
        return std::sin(x * M_PI / a_ * m);
    }
    else if (support_ == "cccc")
    {
        return 1 - std::cos(2 * m * M_PI * x / a_);
    }
    else if (support_ == "hhff")
    {
        double lambda_m = (0.50 + static_cast<double>(m) - 1) * M_PI;

        if (m == 2)
        {
            lambda_m = 4.730041;
        }
        else if (m == 3)
        {
            lambda_m = 7.853205;
        }
        else if (m == 4)
        {
            lambda_m = 10.99561;
        }
        double alpha = lambda_m / a_;

        double a_j = (std::sinh(lambda_m) - std::sin(lambda_m)) / (std::cosh(lambda_m) - std::cos(lambda_m));
        if (m > 1)
        {
            return (std::sin(alpha * x) + std::sinh(alpha * x)) / (std::sin(lambda_m) - std::sinh(lambda_m)) 
            - a_j * (std::cosh(alpha * x) + std::cos(alpha * x)) / (std::cos(lambda_m) - std::cosh(lambda_m));
        }
        else
        {
            return 1;
        }
    }
    else if (support_ == "hhhf")
    {
        double lambda_m = (0.25 + static_cast<double>(m) - 1) * M_PI;

        if (m == 2)
        {
            lambda_m = 3.926602;
        }
        else if (m == 3)
        {
            lambda_m = 7.068582;
        }
        else if (m == 4)
        {
            lambda_m = 10.21018;
        }
        double alpha = lambda_m / a_;

        if (m > 1)
        {
            return std::sin(alpha * x) + std::sinh(alpha * x) * std::sin(lambda_m) / std::sinh(lambda_m);
        }
        else
        {
            return x / a_;
        }
    }
    else
    {
        return 0.0;
    }
}

double NumericFunctions::function_1x(double x, int m)
{
    if (support_ == "hhhh")
    {
        return std::cos(x * M_PI / a_ * m) * M_PI / a_ * m;
    }
    else if (support_ == "cccc")
    {
        return 2 * M_PI * m * std::sin(2 * M_PI * m * x / a_) / a_;
    }
    else if (support_ == "hhff")
    {
        double lambda_m = (0.50 + static_cast<double>(m) - 1) * M_PI;
        if (m == 2)
        {
            lambda_m = 4.730041;
        }
        else if (m == 3)
        {
            lambda_m = 7.853205;
        }
        else if (m == 4)
        {
            lambda_m = 10.99561;
        }

        double alpha = lambda_m / a_;

        double a_j = (std::sinh(lambda_m) - std::sin(lambda_m)) / (std::cosh(lambda_m) - std::cos(lambda_m));

        if (m > 1)
        {
            return alpha * ((std::cos(alpha * x) + std::cosh(alpha * x)) 
            / (std::sin(lambda_m) - std::sinh(lambda_m)) - a_j * (std::sinh(alpha * x) - std::sin(alpha * x))) 
            / (std::cos(lambda_m) - std::cosh(lambda_m));
        }

        else
        {
            return 0;
        }
    }
    else if (support_ == "hhhf")
    {
        double lambda_m = (0.25 + static_cast<double>(m) - 1) * M_PI;

        if (m == 2)
        {
            lambda_m = 3.926602;
        }
        else if (m == 3)
        {
            lambda_m = 7.068582;
        }
        else if (m == 4)
        {
            lambda_m = 10.21018;
        }
        double alpha = lambda_m / a_;
        if (m > 1)
        {
            return alpha * (std::cos(alpha * x) + std::cosh(alpha * x) * std::sin(lambda_m) / std::sinh(lambda_m));
        }
        else
        {
            return 1 / a_;
        }
    }
    else
    {
        return 0.0;
    }
}

double NumericFunctions::function_1xx(double x, int m)
{
    if (support_ == "hhhh")
    {
        return -std::sin(x * M_PI / a_ * m) * std::pow(M_PI / a_ * m, 2);
    }
    else if (support_ == "cccc")
    {
        return 4 * std::pow(M_PI, 2) * std::pow(m, 2) * std::cos(2 * M_PI * m * x / a_) / std::pow(a_, 2);
    }
    else if (support_ == "hhff")
    {
        double lambda_m = (0.50 + static_cast<double>(m) - 1) * M_PI;
        if (m == 2)
        {
            lambda_m = 4.730041;
        }
        else if (m == 3)
        {
            lambda_m = 7.853205;
        }
        else if (m == 4)
        {
            lambda_m = 10.99561;
        }

        double alpha = lambda_m / a_;

        double a_j = (std::sinh(lambda_m) - std::sin(lambda_m)) / (std::cosh(lambda_m) - std::cos(lambda_m));

        if (m > 1)
        {
            return (alpha * alpha) * ((-std::sin(alpha * x) + std::sinh(alpha * x)
             / (std::sin(lambda_m) - std::sinh(lambda_m))) - a_j * (- std::cos(alpha * x)+ std::cosh(alpha * x) 
             ) / ((std::cos(lambda_m) - std::cosh(lambda_m))));
        }
        else
        {
            return 0;
        }
    }
    else if (support_ == "hhhf")
    {
        double lambda_m = (0.25 + static_cast<double>(m) - 1) * M_PI;

        if (m == 2)
        {
            lambda_m = 3.926602;
        }
        else if (m == 3)
        {
            lambda_m = 7.068582;
        }
        else if (m == 4)
        {
            lambda_m = 10.21018;
        }
        double alpha = lambda_m / a_;
        if (m > 1)
        {
            return alpha * alpha * (-1 * std::sin(alpha * x) + std::sinh(alpha * x) * std::sin(lambda_m) / std::sinh(lambda_m));
        }

        else
        {
            return 0;
        }
    }
    else
    {
        return 0.0;
    }
}

double NumericFunctions::function_2(double y, int n)
{
    if (support_ == "hhhh")
    {
        return std::sin(y * M_PI / b_ * n);
    }
    else if (support_ == "cccc")
    {
        return 1 - std::cos(2 * n * M_PI * y / b_);
    }
    else if (support_ == "hhff")
    {
        return std::sin(y * M_PI / b_ * n);
    }
    else if (support_ == "hhhf")
    {
        return std::sin(y * M_PI / b_ * n);
    }
    else
    {
        return 0.0;
    }
}

double NumericFunctions::function_2y(double y, int n)
{
    if (support_ == "hhhh")
    {
        return std::cos(y * M_PI / b_ * n) * M_PI / b_ * n;
    }
    else if (support_ == "cccc")
    {
        return 2 * M_PI * n * std::sin(2 * M_PI * n * y / b_) / b_;
    }
    else if (support_ == "hhff")
    {
        return std::cos(y * M_PI / b_ * n) * M_PI / b_ * n;
    }
    else if (support_ == "hhhf")
    {
        return std::cos(y * M_PI / b_ * n) * M_PI / b_ * n;
    }
    else
    {
        return 0.0;
    }
}

double NumericFunctions::function_2yy(double y, int n)
{
    if (support_ == "hhhh")
    {
        return -std::sin(y * M_PI / b_ * n) * std::pow(M_PI / b_ * n, 2);
    }
    else if (support_ == "cccc")
    {
        return 4 * std::pow(M_PI, 2) * std::pow(n, 2) * std::cos(2 * M_PI * n * y / b_) / std::pow(b_, 2);
    }
    else if (support_ == "hhff")
    {
        return -std::sin(y * M_PI / b_ * n) * std::pow(M_PI / b_ * n, 2);
    }
    else if (support_ == "hhhf")
    {
        return -std::sin(y * M_PI / b_ * n) * std::pow(M_PI / b_ * n, 2);
    }
    else
    {
        return 0.0;
    }
}

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
