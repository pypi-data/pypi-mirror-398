# Xylo – Usage Guide

---

## Requirements

- Windows
- Python 3.8+
- A valid DLL file
- A running target process

---

## Installation

pip install xylo

## Basic Usage

from xylo import Xylo


Create an instance:

xylo = Xylo()


Required Configuration

You must configure:

A DLL path

Either a process name OR a process ID

If no DLL is provided, execution will fail.

Configuration Methods

Set target by process name

xylo.Name("example.exe")


Set target by process ID

xylo.Pid(1234)


Set DLL path

xylo.Dll(r"C:\Path\To\example.dll")


Execution

Inject

xylo.Inject()


## Examples

Inject using process name

from xylo import Xylo

Xylo() \
    .Name("notepad.exe") \
    .Dll(r"C:\Dlls\test.dll") \
    .Inject()


Inject using PID

from xylo import Xylo

Xylo() \
    .Pid(4321) \
    .Dll(r"C:\Dlls\test.dll") \
    .Inject()



Full Script Example

from xylo import Xylo

def main():
    xylo = Xylo()

    xylo.Name("explorer.exe") \
        .Dll(r"C:\Dlls\payload.dll") \
        .Inject()

if __name__ == "__main__":
    main()
