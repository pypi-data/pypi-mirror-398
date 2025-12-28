# MarkUs Exam Matcher

## Installation
It is recommended to use a [virtual environment](https://docs.python.org/3/library/venv.html) to install this package, as it contains many pinned runtime dependencies.

### Production Installation (Recommended)
To install the production version of the package, run the following command in the console:

```console
$ pip install markus-exam-matcher --extra-index-url https://download.pytorch.org/whl/cpu
```

### Latest Development Installation

To install the latest development version of the package, run the following command in the console:

```console
$ pip install git+https://github.com/MarkUsProject/markus-exam-matcher.git --extra-index-url https://download.pytorch.org/whl/cpu
```

### Branch Installation
To install the version specified by a particular branch (when permissions are granted), run the following command in the
console:
```console
$ pip install git+https://github.com/MarkUsProject/markus-exam-matcher.git@branch_name --extra-index-url https://download.pytorch.org/whl/cpu
```

### Commit Hash Installation
To install the version specified by a specific commit, the commit hash can be used by running the following command in
the console:
```console
$ pip install git+https://github.com/MarkUsProject/markus-exam-matcher.git@commit_hash --extra-index-url https://download.pytorch.org/whl/cpu
```
## Usage
This package works under the assumption that the characters to be detected are surrounded by boxes that are placed
side-by-side. An example image with this format is displayed below:

![Text](./examples/student_info_num.jpg?raw=true)

Below is a sample usage that generates a prediction from the file shown above.
```console
$ python3 -m markus_exam_matcher --char_type digit char examples/student_info_num.jpg
0001250981
```

## Developers

1. First, clone this repository.
2. Open a terminal in this repo, and create a new [virtual environment](https://docs.python.org/3/library/venv.html).
3. Run `pip install -e ".[dev]"` to install the dependencies.
4. Then run `pre-commit install` to install the pre-commit hooks (for automatically formatting and checking your code on each commit).
