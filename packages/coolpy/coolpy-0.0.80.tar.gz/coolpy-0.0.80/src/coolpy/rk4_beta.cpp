#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <vector>

namespace py = pybind11;

/*
 Ultra-fast RK4 solver for the beta-function system

   beta'   = beta_p
   beta_p' = (beta_p^2 + 4(1 + L^2) - 4 beta^2 kappa^2) / (2 beta)
*/
py::array_t<double> solve_beta_rk4(
    py::array_t<double, py::array::c_style | py::array::forcecast> s,
    py::array_t<double, py::array::c_style | py::array::forcecast> kappa,
    double beta0,
    double betap0,
    double L
) {
    if (s.ndim() != 1 || kappa.ndim() != 1)
        throw std::runtime_error("s and kappa must be 1D arrays");

    if (s.shape(0) != kappa.shape(0))
        throw std::runtime_error("s and kappa must have same length");

    const py::ssize_t N = s.shape(0);

    auto sr = s.unchecked<1>();
    auto kr = kappa.unchecked<1>();

    // shape: (N, 2)
    py::array_t<double> out(
        std::vector<py::ssize_t>{N, static_cast<py::ssize_t>(2)}
    );
    auto Y = out.mutable_unchecked<2>();

    double b  = beta0;
    double bp = betap0;
    const double L2 = L * L;

    Y(0, 0) = b;
    Y(0, 1) = bp;

    for (py::ssize_t i = 0; i < N - 1; ++i) {
        const double h = sr(i + 1) - sr(i);
        const double k = kr(i);

        // k1
        const double k1_b  = bp;
        const double k1_bp =
            (bp * bp + 4.0 * (1.0 + L2) - 4.0 * b * b * k * k) / (2.0 * b);

        // k2
        const double b2  = b  + 0.5 * h * k1_b;
        const double bp2 = bp + 0.5 * h * k1_bp;
        const double k2_b  = bp2;
        const double k2_bp =
            (bp2 * bp2 + 4.0 * (1.0 + L2) - 4.0 * b2 * b2 * k * k) / (2.0 * b2);

        // k3
        const double b3  = b  + 0.5 * h * k2_b;
        const double bp3 = bp + 0.5 * h * k2_bp;
        const double k3_b  = bp3;
        const double k3_bp =
            (bp3 * bp3 + 4.0 * (1.0 + L2) - 4.0 * b3 * b3 * k * k) / (2.0 * b3);

        // k4
        const double b4  = b  + h * k3_b;
        const double bp4 = bp + h * k3_bp;
        const double k4_b  = bp4;
        const double k4_bp =
            (bp4 * bp4 + 4.0 * (1.0 + L2) - 4.0 * b4 * b4 * k * k) / (2.0 * b4);

        b  += (h / 6.0) * (k1_b  + 2.0 * k2_b  + 2.0 * k3_b  + k4_b);
        bp += (h / 6.0) * (k1_bp + 2.0 * k2_bp + 2.0 * k3_bp + k4_bp);

        Y(i + 1, 0) = b;
        Y(i + 1, 1) = bp;
    }

    return out;
}

/* ---------------- pybind11 binder ---------------- */

void bind_rk4(py::module_ &m) {
    m.def(
        "solve_beta_rk4",
        &solve_beta_rk4,
        py::arg("s"),
        py::arg("kappa"),
        py::arg("beta0"),
        py::arg("betap0"),
        py::arg("L"),
        "Ultra-fast RK4 solver for the beta-function ODE"
    );
}
