#ifndef FRECHET_H
#define FRECHET_H

#include <vector>
#include <functional>

using double_vec_1d = std::vector<double>;
using double_vec_2d = std::vector<std::vector<double>>;
using distanceFunction = std::function<double(const double_vec_1d& point_a, const double_vec_1d& point_b)>;

double computeEuclideanDistance(const double_vec_1d &point_a, const double_vec_1d &point_b);
double computeCurveFrechet(const double_vec_2d& curve_a, const double_vec_2d& curve_b, const distanceFunction &d = computeEuclideanDistance);
double computeLoopFrechet(const double_vec_2d& curve_a, const double_vec_2d& curve_b, const distanceFunction &d = computeEuclideanDistance);

#endif
