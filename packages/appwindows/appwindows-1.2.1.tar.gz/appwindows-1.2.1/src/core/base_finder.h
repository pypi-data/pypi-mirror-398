#pragma once

#include <memory>
#include <string>
#include <vector>

#include "base_window.h"

#include "./exceptions/window_does_not_found.h"

namespace appwindows::core {

class Finder {
 public:
  virtual ~Finder() = default;
  [[nodiscard]]
  virtual std::vector<std::shared_ptr<Window>> get_all_windows() const = 0;
  [[nodiscard]]
  virtual std::unique_ptr<std::string> get_os() const = 0;
  
  [[nodiscard]] virtual std::vector<std::string> get_all_titles() const {
    std::vector<std::string> titles;
    for (const auto& i : get_all_windows()) titles.push_back(*i->get_title());
    return titles;
  }

  [[nodiscard]] virtual std::shared_ptr<Window> get_window_by_title(
      const std::string title) const {
    const auto windows = get_all_windows();
    for (auto window : windows)
      if (window->get_title()->find(title) != std::string::npos) return window;
    throw exceptions::WindowDoesNotFoundException();
  }

  [[nodiscard]] virtual std::shared_ptr<Window> get_window_by_process_id(
      const int process_id) const {
    const auto windows = get_all_windows();
    for (auto window : windows)
      if (*window->get_process_id() == process_id) return window;
    throw exceptions::WindowDoesNotFoundException();
  }
};

}  // namespace appwindows::core