#include "bind.h"

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "base_finder.h"
#include "base_window.h"
#include "./exceptions/window_does_not_valid.h"

namespace py = pybind11;

namespace appwindows::core {

void bind_window(py::module &m) {
  py::class_<Window, std::shared_ptr<Window>>(
      m, "Window", "Interface representing an application window")
      .def(
          "get_points",
          [](Window &self) {
            auto points = self.get_points();
            return points ? *points : throw exceptions::WindowDoesNotValidException();
          },
          "Get all points associated with the window\n\n"
          "Returns:\n"
          "    appwindows.geometry.QuadPoints: QuadPoints object with all points\n\n"
          "Raises:\n"
          "    appwindows.exceptions.WindowDoesNotValidException: If window is invalid")
      .def(
          "get_title",
          [](const Window &self) {
            const auto title = self.get_title();
            return title ? *title : throw exceptions::WindowDoesNotValidException();
          },
          "Get the window title\n\n"
          "Returns:\n"
          "    str: Window title\n\n"
          "Raises:\n"
          "    appwindows.exceptions.WindowDoesNotValidException: If window is invalid")
      .def(
          "get_process_id",
          [](const Window &self) {
            const auto process_id = self.get_process_id();
            return process_id ? *process_id : throw exceptions::WindowDoesNotValidException();
          },
          "Get the window process id\n\n"
          "Returns:\n"
          "    int: process id\n\n"
          "Raises:\n"
          "    appwindows.exceptions.WindowDoesNotValidException: If window is invalid")
      .def(
          "is_valid", [](const Window &self) { return *self.is_valid(); },
          "Is window valid\n\n"
          "Returns:\n"
          "    bool: is valid\n\n"
          "Raises:\n"
          "    appwindows.exceptions.WindowDoesNotValidException: If window is invalid")
      .def(
          "get_size",
          [](const Window &self) {
            auto size = self.get_size();
            return size ? *size : throw exceptions::WindowDoesNotValidException();
          },
          "Get current window size\n\n"
          "Returns:\n"
          "    Size: Current window dimensions\n\n"
          "Raises:\n"
          "    appwindows.exceptions.WindowDoesNotValidException: If window is invalid")
      .def(
          "get_screenshot", [](Window &self) { return self.get_screenshot(); },
          "Get current window image\n\n"
          "Returns:\n"
          "    ndarray: image in ndarray\n\n"
          "Raises:\n"
          "    appwindows.exceptions.WindowDoesNotValidException: If window is invalid")
      .def("to_foreground", &Window::to_foreground,
           "Moved window to foreground\n\n"
           "Raises:\n"
           "    appwindows.exceptions.WindowDoesNotValidException: If window is invalid")
      .def("to_background", &Window::to_background,
           "Moved window to background\n\n"
           "Raises:\n"
           "    appwindows.exceptions.WindowDoesNotValidException: If window is invalid")
      .def("set_minimize", &Window::set_minimize,
           "Set window active state\n\n"
           "Args:\n"
           "    is_minimize (bool): True to activate window\n\n"
           "Raises:\n"
          "    appwindows.exceptions.WindowDoesNotValidException: If window is invalid",
           py::arg("is_minimize"))
      .def("set_fullscreen", &Window::set_fullscreen,
           "Maximize or restore the window\n\n"
           "Args:\n"
           "    is_fullscreen (bool): True to window on fullscreen\n\n"
           "Raises:\n"
          "    appwindows.exceptions.WindowDoesNotValidException: If window is invalid",
           py::arg("is_maximize"))
      .def("resize", &Window::resize,
           "Resize the window\n\n"
           "Args:\n"
           "    size (appwindows.geometry.Size): New window dimensions\n\n"
           "Raises:\n"
           "    appwindows.exceptions.InvalidSizeError: If size is invalid"
           "    appwindows.exceptions.WindowDoesNotValidException: If window is invalid",
           py::arg("size"))
      .def("move", &Window::move,
           "Move window to specified position\n\n"
           "Args:\n"
           "    point (appwindows.geometry.Point): New window position\n\n"
          "Raises:\n"
          "    appwindows.exceptions.WindowDoesNotValidException: If window is invalid",
           py::arg("point"))
      .def("close", &Window::close, "Close the window");
}

void bind_finder(py::module &m) {
  py::class_<Finder, std::shared_ptr<Finder>>(
      m, "Finder", "Interface for finding application windows")
      .def(
          "get_window_by_title",
          [](const Finder &self, const std::string &title) {
            return self.get_window_by_title(title);
          },
          "Find window by its title substring\n\n"
          "Args:\n"
          "    title (str): Window title to search for\n\n"
          "Returns:\n"
          "    Window: Found window\n\n"
          "Raises:\n"
          "    appwindows.exceptions.WindowDoesNotFoundxception: If window is not found",
          py::arg("title"))
      .def(
          "get_window_by_process_id",
          [](const Finder &self, const int process_id) {
            return self.get_window_by_process_id(process_id);
          },
          "Find window by process id\n\n"
          "Args:\n"
          "    process_id (int): Window title to search for\n\n"
          "Returns:\n"
          "    Window | None: Found window or null if window does not exist\n\n"
          "Raises:\n"
          "    appwindows.exceptions.WindowDoesNotFoundxception: If window is not found",
          py::arg("process_id"))
      .def(
          "get_all_windows",
          [](const Finder &self) { return self.get_all_windows(); },
          "Find all opened windows\n\n"
          "Returns:\n"
          "    list[Window]: Found windows\n\n")
      .def(
          "get_all_titles",
          [](const Finder &self) { return self.get_all_titles(); },
          "Get all window titles\n\n"
          "Returns:\n"
          "    list[str]: Found titles\n\n")
      .def(
          "get_os",
          [](const Finder &self) { return *self.get_os(); },
          "Get os and graphical shell\n\n"
          "Returns:\n"
          "    str: your <<os>>::<<graphical shell>>\n\n");
}

}  // namespace appwindows::core