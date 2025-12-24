#pragma once

#include <stdexcept>
#include <string>

namespace appwindows::core::exceptions {

class InvalidSizeException final : public std::invalid_argument {
 public:
  explicit InvalidSizeException(const int width, const int height)
      : invalid_argument("Invalid width(" + std::to_string(width) +
                         ") or height(" + std::to_string(height) + ")") {}
};

}  // namespace appwindows::core::exceptions