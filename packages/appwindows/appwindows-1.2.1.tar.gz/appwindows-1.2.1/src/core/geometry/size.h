#pragma once

namespace appwindows::core {

class Size {
 public:
  Size(int width, int height);
  [[nodiscard]] int get_width() const noexcept { return width_; };
  [[nodiscard]] int get_height() const noexcept { return height_; };

 private:
  int width_;
  int height_;
};

}  // namespace appwindows::core