#pragma once

#include <stdexcept>

namespace appwindows::core::exceptions {

class WindowDoesNotFoundException final : public std::runtime_error {
 public:
  explicit WindowDoesNotFoundException()
      : runtime_error("Window does not found") {}
};

}  // namespace appwindows::core::exceptions