#pragma once

#include <memory>

#include "base_finder.h"

namespace appwindows {

std::shared_ptr<core::Finder> get_finder();

}  // namespace appwindows