#pragma once

#include <memory>
#include <string>
#include <vector>

#include <pybind11/numpy.h>

#include "geometry/point.h"
#include "geometry/size.h"
#include "geometry/quad_points.h"

namespace py = pybind11;

namespace appwindows::core {

class Window {
 public:
  virtual ~Window() = default;
  [[nodiscard]] virtual std::unique_ptr<QuadPoints> get_points() = 0;
  [[nodiscard]] virtual std::unique_ptr<std::string> get_title() const = 0;
  [[nodiscard]] virtual std::unique_ptr<Size> get_size() const = 0;
  [[nodiscard]] virtual std::unique_ptr<int> get_process_id() const = 0;
  [[nodiscard]] virtual std::unique_ptr<bool> is_valid() const = 0;
  [[nodiscard]] virtual py::array_t<unsigned char> get_screenshot() = 0;

  virtual void set_minimize(bool is_minimize) = 0;
  virtual void set_fullscreen(bool is_fullscreen) = 0;
  virtual void resize(Size size) = 0;
  virtual void move(Point point) = 0;
  virtual void close() = 0;
  virtual void to_foreground() = 0;
  virtual void to_background() = 0;
};

}  // namespace appwindows::core