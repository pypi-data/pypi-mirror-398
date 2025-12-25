# Windows Support Status

**Current Status:** Not supported

Windows builds are disabled due to C++ compatibility issues in the adaptagrams dependency.

## Build Errors

When building with MSVC 2022 (Visual Studio 17.x), the adaptagrams library fails to compile with the following errors:

### 1. Deprecated C++ Features Removed in C++17

```
error C3861: 'mem_fun': identifier not found
error C3861: 'bind2nd': identifier not found
error C2504: 'unary_function': base class undefined
```

**Affected files:**
- `cola/libproject/project.cpp` (lines 117, 149, 181, 197, 237, 457)
- `cola/libdialect/constraints.cpp`
- `cola/libdialect/trees.cpp`

**Cause:** MSVC 2022 defaults to C++17 or later, which removed these deprecated features:
- `std::mem_fun` (removed in C++17, use `std::mem_fn` or lambdas)
- `std::bind2nd` (removed in C++17, use `std::bind` or lambdas)
- `std::unary_function` (removed in C++17, define result_type/argument_type manually)

### 2. swap() Function Overload Conflicts

```
error C2664: 'void dialect::swap(dialect::Graph &,dialect::Graph &)':
cannot convert argument 1 from 'dialect::SepType' to 'dialect::Graph &'
```

**Affected file:** `cola/libdialect/constraints.cpp` (lines 218, 219, 228, 229, 251, 252, 261, 262)

**Cause:** The code calls `swap()` on enum types, but a custom `dialect::swap(Graph&, Graph&)` overload shadows `std::swap`. MSVC is stricter about ADL (Argument Dependent Lookup) than GCC/Clang.

### 3. Lambda Type Mismatch in Ternary Operator

```
error C2446: ':': no conversion from 'lambda_1' to 'lambda_2'
```

**Affected file:** `cola/libdialect/trees.cpp` (lines 754, 758, 866)

**Cause:** Code uses ternary operator with two different lambda types. Each lambda has a unique type in C++, so they cannot be used in a ternary expression without conversion to `std::function`.

## Proposed Fixes

To restore Windows support, the [adaptagrams fork](https://github.com/shakfu/adaptagrams) needs the following patches:

### Fix 1: Replace Deprecated Function Adapters

**Before:**
```cpp
#include <functional>
using std::mem_fun;
using std::bind2nd;

// Usage
for_each(items.begin(), items.end(), mem_fun(&Item::process));
for_each(items.begin(), items.end(), bind2nd(mem_fun(&Item::setValue), value));
```

**After:**
```cpp
#include <functional>

// Usage - replace with lambdas
for_each(items.begin(), items.end(), [](Item* item) { item->process(); });
for_each(items.begin(), items.end(), [value](Item* item) { item->setValue(value); });

// Or use std::mem_fn (C++11+)
for_each(items.begin(), items.end(), std::mem_fn(&Item::process));
```

### Fix 2: Replace unary_function Inheritance

**Before:**
```cpp
struct MyFunctor : public std::unary_function<T, R> {
    R operator()(T arg) { ... }
};
```

**After:**
```cpp
struct MyFunctor {
    using argument_type = T;  // If needed for compatibility
    using result_type = R;    // If needed for compatibility
    R operator()(T arg) { ... }
};
```

### Fix 3: Fix swap() ADL Issues

**Before:**
```cpp
// In constraints.cpp
swap(sepType1, sepType2);  // Fails: finds dialect::swap(Graph&, Graph&)
```

**After:**
```cpp
// Explicitly use std::swap for non-Graph types
std::swap(sepType1, sepType2);

// Or rename dialect::swap to avoid shadowing
namespace dialect {
    void swapGraphs(Graph& a, Graph& b);  // Renamed
}
```

### Fix 4: Fix Lambda Ternary Expressions

**Before:**
```cpp
auto func = condition ? [](int x) { return x + 1; }
                      : [](int x) { return x - 1; };
```

**After:**
```cpp
std::function<int(int)> func = condition
    ? std::function<int(int)>([](int x) { return x + 1; })
    : std::function<int(int)>([](int x) { return x - 1; });

// Or use if/else
std::function<int(int)> func;
if (condition) {
    func = [](int x) { return x + 1; };
} else {
    func = [](int x) { return x - 1; };
}
```

## Alternative: Force C++14 Mode

A quicker (but less ideal) fix would be to force C++14 mode for adaptagrams on Windows. This would require modifying the adaptagrams CMakeLists.txt:

```cmake
if(MSVC)
    set(CMAKE_CXX_STANDARD 14)
    set(CMAKE_CXX_STANDARD_REQUIRED ON)
    # Disable C++17 features
    add_compile_options(/std:c++14)
endif()
```

**Note:** This approach is not recommended long-term as C++14 support in MSVC may eventually be deprecated.

## Testing Windows Builds Locally

If you want to test Windows builds:

1. Install Visual Studio 2022 with C++ workload
2. Open "Developer Command Prompt for VS 2022"
3. Clone and build:
   ```cmd
   git clone https://github.com/shakfu/hola-graph.git
   cd hola-graph
   pip install build
   python -m build
   ```

## References

- [C++17 Removed Features](https://en.cppreference.com/w/cpp/17#Removed_features)
- [std::mem_fn (replacement for mem_fun)](https://en.cppreference.com/w/cpp/utility/functional/mem_fn)
- [std::bind (replacement for bind2nd)](https://en.cppreference.com/w/cpp/utility/functional/bind)
- [MSVC C++ Language Conformance](https://docs.microsoft.com/en-us/cpp/overview/visual-cpp-language-conformance)
