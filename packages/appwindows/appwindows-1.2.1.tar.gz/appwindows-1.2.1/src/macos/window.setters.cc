// window.setter.cc
#include "window.h"

#include <ApplicationServices/ApplicationServices.h>
#include <AXUIElement.h>

#include "../core/exceptions/window_does_not_valid.h"
#include "../core/geometry/point.h"
#include "../core/geometry/size.h"

namespace appwindows::macos {

void WindowMacOS::set_minimize(bool is_minimize) {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  auto pid = *get_process_id();
  AXUIElementRef app = AXUIElementCreateApplication(pid);
  CFArrayRef windows;
  AXUIElementCopyAttributeValues(app, kAXWindowsAttribute, 0, 100, &windows);
  if (windows && CFArrayGetCount(windows) > 0) {
    AXUIElementRef window = (AXUIElementRef)CFArrayGetValueAtIndex(windows, 0);
    CFStringRef minAttr = is_minimize ? kAXMinimizedAttribute : kAXNormalWindowAttribute;
    AXUIElementSetAttributeValue(window, minAttr, kCFBooleanTrue);
  }
  if (windows) CFRelease(windows);
  CFRelease(app);
}

void WindowMacOS::set_fullscreen(bool is_fullscreen) {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  auto pid = *get_process_id();
  AXUIElementRef app = AXUIElementCreateApplication(pid);
  CFArrayRef windows;
  AXUIElementCopyAttributeValues(app, kAXWindowsAttribute, 0, 100, &windows);
  if (windows && CFArrayGetCount(windows) > 0) {
    AXUIElementRef window = (AXUIElementRef)CFArrayGetValueAtIndex(windows, 0);
    CFBooleanRef fullscreenValue = is_fullscreen ? kCFBooleanTrue : kCFBooleanFalse;
    AXUIElementSetAttributeValue(window, kAXFullscreenAttribute, fullscreenValue);
  }
  if (windows) CFRelease(windows);
  CFRelease(app);
}

void WindowMacOS::resize(core::Size size) {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  auto pid = *get_process_id();
  AXUIElementRef app = AXUIElementCreateApplication(pid);
  CFArrayRef windows;
  AXUIElementCopyAttributeValues(app, kAXWindowsAttribute, 0, 100, &windows);
  if (windows && CFArrayGetCount(windows) > 0) {
    AXUIElementRef window = (AXUIElementRef)CFArrayGetValueAtIndex(windows, 0);
    CFTypeRef positionRef;
    AXUIElementCopyAttributeValue(window, kAXPositionAttribute, &positionRef);
    CGPoint newPoint = {0, 0};
    if (positionRef) {
      AXValueGetValue((AXValueRef)positionRef, kAXValueCGPointType, &newPoint);
      CFRelease(positionRef);
    }
    CGSize newSize = {static_cast<CGFloat>(size.get_width()), static_cast<CGFloat>(size.get_height())};
    AXValueRef sizeValue = AXValueCreate(kAXValueCGSizeType, &newSize);
    AXUIElementSetAttributeValue(window, kAXSizeAttribute, sizeValue);
    CFRelease(sizeValue);
  }
  if (windows) CFRelease(windows);
  CFRelease(app);
}

void WindowMacOS::move(core::Point point) {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  auto pid = *get_process_id();
  AXUIElementRef app = AXUIElementCreateApplication(pid);
  CFArrayRef windows;
  AXUIElementCopyAttributeValues(app, kAXWindowsAttribute, 0, 100, &windows);
  if (windows && CFArrayGetCount(windows) > 0) {
    AXUIElementRef window = (AXUIElementRef)CFArrayGetValueAtIndex(windows, 0);
    CGPoint newPoint = {static_cast<CGFloat>(point.get_x()), static_cast<CGFloat>(point.get_y())};
    AXValueRef pointValue = AXValueCreate(kAXValueCGPointType, &newPoint);
    AXUIElementSetAttributeValue(window, kAXPositionAttribute, pointValue);
    CFRelease(pointValue);
  }
  if (windows) CFRelease(windows);
  CFRelease(app);
}

void WindowMacOS::close() {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  auto pid = *get_process_id();
  AXUIElementRef app = AXUIElementCreateApplication(pid);
  CFArrayRef windows;
  AXUIElementCopyAttributeValues(app, kAXWindowsAttribute, 0, 100, &windows);
  if (windows && CFArrayGetCount(windows) > 0) {
    AXUIElementRef window = (AXUIElementRef)CFArrayGetValueAtIndex(windows, 0);
    AXUIElementPerformAction(window, kAXCloseAction);
  }
  if (windows) CFRelease(windows);
  CFRelease(app);
}

void WindowMacOS::to_foreground() {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  auto pid = *get_process_id();
  AXUIElementRef app = AXUIElementCreateApplication(pid);
  CFArrayRef windows;
  AXUIElementCopyAttributeValues(app, kAXWindowsAttribute, 0, 100, &windows);
  if (windows && CFArrayGetCount(windows) > 0) {
    AXUIElementRef window = (AXUIElementRef)CFArrayGetValueAtIndex(windows, 0);
    AXUIElementSetAttributeValue(window, kAXMainAttribute, kCFBooleanTrue);
    AXUIElementPerformAction(window, kAXRaiseAction);
  }
  if (windows) CFRelease(windows);
  CFRelease(app);
}

void WindowMacOS::to_background() {
  if (!*is_valid()) throw core::exceptions::WindowDoesNotValidException();
  auto pid = *get_process_id();
  ProcessSerialNumber psn;
  GetProcessForPID(pid, &psn);
  SetFrontProcess(&psn);
  AXUIElementRef app = AXUIElementCreateApplication(pid);
  CFArrayRef windows;
  AXUIElementCopyAttributeValues(app, kAXWindowsAttribute, 0, 100, &windows);
  if (windows && CFArrayGetCount(windows) > 0) {
    AXUIElementRef window = (AXUIElementRef)CFArrayGetValueAtIndex(windows, 0);
    AXUIElementSetAttributeValue(window, kAXMainAttribute, kCFBooleanFalse);
  }
  if (windows) CFRelease(windows);
  CFRelease(app);
}

}  // namespace appwindows::macos