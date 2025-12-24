#pragma once

namespace appwindows::core {

class Point {
 public:
  Point(int x, int y);
  Point operator+(const Point& other) const;
  Point operator-(const Point& other) const;
  Point operator*(const Point& other) const;
  Point operator/(const Point& other) const;
  bool operator==(const Point& other) const;
  bool operator!=(const Point& other) const;
  [[nodiscard]] int get_x() const;
  [[nodiscard]] int get_y() const;

 private:
  int x_;
  int y_;
};

}  // namespace appwindows::core