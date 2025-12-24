#pragma once

#include <memory>

#include "../core/base_finder.h"
#include "../core/base_window.h"

namespace appwindows::windows {

class FinderWindows final : public core::Finder {
 public:
  FinderWindows();
  [[nodiscard]]
  std::vector<std::shared_ptr<core::Window>> get_all_windows() const override;
  [[nodiscard]]
  std::unique_ptr<std::string> get_os() const override;
};

}  // namespace appwindows::windows