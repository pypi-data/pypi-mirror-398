# lite-taskman 🚀

English version | [中文版](./README_zh.md)

`lite-taskman` is an ultra-lightweight (~100 lines of code) thread pool management tool for Python, dedicated to providing a delightful development experience. It is specifically engineered for **concurrent refactoring of sequential code**, **dynamic task incrementation**, and **real-time progress feedback**.

Far from the complexity of the native `ThreadPoolExecutor`, it supports injecting tasks on the fly and offers an intuitive way to retrieve results, helping you achieve a smooth shift from single-threaded to multi-threaded execution.

---

## ✨ Key Features

In concurrent programming, the mental burden of complexity is often the enemy of Python newcomers. `lite-taskman` condenses powerful functionality into about 100 lines of source code to bring you:

* **A Smooth Refactoring Experience**: No need to reconstruct core logic. With simple API replacement, you can elevate legacy sequential code to parallel execution instantly, reaping the performance dividends of concurrency.
* **Intuitive Control**: Break free from complex `Future` object management. Whether you need results in their original order or want to consume them via streaming, the logic is designed to align perfectly with a developer's natural thinking.
* **Delightful Dynamics**: As natural as "adding more rice to your bowl while eating." It supports injecting new tasks at any time during execution, making incremental scenarios like web crawling and recursive scanning more elegant than ever.
* **Ultra-lightweight Feedback**: Zero dependencies and millisecond-level responsiveness. Combined with real-time progress callbacks, it ensures the status of every task is always under your control.

---

## 📦 Installation

```bash
pip install lite-taskman

```

---

## 💡 Common Patterns

### 1. Minimalist Mode: Smooth Shift to Parallel

Leverage multi-core performance by simply changing function calls to `add()`.

```python
# Original sequential logic.
# Total execution time = time(make_soymilk) + time(buy_buns) + time(make_dumplings)
# soymilk = make_soymilk(soy, milk)
# buns = buy_buns(2)
# dumplings = make_dumplings(8, type='pork')

# Transform sequential code into parallel execution with just three lines—ultra-smooth!
from lite_taskman import TaskMan

tman = TaskMan() # Initialize thread pool
tman.add(make_soymilk, soy, milk) # Add task: Simply pass the function as the first argument...
tman.add(buy_buns, 2) # and keep other arguments exactly as they were
tman.add(make_dumplings, 8, type='pork') # Use proprietary parameters for task name, weight, and extra data (see docs)

# exec() returns a result list strictly matching the add() sequence
# Total execution time = max(time(make_soymilk), time(buy_buns), time(make_dumplings))
soymilk, buns, dumplings = [r.result for r in tman.exec()]
```

### 2. Incremental Mode: "Add While Running"

Perfect for crawlers: If you discover a new URL while fetching the first page, just `add()` it immediately.

```python
with TaskMan() as tman:
    tman.add(fetch_url, "http://example.com/page1")
    for r in tman.process():
        # process() is a generator; the loop continues as long as new tasks are added
        new_urls = parse_links(r.result)
        for url in new_urls:
            tman.add(fetch_url, url) # Dynamic addition

```

### 3. Pool Reuse

If you have multiple batches of tasks but want to avoid the overhead of repeatedly creating and destroying thread pools, use `all()`.

```python
with TaskMan(max_workers=4) as tman:
    # Batch 1
    tman.add(make_soymilk, soy, milk)
    tman.add(buy_bun, money)
    soymilk, bun = (t.result for t in tman.all()) # Blocks to get results without closing the pool
    
    # Batch 2 (Reuses the 4 existing worker threads)
    for i in range(8): tman.add(make_dumpling, i)
    dumplings = (t.result for t in tman.all()) 

```

---

## 🛠️ API Reference

### Core Methods

| Method | Description | Use Case |
| --- | --- | --- |
| `add(...)` | Submits a task. Supports custom names, item counts, and extra data. Execution starts immediately. | Base for all scenarios. |
| `process()` | **Generator**. Yields results in **completion order**. Supports dynamic `add()`. | Crawlers, recursion, real-time processing. |
| `all()` | **Blocking**. Waits for all tasks and returns results sorted by **addition order**. | Batch processing with pool reuse. |
| `exec()` | **Blocking**. Equivalent to `with` + `all()`. Auto-shuts down the pool after completion. | One-off parallel tasks, simplest call. |
| `shutdown()` | Immediately shuts down the pool and clears the task queue. | Manual resource management. |

### `TaskMan.add()` Parameters

To avoid naming conflicts, tool-specific parameters are prefixed with `_tm_`:

* `_tm_name`: Task name (defaults to function name) for identification and callbacks.
* `_tm_batch_size`: Task weight (i.e., the number of items within a task). E.g., if one page contains 20 records, set this to 20.
* `_tm_extra`: Metadata pass-through. Returned as-is in `Result.extra`.

### Progress Callback `progress_cb`

```python
def my_cb(name, task_done, task_all, batch_done, batch_all, elapsed_sec):
    # name: Current task name
    # task_done/task_all: Progress based on task count
    # batch_done/batch_all: Progress based on workload (batch_size)
    # elapsed_sec(float): Cumulative elapsed time in seconds

```

---

## 📄 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

**Author**: Rocks Wang ([rockswang@foxmail.com](mailto:rockswang@foxmail.com))