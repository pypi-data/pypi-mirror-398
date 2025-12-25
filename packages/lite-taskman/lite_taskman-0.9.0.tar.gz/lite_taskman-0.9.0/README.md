# lite-taskman 🚀

`lite-taskman` is an extremely lightweight (~100 lines of code) yet powerful thread pool management tool for Python. It is specifically designed for scenarios requiring **dynamic task addition**, **real-time progress feedback**, and **streamed result processing**.

Unlike the native `ThreadPoolExecutor`, `lite-taskman` allows you to continuously inject new tasks into the pool while consuming results—making it the perfect fit for web crawlers, recursive directory scanning, and multi-stage data processing.

## ✨ Key Features

* **Dynamic Incremental Execution**: Add new tasks on the fly during processing until the entire task stream is exhausted.
* **Minimalist API**: Offers both `exec()` for one-stop execution and `process()` as a streaming generator.
* **Progress Tracking**: Built-in flexible callbacks supporting dual-dimension statistics: "Task Count" and "Business Batch Weight."
* **Thread Safety**: Enforces task management within the main thread to effectively avoid multi-threading race conditions.
* **Zero Dependencies**: Pure Python implementation using only the standard library.

---

## 📦 Installation

```bash
pip install lite-taskman

```

---

## 💡 Quick Start

### 1. Batch Tasks (Minimalist Mode)

Use `exec()` when you have a set of known tasks to process in parallel and need the results in a single list.

```python
import os
from lite_taskman import TaskMan

def get_file_size(path):
    return os.stat(path).st_size

# Use context manager to automatically handle thread pool lifecycle
tman = TaskMan(max_workers=4)
files = ["file1.txt", "file2.txt", "file3.txt"]

for f in files:
    # _tm_extra carries arbitrary metadata returned with the result
    tman.add(get_file_size, f, _tm_name=f, _tm_extra=f"path/{f}")

# exec() blocks until all tasks are complete and returns a list of Results
results = tman.exec()

for r in results:
    if r.error:
        print(f"FAILED: {r.name}, Error: {r.error}")
    else:
        print(f"SUCCESS: {r.name}, Size: {r.result} bytes")

```

### 2. Incremental Iteration (Crawler/Recursive Mode)

The most powerful feature: "Add while running."

```python
import requests
import re
from lite_taskman import TaskMan

BASE_URL = "https://quotes.toscrape.com"

def fetch_page(url):
    return requests.get(url, timeout=5).text

tman = TaskMan(max_workers=3)
tman.add(fetch_page, BASE_URL, _tm_name="Page-1")

with tman:
    # process() is a generator; it won't stop as long as new tasks are being added
    for r in tman.process():
        if r.error: continue
        
        # Parse data
        html = r.result
        quotes = re.findall(r'<span class="text".*?>(.*?)</span>', html)
        print(f"[{r.name}] Found {len(quotes)} quotes.")

        # Task Discovery: Find next page and add it to the pool dynamically
        next_match = re.search(r'<li class="next">\s*<a href="(.*?)">', html)
        if next_match:
            next_url = BASE_URL + next_match.group(1)
            tman.add(fetch_page, next_url, _tm_name="NextPage")

```

---

## 🛠️ API Reference

### `TaskMan.add()` Parameters

To avoid conflicts with the target function's arguments, all tool-specific parameters are prefixed with `_tm_`:

| Parameter | Description | Default |
| --- | --- | --- |
| `_tm_name` | Task identifier name. | Function name |
| `_tm_batch_size` | Numerical weight for the task (e.g., number of items in a page). Used in progress callbacks. | 1 |
| `_tm_extra` | Transparent data pass-through. Any object returned in `Result.extra`. | None |

### Progress Callback `progress_cb`

You can define a custom callback to log progress or refresh a UI.

```python
def my_cb(name, task_done, task_all, batch_done, batch_all, elapsed_sec):
    # name: Name of the task just completed
    # task_done/task_all: Progress based on task count
    # batch_done/batch_all: Progress based on business weight (batch_size)
    # elapsed_sec: Total elapsed time in seconds
    pass

```

---

## 📄 License

This project is licensed under the [MIT License](https://www.google.com/search?q=LICENSE).

**Author**: Rocks Wang ([rockswang@foxmail.com](mailto:rockswang@foxmail.com))

