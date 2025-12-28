#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <utility>
#include <vector>

namespace py = pybind11;

/* ---------------- utility helpers ---------------- */

static inline double clip(double v, double lo, double hi) {
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

static inline void apply_bounds(std::vector<double>& x,
                                const std::vector<double>& lb,
                                const std::vector<double>& ub) {
    if (lb.empty()) return;
    for (size_t i = 0; i < x.size(); ++i)
        x[i] = clip(x[i], lb[i], ub[i]);
}

static double eval_obj(py::function f,
                       const std::vector<double>& x,
                       const py::tuple& args) {
    py::array_t<double> x_np(x.size());
    auto xr = x_np.mutable_unchecked<1>();
    for (py::ssize_t i = 0; i < (py::ssize_t)x.size(); ++i)
        xr(i) = x[(size_t)i];

    py::object out = f(x_np, *args);
    return out.cast<double>();
}

/* ---------------- Nelder–Mead core ---------------- */

py::dict nelder_mead(
    py::function objective,
    py::array_t<double, py::array::c_style | py::array::forcecast> x0,
    py::tuple args,
    py::object bounds_obj,
    int max_iter,
    double tol_f,
    double tol_x,
    double initial_step,
    double alpha,
    double gamma,
    double rho,
    double sigma
) {
    if (x0.ndim() != 1)
        throw std::runtime_error("x0 must be 1D");

    const size_t n = (size_t)x0.shape(0);
    if (n == 0)
        throw std::runtime_error("x0 must not be empty");

    /* ---- bounds ---- */
    std::vector<double> lb, ub;
    if (!bounds_obj.is_none()) {
        py::sequence bounds = bounds_obj.cast<py::sequence>();
        if ((size_t)bounds.size() != n)
            throw std::runtime_error("bounds length mismatch");
        lb.resize(n);
        ub.resize(n);
        for (size_t i = 0; i < n; ++i) {
            py::sequence bi = bounds[i].cast<py::sequence>();
            lb[i] = bi[0].cast<double>();
            ub[i] = bi[1].cast<double>();
        }
    }

    /* ---- initial simplex ---- */
    std::vector<double> x_start(n);
    auto r0 = x0.unchecked<1>();
    for (size_t i = 0; i < n; ++i)
        x_start[i] = r0((py::ssize_t)i);
    apply_bounds(x_start, lb, ub);

    std::vector<std::vector<double>> simplex(n + 1, x_start);
    for (size_t i = 0; i < n; ++i) {
        simplex[i + 1][i] += initial_step;
        apply_bounds(simplex[i + 1], lb, ub);
    }

    std::vector<double> fvals(n + 1);
    int nfev = 0;
    for (size_t i = 0; i < n + 1; ++i) {
        fvals[i] = eval_obj(objective, simplex[i], args);
        ++nfev;
    }

    auto sort_simplex = [&]() {
        std::vector<size_t> idx(n + 1);
        for (size_t i = 0; i < n + 1; ++i) idx[i] = i;
        std::sort(idx.begin(), idx.end(),
                  [&](size_t a, size_t b){ return fvals[a] < fvals[b]; });

        std::vector<std::vector<double>> s2(n + 1);
        std::vector<double> f2(n + 1);
        for (size_t k = 0; k < n + 1; ++k) {
            s2[k] = std::move(simplex[idx[k]]);
            f2[k] = fvals[idx[k]];
        }
        simplex = std::move(s2);
        fvals   = std::move(f2);
    };

    sort_simplex();

    auto simplex_size = [&]() {
        double m = 0.0;
        for (size_t i = 1; i < n + 1; ++i)
            for (size_t j = 0; j < n; ++j)
                m = std::max(m, std::abs(simplex[i][j] - simplex[0][j]));
        return m;
    };

    auto f_spread = [&]() {
        double fmin = fvals[0], fmax = fvals[0];
        for (size_t i = 1; i < n + 1; ++i) {
            fmin = std::min(fmin, fvals[i]);
            fmax = std::max(fmax, fvals[i]);
        }
        return std::abs(fmax - fmin);
    };

    bool success = false;
    int nit = 0;

    for (; nit < max_iter; ++nit) {
        if (f_spread() < tol_f && simplex_size() < tol_x) {
            success = true;
            break;
        }

        std::vector<double> xc(n, 0.0);
        for (size_t i = 0; i < n; ++i)
            for (size_t j = 0; j < n; ++j)
                xc[j] += simplex[i][j];
        for (double &v : xc) v /= double(n);

        const auto &xw = simplex[n];

        std::vector<double> xr(n);
        for (size_t j = 0; j < n; ++j)
            xr[j] = xc[j] + alpha * (xc[j] - xw[j]);
        apply_bounds(xr, lb, ub);

        double fr = eval_obj(objective, xr, args); ++nfev;

        if (fr < fvals[0]) {
            std::vector<double> xe(n);
            for (size_t j = 0; j < n; ++j)
                xe[j] = xc[j] + gamma * (xr[j] - xc[j]);
            apply_bounds(xe, lb, ub);

            double fe = eval_obj(objective, xe, args); ++nfev;
            simplex[n] = (fe < fr) ? std::move(xe) : std::move(xr);
            fvals[n]   = std::min(fe, fr);
        }
        else if (fr < fvals[n - 1]) {
            simplex[n] = std::move(xr);
            fvals[n]   = fr;
        }
        else {
            std::vector<double> xcand(n);
            for (size_t j = 0; j < n; ++j)
                xcand[j] = xc[j] + rho * (xw[j] - xc[j]);
            apply_bounds(xcand, lb, ub);

            double fc = eval_obj(objective, xcand, args); ++nfev;
            if (fc < fvals[n]) {
                simplex[n] = std::move(xcand);
                fvals[n]   = fc;
            }
            else {
                const auto &xb = simplex[0];
                for (size_t i = 1; i < n + 1; ++i) {
                    for (size_t j = 0; j < n; ++j)
                        simplex[i][j] = xb[j] + sigma * (simplex[i][j] - xb[j]);
                    apply_bounds(simplex[i], lb, ub);
                    fvals[i] = eval_obj(objective, simplex[i], args);
                    ++nfev;
                }
            }
        }

        sort_simplex();
    }

    py::array_t<double> xbest(n);
    auto xb = xbest.mutable_unchecked<1>();
    for (size_t j = 0; j < n; ++j)
        xb((py::ssize_t)j) = simplex[0][j];

    py::dict res;
    res["x"] = xbest;
    res["fun"] = fvals[0];
    res["nit"] = nit;
    res["nfev"] = nfev;
    res["success"] = success;
    res["message"] = success ? "Converged" : "Max iterations reached";
    return res;
}

/* ---------------- pybind11 binder ---------------- */

void bind_nelder_mead(py::module_ &m) {
    m.def("nelder_mead", &nelder_mead,
          py::arg("objective"),
          py::arg("x0"),
          py::arg("args") = py::tuple(),
          py::arg("bounds") = py::none(),
          py::arg("max_iter") = 1000,
          py::arg("tol_f") = 1e-6,
          py::arg("tol_x") = 1e-6,
          py::arg("initial_step") = 1.0,
          py::arg("alpha") = 1.0,
          py::arg("gamma") = 2.0,
          py::arg("rho") = 0.5,
          py::arg("sigma") = 0.5);
}
