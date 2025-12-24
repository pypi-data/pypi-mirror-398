#pragma once

#include <memory>
#include <vector>

#include "../core/base_finder.h"
#include "../core/base_window.h"

namespace appwindows::macos {

class FinderMacOS final : public core::Finder {
public:
  FinderMacOS();
  [[nodiscard]] std::vector<std::shared_ptr<core::Window>> get_all_windows() const override;
  [[nodiscard]] std::unique_ptr<std::string> get_os() const override;
};

}  // namespace appwindows::macos