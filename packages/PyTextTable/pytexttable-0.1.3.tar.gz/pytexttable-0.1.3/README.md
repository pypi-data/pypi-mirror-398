# TextTable

TextTable is a lightweight Python module that helps developers draw well-formatted
tables in the console using ASCII or Unicode box-drawing characters.

It is designed for command-line applications where clear tabular output and
optional pagination are required.

---

## Features

- Draw tables using ASCII or Unicode borders
- Support for single-line, double-line, and dashed table styles
- Automatic column width calculation
- Left, right, and center text alignment
- Pagination support for large datasets
- Cross-platform (Windows, Linux, macOS)

---

## Installation

```bash
pip install pytexttable
```
## Basic Usage

from TextTable import TextTable

t = TextTable(ttype='=', page_size=10)

t.set_columns(['Column 1', 'Column 2', 'Column 3'])

t.add_row(['Data 1', 'Data 2', 'Data 3'])

t.add_row(['More', 'Sample', 'Values'])

print(t)

## Pagination Example

from TextTable import TextTable

t = TextTable(ttype='-', page_size=5)

t.set_columns(['ID', 'Name', 'Value'])

for i in range(20):

    t.add_row([str(i), f'Item {i}', str(i * 10)])

t.print_with_pagination()


##Use keyboard input to navigate:

1 or right/up arrow → Next page

2 or left/down arrow → Previous page

0 / Enter → Exit