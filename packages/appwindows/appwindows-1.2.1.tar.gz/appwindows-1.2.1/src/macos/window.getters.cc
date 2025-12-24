#include "window.h"

#include <ApplicationServices/ApplicationServices.h>

#include <memory>

#include "../core/exceptions/window_does_not_valid.h"
#include "../core/geometry/point.h"
#include "../core/geometry/quad_points.h"
#include "../core/geometry/size.h"

namespace appwindows::macos {

WindowMacOS::WindowMacOS(CGWindowID window_id) : window_id_(window_id) {}

std::unique_ptr<core::QuadPoints> WindowMacOS::get_points() {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  CFArrayRef window_list = CGWindowListCopyWindowInfo(
      kCGWindowListOptionIncludingWindow, window_id_);
  if (CFArrayGetCount(window_list) == 0) {
    CFRelease(window_list);
    throw core::exceptions::WindowDoesNotValidException();
  }
  CFDictionaryRef window_info =
      reinterpret_cast<CFDictionaryRef>(CFArrayGetValueAtIndex(window_list, 0));
  CFDictionaryRef bounds_ref = reinterpret_cast<CFDictionaryRef>(
      CFDictionaryGetValue(window_info, kCGWindowBounds));
  CGRect bounds;
  CGRectMakeWithDictionaryRepresentation(bounds_ref, &bounds);
  CFRelease(window_list);
  core::Point left_top(bounds.origin.x, bounds.origin.y);
  core::Point right_top(bounds.origin.x + bounds.size.width, bounds.origin.y);
  core::Point right_bottom(bounds.origin.x + bounds.size.width,
                           bounds.origin.y + bounds.size.height);
  core::Point left_bottom(bounds.origin.x,
                          bounds.origin.y + bounds.size.height);

  return std::make_unique<core::QuadPoints>(left_top, right_top, right_bottom,
                                            left_bottom);
}

std::unique_ptr<std::string> WindowMacOS::get_title() const {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  CFArrayRef window_list = CGWindowListCopyWindowInfo(
      kCGWindowListOptionIncludingWindow, window_id_);
  if (CFArrayGetCount(window_list) == 0) {
    CFRelease(window_list);
    throw core::exceptions::WindowDoesNotValidException();
  }
  CFDictionaryRef window_info =
      reinterpret_cast<CFDictionaryRef>(CFArrayGetValueAtIndex(window_list, 0));
  CFStringRef title_ref = reinterpret_cast<CFStringRef>(
      CFDictionaryGetValue(window_info, kCGWindowName));
  std::string title;
  if (title_ref) {
    const char* title_cstr =
        CFStringGetCStringPtr(title_ref, kCFStringEncodingUTF8);
    if (title_cstr) {
      title = title_cstr;
    } else {
      char buffer[256];
      if (CFStringGetCString(title_ref, buffer, sizeof(buffer),
                             kCFStringEncodingUTF8))  title = buffer;
    }
  }
  CFRelease(window_list);
  return std::make_unique<std::string>(title);
}

std::unique_ptr<core::Size> WindowMacOS::get_size() const {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  CFArrayRef window_list = CGWindowListCopyWindowInfo(
      kCGWindowListOptionIncludingWindow, window_id_);
  if (CFArrayGetCount(window_list) == 0) {
    CFRelease(window_list);
    throw core::exceptions::WindowDoesNotValidException();
  }
  CFDictionaryRef window_info =
      reinterpret_cast<CFDictionaryRef>(CFArrayGetValueAtIndex(window_list, 0));
  CFDictionaryRef bounds_ref = reinterpret_cast<CFDictionaryRef>(
      CFDictionaryGetValue(window_info, kCGWindowBounds));

  CGRect bounds;
  CGRectMakeWithDictionaryRepresentation(bounds_ref, &bounds);
  CFRelease(window_list);
  return std::make_unique<core::Size>(bounds.size.width, bounds.size.height);
}

py::array_t<unsigned char> WindowMacOS::get_screenshot() {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  CGImageRef screenshot =
      CGWindowListCreateImage(CGRectNull, kCGWindowListOptionIncludingWindow,
                              window_id_, kCGWindowImageBoundsIgnoreFraming);
  size_t width = CGImageGetWidth(screenshot);
  size_t height = CGImageGetHeight(screenshot);
  size_t bytes_per_row = CGImageGetBytesPerRow(screenshot);
  CFDataRef data_ref =
      CGDataProviderCopyData(CGImageGetDataProvider(screenshot));
  const unsigned char* data = CFDataGetBytePtr(data_ref);
  auto result = py::array_t<unsigned char>(
      {static_cast<py::ssize_t>(height), static_cast<py::ssize_t>(width), 4});
  auto buf = result.mutable_data();
  for (size_t y = 0; y < height; ++y) {
    for (size_t x = 0; x < width; ++x) {
      size_t src_index = y * bytes_per_row + x * 4;
      size_t dst_index = (y * width + x) * 4;
      buf[dst_index + 0] = data[src_index + 2];
      buf[dst_index + 1] = data[src_index + 1];
      buf[dst_index + 2] = data[src_index + 0];
      buf[dst_index + 3] = data[src_index + 3];
    }
  }
  CFRelease(data_ref);
  CGImageRelease(screenshot);
  return result;
}

std::unique_ptr<int> WindowMacOS::get_process_id() const {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  CFArrayRef window_list = CGWindowListCopyWindowInfo(
      kCGWindowListOptionIncludingWindow, window_id_);
  if (CFArrayGetCount(window_list) == 0) {
    CFRelease(window_list);
    throw core::exceptions::WindowDoesNotValidException();
  }
  CFDictionaryRef window_info =
      reinterpret_cast<CFDictionaryRef>(CFArrayGetValueAtIndex(window_list, 0));
  CFNumberRef pid_ref = reinterpret_cast<CFNumberRef>(
      CFDictionaryGetValue(window_info, kCGWindowOwnerPID));
  int pid;
  CFNumberGetValue(pid_ref, kCFNumberIntType, &pid);
  CFRelease(window_list);
  return std::make_unique<int>(pid);
}

std::unique_ptr<bool> WindowMacOS::is_valid() const {
  CFArrayRef window_list = CGWindowListCopyWindowInfo(
      kCGWindowListOptionIncludingWindow, window_id_);
  bool valid = CFArrayGetCount(window_list) > 0;
  CFRelease(window_list);
  return std::make_unique<bool>(valid);
}

}  // namespace appwindows::macos