#include "finder.h"

#include <windows.h>

#include <memory>

#include "../core/base_window.h"
#include "window.h"

namespace appwindows::windows {

FinderWindows::FinderWindows() = default;

std::unique_ptr<std::string> FinderWindows::get_os() const {
  return std::make_unique<std::string>("Windows::Windows");
};

std::vector<std::shared_ptr<core::Window>> FinderWindows::get_all_windows()
    const {
  std::vector<std::shared_ptr<core::Window>> result;
  EnumWindows(
      [](const HWND hwnd, const LPARAM lparam) {
        auto& windows =
            *reinterpret_cast<std::vector<std::shared_ptr<core::Window>>*>(
                lparam);
        if (IsWindowVisible(hwnd))
          windows.push_back(
              std::make_shared<WindowWindows>(std::make_shared<HWND>(hwnd)));
        return TRUE;
      },
      reinterpret_cast<LPARAM>(&result));
  return result;
}

}  // namespace appwindows::windows
