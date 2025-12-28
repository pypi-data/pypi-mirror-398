//#include <pybind11/pybind11.h>
//
//namespace py = pybind11;
//
//double multiply(double a, double b) {
//    return a * b;
//}
//
//PYBIND11_MODULE(_mymath, m) {
//    m.doc() = "coolpy C++ math kernels";
//    m.def("multiply", &multiply, "Multiply two numbers and return a double");
//}

#include <pybind11/pybind11.h>

namespace py = pybind11;

// forward declarations
void bind_rk4(py::module_ &);
void bind_nelder_mead(py::module_ &);

PYBIND11_MODULE(_mymath, m) {
    m.doc() = "coolpy C++ acceleration module";

    bind_rk4(m);
    bind_nelder_mead(m);
}
