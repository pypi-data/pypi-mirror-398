#pragma once

#include <X11/Xlib.h>

#include <memory>
#include <vector>

#include "../core/base_window.h"
#include "../core/geometry/quad_points.h"
#include "../core/geometry/point.h"
#include "../core/geometry/size.h"

using WindowX = Window;

namespace appwindows::x_server {

class WindowXServer final : public core::Window {
 public:
  explicit WindowXServer(WindowX window);
  [[nodiscard]] std::unique_ptr<core::QuadPoints> get_points() override;
  [[nodiscard]] std::unique_ptr<core::Size> get_size() const override;
  [[nodiscard]] std::unique_ptr<std::string> get_title() const override;
  [[nodiscard]] std::unique_ptr<int> get_process_id() const override;
  [[nodiscard]] py::array_t<unsigned char> get_screenshot() override;
  [[nodiscard]] std::unique_ptr<bool> is_valid() const override;

  void set_minimize(bool is_minimize) override;
  void set_fullscreen(bool is_fullscreen) override;
  void resize(core::Size size) override;
  void move(core::Point point) override;
  void close() override;
  void to_foreground() override;
  void to_background() override;

 private:
  void to_background(bool is_background);
  void to_foreground(bool is_foreground);
  WindowX window_;
};

}  // namespace appwindows::x_server