#pragma once

#include <X11/Xlib.h>

#include <memory>
#include <vector>

#include "../core/base_finder.h"
#include "../core/base_window.h"

namespace appwindows::x_server {

class FinderXServer final : public core::Finder {
 public:
  FinderXServer();
  [[nodiscard]]
  std::vector<std::shared_ptr<core::Window>> get_all_windows() const override;
  [[nodiscard]]
  std::unique_ptr<std::string> get_os() const override;
  
  static Display* open_display();
};

}  // namespace appwindows::x_server