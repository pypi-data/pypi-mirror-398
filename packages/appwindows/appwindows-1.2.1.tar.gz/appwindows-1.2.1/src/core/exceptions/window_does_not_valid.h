#pragma once

#include <stdexcept>

namespace appwindows::core::exceptions {

class WindowDoesNotValidException final : public std::runtime_error {
 public:
  explicit WindowDoesNotValidException()
      : runtime_error("Window does not valid") {}
};

}  // namespace appwindows::core::exceptions