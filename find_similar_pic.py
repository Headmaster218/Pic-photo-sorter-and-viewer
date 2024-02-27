import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
import imagehash
from PIL import Image
from collections import defaultdict
from threading import Thread

class ImageGraph:
    def __init__(self):
        self.edges = defaultdict(list)

    def add_edge(self, img1, img2):
        self.edges[img1].append(img2)
        self.edges[img2].append(img1)

    def find_connected_components(self):
        visited = set()
        components = []

        def dfs(img, component):
            visited.add(img)
            component.append(img)
            for neighbor in self.edges[img]:
                if neighbor not in visited:
                    dfs(neighbor, component)

        for img in self.edges:
            if img not in visited:
                component = []
                dfs(img, component)
                components.append(component)
        return components

def generate_hash(directory, hash_func, update_progress):
    hashes = {}
    for root, dirs, filenames in os.walk(directory):
        total = len(filenames)
        for i, filename in enumerate(filenames):
            if filename.lower().endswith(('jpg', 'jpeg', 'png')):
                try:
                    img_path = os.path.join(root, filename)
                    with Image.open(img_path) as img:
                        hash = hash_func(img)
                        hashes[img_path] = str(hash)
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
            update_progress(i + 1, total)
    return hashes

def compare_hashes(hashes, threshold=5):
    graph = ImageGraph()
    keys = list(hashes.keys())
    for i in range(len(keys)):
        for j in range(i+1, len(keys)):
            if imagehash.hex_to_hash(hashes[keys[i]]) - imagehash.hex_to_hash(hashes[keys[j]]) < threshold:
                graph.add_edge(keys[i], keys[j])
    return graph.find_connected_components()

class ImageHashGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("相似图片查找器")
        
        self.hash_method = tk.StringVar()
        self.directory = ""

        ttk.Label(root, text="选择哈希方法:").pack(pady=10)
        self.create_hash_method_buttons()
        ttk.Button(root, text="选择目录", command=self.select_directory).pack(pady=5)
        
        self.selected_directory_label = ttk.Label(root, text="未选择目录")
        self.selected_directory_label.pack(pady=5)
        
        self.start_button = ttk.Button(root, text="开始", command=self.start_processing)
        self.start_button.pack(pady=20)
        
        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)

    def create_hash_method_buttons(self):
        hash_methods = {
            "平均哈希 (适用于快速比较)": imagehash.average_hash,
            "感知哈希 (对细微变化敏感)": imagehash.phash,
            "差异哈希 (高效识别相似图片),推荐": imagehash.dhash,
            "小波哈希 (细节层面的相似度)": imagehash.whash,
        }
        for text, method in hash_methods.items():
            ttk.Radiobutton(self.root, text=text, variable=self.hash_method, value=text).pack(anchor=tk.W)
        self.hash_method.set("差异哈希 (高效识别相似图片),推荐")

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.directory = directory
            self.selected_directory_label.config(text=f"已选择目录: {directory}")
        else:
            messagebox.showinfo("信息", "未选择目录。")

    def update_progress(self, current, total):
        self.progress['value'] = (current / total) * 100
        self.root.update_idletasks()

    def process_images(self):
        self.start_button["state"] = "disabled"
        hash_funcs = {
            "平均哈希 (适用于快速比较)": imagehash.average_hash,
            "感知哈希 (对细微变化敏感)": imagehash.phash,
            "差异哈希 (高效识别相似图片),推荐": imagehash.dhash,
            "小波哈希 (细节层面的相似度)": imagehash.whash,
        }
        hash_func = hash_funcs[self.hash_method.get()]
        
        hashes = generate_hash(self.directory, hash_func, self.update_progress)
        similar_images_groups = compare_hashes(hashes)
        
        result_file = f"jsondata/相似照片数据之{self.hash_method.get().split()[0]}.json"
        with open(result_file, "w",encoding='utf-8') as f:
            json.dump(similar_images_groups, f, indent=4, ensure_ascii=False)
        
        messagebox.showinfo("完成", f"找到 {len(similar_images_groups)} 组相似图片。结果已保存至 {result_file}。退出本应用，继续使用手动选择并删除相似照片")
        self.progress['value'] = 0
        self.start_button["state"] = "normal"

    def start_processing(self):
        if not self.directory:
            messagebox.showerror("错误", "请先选择一个目录。")
            return
        Thread(target=self.process_images).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageHashGUI(root)
    root.mainloop()
