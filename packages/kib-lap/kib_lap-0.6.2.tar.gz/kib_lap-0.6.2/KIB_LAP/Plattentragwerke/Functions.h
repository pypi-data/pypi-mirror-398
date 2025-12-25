// Functions.h

#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#include <string>

class NumericFunctions
{
public:
    NumericFunctions(double a, double b, const std::string &support);
    NumericFunctions() {};

    double function_1(double x, int m);
    double function_1x(double x, int m);
    double function_1xx(double x, int m);
    double function_2(double y, int n);
    double function_2y(double y, int n);
    double function_2yy(double y, int n);

private:
    double a_;
    double b_;
    std::string support_;
};

#include <vector>
#include <functional>

class NumericalIntegration
{
public:
    static double integrate_product(
        const std::function<double(double, int)> &func1,
        const std::function<double(double, int)> &func2,
        const std::vector<double> &points,
        int index1,
        int index2);
};

#endif // FUNCTIONS_H
