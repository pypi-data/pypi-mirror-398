# catena4j v2.1.0

## Introduction

Catena4J is a high-performance Python implementation of Defects4J and CatenaD4J with a native API.

It reimplemented most defects4j commands using Python and Java for better performance, while providing API for programming access to the dataset.

[CatenaD4J](https://github.com/universetraveller/CatenaD4J) (c4j) is a dataset for evaluating automated program repair techniques on indivisible multi-hunk bugs. A "catena bug" consists of multiple interdependent code hunks that must all be fixed together to resolve the bug.

Catena4J contains bugs from both Defects4J and CatenaD4J.

> [!NOTE]
> The defects4j version currently implemented is v2.1.0 and plan to upgrade to v3.0.1 in next version. In this case, the JDK requirement will also change to JDK 11 (current JDK 8).

### Key Features
- **1500+ supported bugs** across 17 projects including all Defects4J and CatenaD4J bugs
- **426 indivisible multi-hunk bugs** requiring coordinated fixes with minimized tests
- **High performance** python implementation of Defects4J with a native API
- **Compatible with Defects4J** by implementing most defects4j commands
- **Extensible architecture** supporting custom commands and loaders

### Bug Structure
Each bug in CatenaD4J has:
- A unique `catena_id (cid)` identifier
- Association with a source Defects4J `bug_id (bid)`
- Minimal failing tests with single assertions
- Multiple interdependent code hunks

Bugs are referenced using the format: `<bug_id><b/f>[<cid>]`
- `bug_id`: Original Defects4J bug number
- `b/f`: Buggy or fixed version
- `cid`: Optional catena identifier for bugs in CatenaD4J

## Table of Contents
- [Introduction](#introduction)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Available Commands](#available-commands)
- [Command Reference](#command-reference)
- [Configuration](#configuration)
- [Examples](#examples)
- [Comparison with Defects4J](#comparison-with-defects4j)

## Installation

### Requirements
- **Python 3**: Pre-installed on most Linux/macOS systems
- **Defects4J v2.0**: See [defects4j repository](https://github.com/rjust/defects4j.git)
- **Java 1.8 (JDK 8)**: See [OpenJDK 8](https://openjdk.org/projects/jdk8/)

### Package Manager (Recommended)

The easiest way to install this repository is using the python package manager such as `uv` and `pip`.

This operation will install this repository as a python library while providing a console script `catena4j`.

From the built package:

```bash
pip install catena4j
```

or from source:

```bash
pip install .
```

Test the installation:
```bash
catena4j pids
```


### Docker Installation

Another easy way to get started is using Docker.

1. **Install Docker** (if not already installed):
   - Follow instructions at [Install Docker Engine](https://docs.docker.com/engine/install/)

2. **Download the Dockerfile**:
   ```bash
   curl https://raw.githubusercontent.com/universetraveller/catena4j/main/Dockerfile -o Dockerfile
   ```

3. **Build the Docker image**:
   ```bash
   docker build -t catena4j:main -f ./Dockerfile .
   ```

4. **Create and run a container**:
   ```bash
   docker run -it catena4j:main /bin/bash
   ```

### Manual Installation

For native installation without Docker:

1. **Install Prerequisites**:
   - Install Python 3, Java 8, and Defects4J v2.0 (see Requirements above)

2. **Clone the Repository**:
   ```bash
   git clone https://github.com/universetraveller/catena4j.git
   cd catena4j
   ```

3. **Build the Java Toolkit**:
   ```bash
   cd toolkit
   ./gradlew clean build
   cd ..
   ```

4. **Using setup_unix_user.py (Optional)**
   For custom installation with a user-specified startup script:

   The repository contains an example startup script `c4j` but this can also be generated using
   `setup_unix_user.py` if you don't want to install it as a library or to python's site-packages.

   ```bash
   python3 setup_unix_user.py -n <script_name> -p <python_path>
   ```

   Options:
   - `-n, --name`: Name of the startup script to generate (default: `c4j`)
   - `-p, --python`: Path to Python interpreter (default: current Python executable)

   This will:
   1. Build the Java toolkit
   2. Generate a startup script with your chosen name
   3. Add the script to your PATH (in `.bashrc`, `.zshrc`, or `.profile`)

5. **Add to PATH** (when using the provided startup script `c4j`):
   ```bash
   export PATH=$PATH:/path/to/catena4j
   ```

6. **Verify Installation**:
   ```bash
   c4j pids
   ```

## Quick Start

1. **List available projects**:
   ```bash
   catena4j pids
   ```

2. **List bugs for a project**:
   ```bash
   catena4j bids -p Chart
   ```

3. **List catena IDs for a specific bug**:
   ```bash
   catena4j cids -p Chart -b 15
   ```

4. **Check out a buggy version**:
   ```bash
   catena4j checkout -p Chart -v 15b1 -w ./buggy_chart
   ```

5. **Compile the checked-out version**:
   ```bash
   catena4j compile -w ./buggy_chart
   ```

6. **Run tests**:
   ```bash
   catena4j test -w ./buggy_chart
   ```

7. **Export properties**:
   ```bash
   catena4j export -p tests.trigger -w ./buggy_chart
   ```

## Available Commands

| Command   | Description                                              |
|-----------|----------------------------------------------------------|
| checkout  | Check out a specific version of a bug                    |
| export    | Export version-specific properties                       |
| test      | Run tests on a checked-out project version               |
| compile   | Compile a checked-out project version                    |
| clean     | Clean the output directory                               |
| reset     | Reset unstaged modifications in a working directory      |
| pids      | Print available project names                            |
| bids      | Print available bug IDs for a project                    |
| cids      | Print available catena IDs for a bug                     |

## Command Reference

### checkout

Check out a specific version of a bug to a working directory.

**Syntax**:
```bash
catena4j checkout -p <project> -v <version_id> -w <work_dir> [--full-history]
```

**Options**:
- `-p <project>`: Project name (required)
- `-v <version_id>`: Version identifier in format `<bid><b/f>[<cid>]` (required)
  - `bid`: Bug ID (integer)
  - `b/f`: 'b' for buggy, 'f' for fixed
  - `cid`: Catena ID (optional, integer)
- `-w <work_dir>`: Working directory path (required)
- `--full-history`: Generate additional commits (post-fix, pre-fix revisions)

**Examples**:
```bash
# Check out buggy version of Chart bug 15, catena ID 1
catena4j checkout -p Chart -v 15b1 -w ./chart_15b1

# Check out fixed version of Chart bug 15 from Defects4j
catena4j checkout -p Chart -v 15f -w ./chart_15f

# Check out with full history
catena4j checkout -p Chart -v 15b1 -w ./chart_15b1 --full-history
```

### export

Export version-specific properties of a checked-out bug.

**Syntax**:
```bash
catena4j export -p <property> [-w <work_dir>] [-o <output_file>] [--from-cache] [--update-cache]
```

**Options**:
- `-p <property>`: Property name to export (required)
- `-w <work_dir>`: Working directory (default: current directory)
- `-o <output_file>`: Output file path (default: stdout)
- `--from-cache`: Read from cache instead of computing
- `--update-cache`: Force cache update

**Available Properties**:

*CatenaD4J Properties*:
- `classes.modified`: Classes modified by the bug fix
- `tests.trigger`: Trigger tests that expose the bug

*Defects4J Static Properties*:
- `classes.relevant`: Classes loaded by triggering tests
- `dir.src.classes`: Source directory of classes
- `dir.src.tests`: Source directory of tests
- `tests.relevant`: Tests touching modified sources

*Defects4J Dynamic Properties* (computed at runtime):
- `cp.compile`: Classpath to compile the project
- `cp.test`: Classpath for tests
- `dir.bin.classes`: Target directory of classes
- `dir.bin.tests`: Target directory of test classes
- `tests.all`: List of all developer-written tests

**Examples**:
```bash
# Export trigger tests to stdout
catena4j export -p tests.trigger -w ./chart_15b1

# Export to file
catena4j export -p classes.modified -w ./chart_15b1 -o modified.txt

# Use cache
catena4j export -p tests.all -w ./chart_15b1 --from-cache
```

### test

Run tests on a checked-out project version.

**Syntax**:
```bash
catena4j test [-w <work_dir>] [-c] [-l] [-i <level>] [-t <test> | -r | --trigger]
```

**Options**:
- `-w <work_dir>`: Working directory (default: current directory)
- `-c, --compile`: Compile before running tests (will not compile by default)
- `-l, --list`: List tests without executing them (output to `<work_dir>/all_tests`)
- `-i, --isolation <level>`: Test isolation level (default: from config)
  - `1`: Reused isolated classloader (fastest)
  - `2`: Isolated classloader per test class
  - `3`: Use Ant's JUnit task (slowest, most isolated)
- `-t <test>`: Run specific test(s) in format `ClassName#methodName` (can be repeated)
- `-r`: Run only relevant tests
- `--trigger`: Run only trigger tests
- `-a`: Collect failed assertions without breaking (experimental)

**Isolation Levels**:

- Level 1 uses a single isolated classloader for the whole test process
   This level can produce identical test results for most test cases (98%+) compared with Defect4J and run fastest.

   For few bugs that contain order sensitive test cases this level can produce different results compared with defects4j.
   However, the results will not change in each run.

- Level 2 uses a single isolated classloader for each test class
   This level can produce more identical test results (99%+, except few test cases depend on classloader type) than level 1.

- Level 3 uses Ant's classloader directly
   This level simulates what defects4j's test command does so it can produce same test results compared with defects4j.

**Examples**:
```bash
# Run all tests
catena4j test -w ./chart_15b1

# Compile and run trigger tests
catena4j test -w ./chart_15b1 -c --trigger

# Run specific test
catena4j test -w ./chart_15b1 -t org.jfree.chart.ChartTest#testMethod

# List all tests without running
catena4j test -w ./chart_15b1 -l

# Run with maximum isolation
catena4j test -w ./chart_15b1 -i 3
```

### compile

Compile a checked-out project version.

**Syntax**:
```bash
catena4j compile [-w <work_dir>] [--target <target>] [--verbose]
```

**Options**:
- `-w <work_dir>`: Working directory (default: current directory)
- `--target <target>`: Compilation target (default: `compile.tests`)
  - Must contain 'compile' or be 'clean'
  - Examples: `compile`, `compile.tests`, `gradle.compile`
- `--verbose`: Show detailed compilation output

**Examples**:
```bash
# Compile tests (default)
catena4j compile -w ./chart_15b1

# Compile only classes
catena4j compile -w ./chart_15b1 --target compile

# Verbose compilation
catena4j compile -w ./chart_15b1 --verbose
```

### clean

Clean the build output directory (run ant's clean task).

**Syntax**:
```bash
catena4j clean [-w <work_dir>] [--verbose]
```

**Options**:
- `-w <work_dir>`: Working directory (default: current directory)
- `--verbose`: Show detailed output

**Example**:
```bash
catena4j clean -w ./chart_15b1
```

### reset

Reset all unstaged modifications in a working directory.

It run `git checkout <commit>` and `git clean -xdf` internally.

**Syntax**:
```bash
catena4j reset [-w <work_dir>]
```

**Options**:
- `-w <work_dir>`: Working directory to reset (default: current directory)

**Example**:
```bash
catena4j reset -w ./chart_15b1
```

### pids

Print all available project names in the dataset.

**Syntax**:
```bash
catena4j pids
```

**Example Output**:
```
Chart
Cli
Closure
Codec
Collections
Compress
...
```

### bids

Print available bug IDs for a specific project.

**Syntax**:
```bash
catena4j bids -p <project> [--with-cids] [-D | -A]
```

**Options**:
- `-p <project>`: Project name (required)
- `--with-cids`: Show only bug IDs that have at least one catena ID
- `-D`: Show deprecated bug IDs
- `-A`: Show all bug IDs (active and deprecated)

**Examples**:
```bash
# Show active bugs
catena4j bids -p Chart

# Show bugs with catena IDs
catena4j bids -p Chart --with-cids

# Show all bugs including deprecated
catena4j bids -p Chart -A
```

### cids

Print available catena IDs for a specific bug.

**Syntax**:
```bash
catena4j cids -p <project> -b <bug_id>
```

**Options**:
- `-p <project>`: Project name (required)
- `-b <bug_id>`: Bug ID (required)

**Example**:
```bash
catena4j cids -p Chart -b 15
```

## Configuration

CatenaD4J configuration is defined in `catena4j/config.py`. Key settings include:

### Global Settings
- `cli_program`: CLI program name (default: `'catena4j'`)
- `rich_output`: Enable colored and enhanced output (default: `True`)
- `minimal_checkout`: Skip unnecessary commit processes (default: `True`)

### Paths
- `c4j_rel_projects`: Relative path to projects directory
- `c4j_rel_toolkit_lib`: Path to compiled Java toolkit JAR
- `d4j_rel_ant_path`: Path to Defects4J Ant binaries
- `d4j_rel_projects`: Path to Defects4J projects metadata

### Testing
- `c4j_test_isolation_level`: Default test isolation level (default: `1`)
  - `1`: Reused isolated classloader
  - `2`: Isolated classloader per test class
  - `3`: Ant's JUnit task

### Toolkit Java Classes
- `c4j_toolkit_export_main`: Main class for export operations
- `c4j_toolkit_test_main`: Main class for test execution
- `c4j_toolkit_execute_main`: Main class for general execution

### Version Tags
- `c4j_tag`: Tag format for CatenaD4J versions
- `d4j_tag`: Tag format for Defects4J versions

To customize configuration, modify `catena4j/config.py` before installation or use the extensibility APIs or user_setup module to override settings programmatically.

## Examples

### Working with a Single Bug

```bash
# Create a workspace
mkdir -p workspace && cd workspace

# Check out a buggy version
catena4j checkout -p Math -v 5b1 -w ./math_5b1

# Navigate to working directory
cd math_5b1

# Export trigger tests
catena4j export -p tests.trigger -w .

# Compile the project
catena4j compile -w .

# Run trigger tests
catena4j test -w . --trigger

# Export modified classes
catena4j export -p classes.modified -w . -o modified_classes.txt

# Reset modifications
catena4j reset -w .
```

### Using Cache for Performance

```bash
# First run: compute and cache
catena4j export -p tests.all -w ./chart_15b1 --update-cache

# Subsequent runs: use cached results (much faster)
catena4j export -p tests.all -w ./chart_15b1 --from-cache

# Force cache refresh
catena4j export -p tests.all -w ./chart_15b1 --update-cache
```

## Comparison with Defects4J
This implementation optimizes runtime performance by reducing unnecessary operations, such as refining project build files and reimplementing commands.
It also provides an API for users, whereas Defects4J can only be executed as a command-line tool.

When checking out all 835 projects on the same machine, Defects4J takes 32:57, while this implementation completes the task in 05:48.
To ensure consistency, the outputs produced by Defects4J and Catena4J are compared and verified to be identical.

When exporting all properties in parallel, Defects4J takes 25 minutes, whereas this implementation takes only 5 minutes.
Even when this implementation is run sequentially, it completes in 19:14.

For testing, this implementation can achieve up to a 10× speedup.
However, there is a concern that test isolation is not well designed in some of these legacy projects, so Ant-based testing is still required.
That said, the current implementation produces identical test results for most test cases.

The average benchmark runtime for testing each project is summarized below:

Ant represents using the Ant junit task (level 3), while HashMap and LinkedHashMap are two implementations of level 1, and IsolatedClassLoader correspond to the implementation of level 2.

| Project         | Ant    | HashMap | LinkedHashMap | IsolatedClassLoader |
| --------------- | ------ | ------- | ------------- | ------------------- |
| JxPath          | 2.049  | 1.010   | 1.076         | 1.953               |
| Collections     | 12.892 | 11.939  | 12.510        | 12.818              |
| Csv             | 1.138  | 1.064   | 1.033         | 1.103               |
| JacksonXml      | 6.437  | 0.728   | 0.696         | 4.817               |
| Lang            | 8.787  | 8.630   | 8.463         | 8.764               |
| Jsoup           | 1.402  | 0.779   | 0.785         | 1.228               |
| Compress        | 3.560  | 3.152   | 3.094         | 3.480               |
| JacksonCore     | 3.518  | 2.749   | 2.651         | 3.390               |
| Mockito         | 15.842 | 4.535   | 4.444         | 13.223              |
| Math            | 18.602 | 12.868  | 14.978        | 18.259              |
| JacksonDatabind | 30.840 | 5.174   | 4.830         | 23.560              |
| Closure         | 30.477 | 6.921   | 6.694         | 27.873              |
| Codec           | 1.769  | 1.757   | 1.768         | 1.717               |
| Time            | 4.610  | 1.859   | 1.786         | 3.828               |
| Chart           | 4.967  | 2.220   | 2.123         | 4.492               |
| Cli             | 0.418  | 0.410   | 0.345         | 0.410               |
| Gson            | 1.684  | 0.580   | 0.572         | 1.291               |

The current implementation still requires a Defects4J installation to access certain metadata files and downloaded repositories.
In future work, it may be possible to eliminate the need to install Defects4J entirely.

### Getting Help

- **Issues**: Report bugs at [GitHub Issues](https://github.com/universetraveller/catena4j/issues)
- **Documentation**: See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design
- **API Reference**: See [API.md](docs/API.md) for programmatic usage
- **Defects4J Documentation**: [Defects4J Repository](https://github.com/rjust/defects4j)

## Next Steps

- **Understand the Architecture**: Read [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **API Programming**: See [API.md](docs/API.md) for using catena4j as a library
- **Extend the Dataset**: Learn about loaders and commands in the component guides
- **Reproduce Experiments**: Follow instructions in the old repository [CatenaD4J](https://github.com/universetraveller/CatenaD4J)

## References

- **Paper**: Q. Xin, H. Wu, J. Tang, X. Liu, S. Reiss and J. Xuan. "Detecting, Creating, Evaluating, and Understanding Indivisible Multi-Hunk Bugs." FSE 2024.
- **CatenaD4J**: [https://github.com/universetraveller/CatenaD4J](https://github.com/universetraveller/CatenaD4J)
- **Defects4J**: [https://github.com/rjust/defects4j](https://github.com/rjust/defects4j)
