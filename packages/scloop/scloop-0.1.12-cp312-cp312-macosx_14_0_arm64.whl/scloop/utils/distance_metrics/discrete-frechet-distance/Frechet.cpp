#include "Frechet.h"
#include <algorithm>
#include <cmath>
#include <limits>

// this appears to be preferred in c++ instead of INFINITY?
static constexpr double inf = std::numeric_limits<double>::infinity();
using free_space_diagram = double_vec_2d;

// compute euclidean distance between two vectors
double computeEuclideanDistance(const double_vec_1d &point_a,
                                const double_vec_1d &point_b) {
  if (point_a.size() != point_b.size()) {
    return inf;
  }
  double ss = 0;
  for (size_t i = 0; i < point_a.size(); ++i) {
    double diff = point_a[i] - point_b[i];
    ss += diff * diff;
  }
  return std::sqrt(ss);
}

/*
Entry ij is -1 if it is an uncomputed coupling between point i and point j
Entry ij is a nonnegative value if it is computed and will be reused in
recursion
*/
free_space_diagram newFreeSpace(int p, int q) {
  return free_space_diagram(p, double_vec_1d(q, -1.0));
}

/*
Recursive helper function for computing Frechet distace
Based on the article Computing Discrete Frechet Distance, Thomas Eiter and
Heikki Mannila, 1994
*/
double updateFreeSpace(free_space_diagram &fsd, const double_vec_2d &curve_a,
                       const double_vec_2d &curve_b, int i, int j,
                       const distanceFunction &d) {
  if (fsd[i][j] > -1) {
    return fsd[i][j];
  } else if (i == 0 && j == 0) {
    fsd[i][j] = d(curve_a[i], curve_b[j]);
  } else if (i > 0 && j == 0) {
    fsd[i][j] = std::max(updateFreeSpace(fsd, curve_a, curve_b, i - 1, j, d),
                         d(curve_a[i], curve_b[j]));
  } else if (i == 0 && j > 0) {
    fsd[i][j] = std::max(updateFreeSpace(fsd, curve_a, curve_b, i, j - 1, d),
                         d(curve_a[i], curve_b[j]));
  } else if (i > 0 && j > 0) {
    fsd[i][j] = std::max(
        std::min({updateFreeSpace(fsd, curve_a, curve_b, i - 1, j, d),
                  updateFreeSpace(fsd, curve_a, curve_b, i - 1, j - 1, d),
                  updateFreeSpace(fsd, curve_a, curve_b, i, j - 1, d)}),
        d(curve_a[i], curve_b[j]));
  } else {
    fsd[i][j] = inf;
  }
  return fsd[i][j];
}

/*
TODO: non-recursive version of updateFreeSpace
*/

/*
Based on the article Computing Discrete Frechet Distance, Thomas Eiter and
Heikki Mannila, 1994
*/
double computeCurveFrechet(const double_vec_2d &curve_a,
                           const double_vec_2d &curve_b,
                           const distanceFunction &d) {
  size_t p = curve_a.size();
  size_t q = curve_b.size();
  if (p == 0 || q == 0) {
    return -1.0;
  }
  free_space_diagram fsd = newFreeSpace(p, q);
  return updateFreeSpace(fsd, curve_a, curve_b, p - 1, q - 1, d);
}

/*
This function needs to consider different start&end points as the start&end for
loops can be any points.
Also, need to consider different orders.
*/
double computeLoopFrechet(const double_vec_2d &curve_a,
                          const double_vec_2d &curve_b,
                          const distanceFunction &d) {
  size_t p = curve_a.size();
  size_t q = curve_b.size();
  if (p == 0 || q == 0) {
    return -1.0;
  }
  double min_frechet_distance = inf;
  double_vec_2d curve_a_reordered(p);

  for (int i = 0; i < p; ++i) {
    // Forward direction
    std::rotate_copy(curve_a.begin(), curve_a.begin() + i, curve_a.end(),
                     curve_a_reordered.begin());
    double frechet_distance_inorder =
        computeCurveFrechet(curve_a_reordered, curve_b, d);

    if (frechet_distance_inorder >= 0) {
      min_frechet_distance =
          std::min(min_frechet_distance, frechet_distance_inorder);
    }

    // Reverse direction
    std::reverse(curve_a_reordered.begin(), curve_a_reordered.end());
    double frechet_distance_revorder =
        computeCurveFrechet(curve_a_reordered, curve_b, d);

    if (frechet_distance_revorder >= 0) {
      min_frechet_distance =
          std::min(min_frechet_distance, frechet_distance_revorder);
    }
  }

  return (min_frechet_distance == inf) ? -1.0 : min_frechet_distance;
}

// -----
// Goals
// -----
/*
1. discrete frechet distance for curves
2. discrete frechet distance for loops
3. python wrapper
4. handle groups of curves
*/
