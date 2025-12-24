#include "bind_geometry.h"

#include <pybind11/pybind11.h>

#include "point.h"
#include "size.h"
#include "quad_points.h"

namespace py = pybind11;

namespace appwindows::core::geometry {

void bind_geometry(py::module &m){
  py::class_<appwindows::core::Point>(
      m, "Point", "Represents a 2D point with x and y coordinates")
      .def(py::init<int, int>(),
           "Create a point with specified coordinates\n\n"
           "Args:\n"
           "    x (int): X coordinate\n"
           "    y (int): Y coordinate",
           py::arg("x"), py::arg("y"))
      .def("__add__", &appwindows::core::Point::operator+, "Add two points")
      .def("__sub__", &appwindows::core::Point::operator-,
           "Subtract two points")
      .def("__mul__", &appwindows::core::Point::operator*,
           "Multiply two points")
      .def("__truediv__", &appwindows::core::Point::operator/,
           "Divide two points")
      .def("__eq__", &appwindows::core::Point::operator==,
           "Points is equal")
      .def_property_readonly("x", &appwindows::core::Point::get_x,
                             "X coordinate")
      .def_property_readonly("y", &appwindows::core::Point::get_y,
                             "Y coordinate");

  py::class_<appwindows::core::Size>(
      m, "Size", "Represents dimensions with width and height")
      .def(py::init<int, int>(),
           "Create size with specified dimensions\n\n"
           "Args:\n"
           "    width (int): Width dimension\n"
           "    height (int): Height dimension\n\n"
           "Raises:\n"
           "    InvalidSizeError: If width or height are invalid",
           py::arg("width"), py::arg("height"))
      .def_property_readonly("width", &appwindows::core::Size::get_width,
                             "Width dimension")
      .def_property_readonly("height", &appwindows::core::Size::get_height,
                             "Height dimension");

  py::class_<appwindows::core::QuadPoints>(
      m, "QuadPoints", "Vertices of a quadrilateral")
      .def(py::init<Point, Point, Point, Point>(),
           "QuadPoints constructor\n\n"
           "Args:\n"
           "    left_top (appwindows.geometry.Point): left top point\n"
           "    right_top (appwindows.geometry.Point): right top point\n"
           "    right_bottom (appwindows.geometry.Point): right bottom point\n"
           "    left_bottom (appwindows.geometry.Point): left bottom point",
           py::arg("left_top"), py::arg("right_top"), py::arg("right_bottom"), py::arg("left_bottom"))
      .def_property_readonly("left_top", &appwindows::core::QuadPoints::get_left_top,
                             "Left top point")
      .def_property_readonly("right_top", &appwindows::core::QuadPoints::get_right_top,
                             "Right top point")
      .def_property_readonly("right_bottom", &appwindows::core::QuadPoints::get_right_bottom,
                             "Right bottom point")
      .def_property_readonly("left_bottom", &appwindows::core::QuadPoints::get_left_bottom,
                             "Left bottom point");
}

}  // namespace appwindows::core::geometry