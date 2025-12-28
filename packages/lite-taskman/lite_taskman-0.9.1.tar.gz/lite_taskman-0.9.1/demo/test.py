# -*- coding: utf-8 -*-
import time
import re
import requests as http
from lite_taskman import TaskMan

def slow_task(x, y, kw=None):
    time.sleep(0.1)
    return f"Result: {x} {y} {kw}"

def fetch_page(url):
    # 为第二个 demo 定义的简单包装
    return http.get(url, timeout=5)

def verify_demo1():
    print("\n=== Running Demo 1: Minimalist Mode ===")
    tman = TaskMan(max_workers=4)
    
    # 添加任务
    tman.add(slow_task, 'hello', 1, kw=3)
    tman.add(slow_task, 'world', 'x', kw=[15])
    tman.add(slow_task, 25, {'a': 1})
    
    # 获取结果 (exec 模式)
    results = [r.result for r in tman.exec()]
    
    for i, res in enumerate(results, 1):
        print(f"Task {i} output: {res}")

def verify_demo2():
    print("\n=== Running Demo 2: Incremental Mode ===")
    BASE_URL = "https://quotes.toscrape.com"
    
    tman = TaskMan(max_workers=3)
    tman.add(fetch_page, BASE_URL, _tm_name="Initial-Page")
    
    total_quotes = 0
    with tman:
        for r in tman.process():
            if r.error:
                print(f"Error at {r.name}: {r.error}")
                continue
                
            html = r.result.text
            quotes = re.findall(r'<span class="text".*?>(.*?)</span>', html)
            total_quotes += len(quotes)
            print(f"[{r.name}] Found {len(quotes)} quotes.")
            
            # 增量发现：查找“下一页”
            if mch := re.search(r'<li class="next">\s*<a href="(.*?)">', html):
                next_url = BASE_URL + mch.group(1)
                # 动态追加任务
                tman.add(fetch_page, next_url, _tm_name=f"Page-{next_url.split('/')[-2] or 'Next'}")

    print(f"Incremental processing finished. Total quotes: {total_quotes}")

if __name__ == "__main__":
    verify_demo1()
    verify_demo2()