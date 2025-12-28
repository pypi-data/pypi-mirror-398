import os
from lite_taskman import TaskMan

def scan_node(path):
    """Returns a list of sub-nodes if it's a directory, else None."""
    if os.path.isdir(path):
        try:
            return [os.path.join(path, f) for f in os.listdir(path)]
        except PermissionError:
            return []
    return None

def demo_process():
    # We use a custom progress callback to see the dynamic total count growing
    tman = TaskMan(max_workers=4)
    
    # Initial seeds
    root_path = os.path.expanduser(r"D:\tmp") # Scan home directory
    tman.add(scan_node, root_path, _tm_name="root")
    
    print(f"Starting recursive scan from: {root_path}")
    
    file_count = 0
    dir_count = 0

    with tman:
        # process() keeps yielding as long as new subdirs are added
        for r in tman.process():
            if r.error: continue
            
            nodes = r.result
            if nodes is not None: # It was a directory
                dir_count += 1
                for node in nodes:
                    # Dynamically add sub-items back to TaskMan
                    tman.add(scan_node, node, _tm_name=os.path.basename(node))
            else: # It was a file
                file_count += 1
                
            # Optional: Limit the demo so it doesn't run forever
            if dir_count > 50: 
                print("--- Limit reached for demo ---")
                break

    print(f"\nScan Finished!")
    print(f"Total Folders Processed: {dir_count}")
    print(f"Total Files Found: {file_count}")

if __name__ == '__main__':
    demo_process()