#include "window.h"

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xatom.h>

#include <pybind11/numpy.h>

#include <memory>
#include <string>
#include <vector>

#include "../core/exceptions/window_does_not_valid.h"
#include "finder.h"

namespace py = pybind11;

namespace appwindows::x_server {

std::unique_ptr<bool> WindowXServer::is_valid() const {
  auto display = FinderXServer::open_display();
  static bool is_valid = true;
  auto old_error_handler =
      XSetErrorHandler([](Display* display, XErrorEvent* error) {
        if (error->error_code == BadWindow) is_valid = false;
        return 0;
      });
  XWindowAttributes attrs;
  XGetWindowAttributes(display, window_, &attrs);
  XSetErrorHandler(old_error_handler);
  XCloseDisplay(display);
  return std::make_unique<bool>(is_valid);
}

std::unique_ptr<core::QuadPoints> WindowXServer::get_points() {
  XWindowAttributes attrs;
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  auto display = FinderXServer::open_display();
  if (!XGetWindowAttributes(display, window_, &attrs)) return nullptr;
  auto points = std::make_unique<core::QuadPoints>(core::Point{attrs.x, attrs.y},
                                                   core::Point{attrs.x + attrs.width, attrs.y},
                                                   core::Point{attrs.x + attrs.width, attrs.y + attrs.height},
                                                   core::Point{attrs.x, attrs.y + attrs.height});
  XCloseDisplay(display);
  return points;
}

std::unique_ptr<core::Size> WindowXServer::get_size() const {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  auto display = FinderXServer::open_display();
  XWindowAttributes attrs;
  if (!XGetWindowAttributes(display, window_, &attrs)) return nullptr;
  XCloseDisplay(display);
  return std::make_unique<core::Size>(attrs.width, attrs.height);
}

std::unique_ptr<std::string> WindowXServer::get_title() const {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  auto display = FinderXServer::open_display();
  Atom utf8_string = XInternAtom(display, "UTF8_STRING", False);
  Atom net_wm_name = XInternAtom(display, "_NET_WM_NAME", False);
  Atom actual_type;
  int actual_format;
  unsigned long nitems, bytes_after;
  unsigned char* data = nullptr;
  XGetWindowProperty(display, window_, net_wm_name, 0, (~0L), False,
                     utf8_string, &actual_type, &actual_format, &nitems,
                     &bytes_after, &data) == Success&& data;
  std::string title(reinterpret_cast<char*>(data), nitems);
  XFree(data);
  XCloseDisplay(display);
  return std::make_unique<std::string>(title);
}

py::array_t<unsigned char> WindowXServer::get_screenshot() {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  auto display = FinderXServer::open_display();
  auto size = get_size();
  auto image = XGetImage(display, window_, 0, 0, size->get_width(),
                         size->get_height(), AllPlanes, ZPixmap);
  std::vector<size_t> shape = {static_cast<size_t>(size->get_height()),
                               static_cast<size_t>(size->get_width()), 3};
  py::array_t<unsigned char> result(shape);
  auto buf = result.mutable_unchecked<3>();
  for (int y = 0; y < size->get_height(); ++y)
    for (int x = 0; x < size->get_width(); ++x) {
      unsigned long pixel = XGetPixel(image, x, y);
      buf(y, x, 0) = (pixel >> 16) & 0xff;
      buf(y, x, 1) = (pixel >> 8) & 0xff;
      buf(y, x, 2) = pixel & 0xff;
    }
  XDestroyImage(image);
  XCloseDisplay(display);
  return result;
}

std::unique_ptr<int> WindowXServer::get_process_id() const {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  auto display = FinderXServer::open_display();
  Atom net_wm_pid = XInternAtom(display, "_NET_WM_PID", False);
  Atom actual_type;
  int actual_format;
  unsigned long nitems, bytes_after;
  unsigned long* pid = nullptr;
  int status =
      XGetWindowProperty(display, window_, net_wm_pid, 0, 1, False, XA_CARDINAL,
                         &actual_type, &actual_format, &nitems, &bytes_after,
                         reinterpret_cast<unsigned char**>(&pid));

  std::unique_ptr<int> result = nullptr;
  if (status == Success && actual_type == XA_CARDINAL && actual_format == 32 &&
      nitems == 1 && pid)
    result = std::make_unique<int>(static_cast<int>(*pid));
  if (pid) XFree(pid);
  XCloseDisplay(display);
  return result;
}

}  // namespace appwindows::x_server