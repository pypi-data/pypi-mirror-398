# Crew - The C/C++ Package Manager

## What is Crew?
**Crew is not a framework.** It is a **Dependency Manager** (like `npm` for JavaScript or `cargo` for Rust) designed specifically for C and C++.

It solves the biggest headache in C++ development: **Installing Libraries**.

## Requirements
*   **Python 3.x**: To run the `crew` tool.
*   **Git**: To download packages.
*   **Compiler**: `gcc`, `g++`, or `clang` for building your projects.

## Installation

### Option 1: Install from PyPI (Recommended)
*Once published, you can install it with a single command:*
```bash
pip install crew-cli
```

### Option 2: Install from Source (For Developers)
1.  **Clone the repo:**
    ```bash
    git clone https://github.com/127crew/crew.git
    cd crew
    ```

2.  **Install locally:**
    ```bash
    pip install .
    ```

3.  **Verify:**
    Open a new terminal and type:
    ```bash
    crew --help
    ```
    If it works, you can now go to **any folder** and just run `crew init` or `crew create`.

## Quick Start

### New Project (`crew create`)
Best for starting from scratch. Creates a folder, code, and config.
```bash
# Create a C project
python3 crew.py create my-app --template c
```

### Existing Project (`crew init`)
Best if you already have code. Creates `crew.json` in the current folder.
```bash
cd my-existing-project
python3 crew.py init
```

### Install Dependencies
```bash
# Install a C library (stb)
python3 crew.py install https://github.com/nothings/stb.git

# Install a C++ library (nlohmann json)
python3 crew.py install https://github.com/nlohmann/json.git@v3.11.2
```
## License
This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.
## Examples

### C Example (`stb_image`)
**File: `main.c`**
```c
#include <stdio.h>
#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"

int main() {
    printf("STB Image Version: %d\n", STBI_VERSION);
    return 0;
}
```
**Build & Run:**
```bash
gcc main.c -lm $(python3 crew.py flags) -o app_c
./app_c
```

---

### C++ Example (`nlohmann/json`)
**File: `main.cpp`**
```cpp
#include <iostream>
#include <nlohmann/json.hpp>
using json = nlohmann::json;

int main() {
    json j = { {"name", "Crew"}, {"awesome", true} };
    std::cout << j.dump(4) << std::endl;
    return 0;
}
```
**Build & Run:**
```bash
g++ main.cpp $(python3 crew.py flags) -o app_cpp
./app_cpp
```

## How to use in your project
You don't need to change your build system. Just add `$(crew flags)` to your compiler command. It generates the necessary `-I` flags (e.g., `-Icrew_modules/stb`).
