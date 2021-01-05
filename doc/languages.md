## Language Support

The languages currently have some level of support in the `solver` script. Most contain an executor that is compatible with performance timing, but some do not.

### C

C source code is compiled with `gcc` without any fancy options or libraries.

### Timing Support

A c executor exists with the following signature

```c
void executor(
    char *data[],
    char *(*part1_fn)(char **),
    char *(*part2_fn)(char **),
    int argc,
    char *argv[]);
```

Below is template code for using the executor

```c
// main.c
#include "../../lib/lib.h"

char *part1_result(char *data[])
{
  // compute part 1 solution
  return solution;
}

char *part2_result(char *data[])
{
  // compute part 2 solution
  return solution;
}

int main(int argc, char *argv[])
{
  // load challenge input
  executor(data, part1_result, part2_result, argc, argv);
}
```

### Golang

Support for golang is minimal. `solver` will compile and run a solution in `main.go`, but there is no exector for performance timing.

### Java

### Timing Support

A Java executor exists with the following signature

```java
public interface Solution {
  public String part1Answer();
  public String part2Answer();
}

public class Executor {
  public Executor(Solution solution);
  public void run(String[] args);
}
```

Below is template code for using the executor

```java
// Main.java
import tcollier.Executor;
import tcollier.Solution;

class Day1Solution implements Solution {
  private String[] data;

  public Day0Solution(String[] data) {
    this.data = data;
  }

  public String part1Answer() {
    // compute part 1 solution
    return solution
  }

  public String part2Answer() {
    // compute part 2 solution
    return solution
  }
}

class Main {
  public static void main(String[] args) {
    String[] data = // load data
    Executor executor = new Executor(new Day1Solution(data));
    executor.run(args);
  }
}
```

### Lisp

Support for common lisp is minimal. `solver` will run a solution in `main.lisp` using `sbcl` ([download from sbcl.org](http://www.sbcl.org/) or install with HomeBrew), but there is no exector for performance timing.

### Python

### Timing Support

A python executor exists, below is template code for using the executor

```python
# main.py
import sys

from lib.executor import Executor


def part1_solution(input):
    # compute part 1 solution
    return solution


def part2_solution(input):
    # compute part 2 solution
    return solution

data = # fetch data
executor = Executor(data, part1_solution, part2_solution)
executor(sys.argv)
```

### Ruby

### Timing Support

A ruby executor exists, below is template code for using the executor

```ruby
# main.rb
require_relative '../../lib/executor'

part1_proc = Proc.new { |input| compute_part1_solution(input) }
part2_proc = Proc.new { |input| compute_part2_solution(input) }
executor = Executor.new(load_input, part1_proc, part2_proc)
executor.run(ARGV)
```

### Rust

### Timing Support

**IMPORTANT**: The executor code needs to be soft linked from the challenge day directory in order for rustc to compile correctly, e.g.

```
% cd 2020/01
% ln -s ../../lib/util.rs
```

Below is template code for using the executor

```rs
// main.rs
use std::env;

mod util;

struct Day1Solution {
  input: Vec<String>
}

impl util::Solution for Day1Solution {
  fn part1_result(&self) -> String {
    // compute and return part 1 solution
  }

  fn part2_result(&self) -> String {
    // compute and return part 2 solution
  }
}

fn main() {
  let input = // load input
  let solution = Day1Solution { input: input };
  let executor = util::Executor::new(&solution as &util::Solution);
  let args = env::args().collect();
  executor.run(args);
}
```

### Scala

### Timing Support

A scala executor exists, below is template code for using the executor

```scala
import tcollier.Executor;
import tcollier.Solution;

class Day1Solution(val input: Array[String]) extends Solution {
  def part1Answer(): String = {
    // compute part 1 solution
    return solution
  }

  def part2Answer(): String = {
    // compute part 2 solution
    return solution
  }
}

object Main {
  def main(args: Array[String]): Unit = {
    val data: Array[String] = // load data
    val executor: Executor = new Executor(new Day0Solution(data));
    executor.run(args);
  }
}
```

### Typescript

### Requirements

The `solver` script uses `node` to compile typescript files and run the compiled javascript. Ensure `node` and `npm` are installed.

### Timing Support

A typescript executor exists, below is template code for using the executor

```ts
// main.ts
const loadData = (): string[] => // load data

const part1Result = (words: string[]): string => {
  // compute and return part 1 solution
}

const part2Result = (words: string[]): string => {
  // compute and return part 2 solution
}

export { loadData, part1Result, part2Result }
```