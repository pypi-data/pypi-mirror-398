#include "window.h"

#include <windows.h>

#include "../core/exceptions/window_does_not_valid.h"
#include "../core/geometry/point.h"
#include "../core/geometry/size.h"

namespace appwindows::windows {

WindowWindows::WindowWindows(const std::shared_ptr<HWND>& window)
    : window_(window) {}

void WindowWindows::set_fullscreen(const bool is_fullscreen) {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  ShowWindow(*window_, is_fullscreen ? SW_MAXIMIZE : SW_RESTORE);
}

void WindowWindows::resize(const core::Size size) {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  RECT rect;
  GetWindowRect(*window_, &rect);
  SetWindowPos(*window_, nullptr, rect.left, rect.top, size.get_width(),
               size.get_height(), SWP_NOZORDER | SWP_NOACTIVATE);
}

void WindowWindows::move(const core::Point point) {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  const std::unique_ptr<core::Size> size = get_size();
  SetWindowPos(*window_, nullptr, point.get_x(), point.get_y(),
               size->get_width(), size->get_height(),
               SWP_NOZORDER | SWP_NOSIZE | SWP_NOACTIVATE);
}

void WindowWindows::close() {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  PostMessage(*window_, WM_CLOSE, 0, 0);
}

void WindowWindows::to_background() {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  SetWindowPos(*window_, HWND_BOTTOM, 0, 0, 0, 0,
               SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE);
}

void WindowWindows::to_foreground() {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  set_minimize(false);
  SetForegroundWindow(*window_);
  SetActiveWindow(*window_);
  SetWindowPos(*window_, HWND_TOP, 0, 0, 0, 0,
               SWP_NOSIZE | SWP_NOMOVE | SWP_SHOWWINDOW);
}

void WindowWindows::set_minimize(const bool is_minimize) {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  ShowWindow(*window_, is_minimize ? SW_MINIMIZE : SW_RESTORE);
}

}  // namespace appwindows::windows