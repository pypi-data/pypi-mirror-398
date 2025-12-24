#pragma once

#include <pybind11/pybind11.h>

namespace py = pybind11;

namespace appwindows::core::exceptions {

void bind_exceptions(py::module &m);

}  // namespace appwindows::core::geometry