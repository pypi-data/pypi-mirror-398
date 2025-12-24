#pragma once

#include "point.h"

namespace appwindows::core {

class QuadPoints {
 public:
  QuadPoints(Point left_top, Point right_top, Point right_bottom, Point left_bottom) : left_top_(left_top),
                                                                                 right_top_(right_top), 
                                                                                 right_bottom_(right_bottom),
                                                                                 left_bottom_(left_bottom) {};
  Point get_left_top() { return left_top_; }
  Point get_right_top() { return right_top_; }
  Point get_right_bottom() { return right_bottom_; }
  Point get_left_bottom() { return left_bottom_; }
  
 private:
  Point left_top_;
  Point right_top_;
  Point right_bottom_;
  Point left_bottom_;
};

}  // namespace appwindows::core