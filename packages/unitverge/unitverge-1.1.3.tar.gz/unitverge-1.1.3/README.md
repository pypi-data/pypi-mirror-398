# UnitVerge — A Meta-Tool for Creating Tools

[![Status](https://img.shields.io/badge/status-beta-yellow.svg)](https://github.com/pt-main/unitverge)
[![PyPI](https://img.shields.io/pypi/v/unitverge.svg)](https://pypi.org/project/unitverge/)
[![GitHub](https://img.shields.io/github/v/tag/pt-main/unitverge.svg?label=GitHub)](https://github.com/pt-main/unitverge)
![Name](https://img.shields.io/badge/name-unitverge-blue.svg)

**A foundation for building systems of any complexity without compromise.** UnitVerge is not a framework in the conventional sense, but a multi-layered architecture for creating specialized languages, code generators, and computational systems with complete control over every abstraction layer. The system eliminates dependency on external libraries and imposed architectural decisions, providing a toolkit for building tools perfectly tailored to the task.

## Key Features

**Full Extensibility at All Levels.** Every system component—from the virtual machine to syntactic sugar—can be redefined, extended, or completely replaced. Extend the Bytex language with new commands, create your own metaclasses for code generation, modify the type system, or implement specialized optimizations without the constraints of inherited architecture.

**Multi-Layered Architecture.** The system operates on four coordinated abstraction levels. The bottom layer is **Bytex VM**, a highly optimized Cython-based virtual machine with a register architecture and efficient memory management. Above it is the **Bytex language**, an assembly-like DSL for direct VM control. The third layer is **Verge**, a translation and code generation system with plugin and metaclass support. The top layer is **Unit**, a Python interface for the declarative description of complex structures.

**Performance Without Compromise.** Critical components are implemented in Cython using static typing and low-level optimizations. Bytex VM executes computational operations 3-4 times faster than standard Python when working with register-section operations. The hybrid architecture allows combining high-level abstractions with near-native performance.

**Points and Contexts System.** The unique Points model allows code to be separated into independent fragments with dynamic switching during generation. This implements the principle of conditional compilation, enabling the creation of adaptive systems that assemble various execution variants from a single source description. Contexts ensure modularity and component isolation.

## Architecture in Detail

**Bytex VM** – A register-based virtual machine optimized for sequential operation execution. Supports 2048 registers with 4096 sections each (over 8 million cells), memory management via a pointer system, multiple memory areas (hands), and parametric cells. Fully written in Cython using cdef classes and static methods for maximum performance.

**Bytex Language** – A low-level language that transpiles to Python code interacting with the VM. Syntax includes memory management commands (`moveto`, `jump`), arithmetic operations (`add`, `sub`, `mull`), flow control (`start`, `do`, `goto`), preprocessor directives (`#include`, `#append`), and a plugin system for extension. The translator is built on command tables with support for dynamic addition of new instructions.

**Verge Core** – The code generation core, built on a metaclass hierarchy. The base class `UVObj` provides three specializations: `generatable` for code generation contexts with the points system, `builder` for instruction assembly, and `instruction` as a foundation for user extensions. The dispatch system uses method tables instead of conditional constructs.

**Unit DSL** – A high-level Python interface that turns context managers into a declarative language for describing programs. Allows describing conditions, loops, functions, and classes in Python style, which are translated into optimized Bytex code. Supports plugins that add new methods at runtime.

## Quick Start

```python
from UnitVerge import *

# Creating a context with a points system
ctx = Unit("main")
ctx.new_point("init")
ctx.set_point("init")
ctx.var_btx("x", 10)

# Declarative logic description
with ctx.ifblock("x > 5"):
    ctx.println_btx("Condition met")
    
# Generation and execution
ctx.pipeline(['init', 'main'])
v = Verge()
v.interprete([ctx])
code = v.compile()

# Result — optimized Bytex code
print(code)
```

## Extensibility in Practice

**Adding a Bytex Command:**
```python
def custom_command(translator, line):
    # line = ["mycmd", "arg1", "arg2"]
    edit = translator.plugin('main')
    edit(f"# Custom command")
    edit(f"print('Called: {line[1]}')")

translator = Translator()
translator.plugin('command')("mycmd", custom_command)
```

**Creating a Verge Metaclass:**
```python
class CustomGenerator(UVObj('generatable')):
    def __init__(self):
        super().__init__()
        self.pipeline(['main'])
    
    def generate_special(self, data):
        self.raw([f"# Generation for {data}"])
        return self
```

**Unit DSL Plugin:**
```python
ctx = Unit("example")
ctx.plugin("security_check", lambda self, msg: self.raw(f"# Security check: {msg}"))
ctx.security_check("Access granted")
```

## Performance

The system demonstrates significant advantages in computational tasks due to the specialized architecture of Bytex VM. Operations with registers and sections are executed without the overhead of Python objects, and the Cython implementation provides near-C performance for critical sections. In tests of matrix operations and numerical modeling, a 3-4x speedup compared to pure Python is achieved. Translating Bytex to Python code minimizes interpretation overhead, generating dense, efficient code.

## Application Areas

**Creating Domain-Specific Languages.** UnitVerge is ideal for building DSLs in narrow domains: financial computing, data analysis, configuration management, hardware description. The multi-layered approach allows starting with high-level syntax and gradually optimizing critical sections, descending to the Bytex level.

**Developing Code Generation Tools.** The points and contexts system enables building complex code generators for automatic boilerplate assembly, design patterns, serializers, validators. Plugin support makes it possible to create extensible systems like web development frameworks or ORMs.

**Language and Virtual Machine Research.** UnitVerge provides a ready-made infrastructure for experimenting with new programming paradigms, type systems, memory models. The ability to modify any layer allows testing hypotheses without building a system from scratch.

**High-Performance Computing.** The combination of Bytex VM and Cython optimizations provides a tool for tasks where pure Python is not fast enough, but moving to C/C++ is excessive. The register architecture is efficient for numerical algorithms, signal processing, cryptographic operations.

## Development Philosophy

**Control Over Every Layer.** UnitVerge is built on the principle that a developer should be able to change any system component without encountering architectural limitations. If the standard behavior is suboptimal for a task—it can be replaced without breaking the rest of the system.

**Minimal Dependencies.** The only mandatory dependency is Python. Cython components are supplied pre-compiled, but their source code is available for modification. This allows deploying systems built on UnitVerge in isolated environments without complex toolchains.

**Architectural Integrity.** All system levels are designed to work together but remain independent. Bytex VM can be used separately, Verge with other backends, Unit DSL for generating code in other languages. This provides flexibility without losing consistency.

---

UnitVerge is not a ready-made solution, but a tool for creating solutions. For typical tasks, specialized frameworks exist; for unique ones—specialized systems must be built. This framework is for those who prefer to create perfect tools instead of adapting imperfect ones.

By Pt.
