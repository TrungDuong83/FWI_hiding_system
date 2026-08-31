# -*- coding: utf-8 -*-
"""
src/mining/miner.py — PART 3: CORE FWI MINING ENGINE (weighted N-list / SWU-N-list, [21]).

Port từ `fwi_hiding_system_v38 (3).py` (Q9). ĐÃ:
  - Gỡ toàn bộ phụ thuộc Colab (drive.mount, PathManager /content, khối viz seaborn).
  - Áp ĐÚNG 2 fix theo docs/SPEC_PART3_FIX.md:
      FIX A  — compute_tw_optimized: tw = Σ_{i∈T} w(i) / |T|  (BỎ * qty).
      FIX B  — swunl_intersection_optimized: giao theo TIDSET (sửa over-prune k≥3)
               + wiring self.tw_map trong OptimizedWUNTree_v1.
KHÔNG đổi logic mining nào khác (find_fwi_*, tree build, traversal giữ nguyên).

Định nghĩa FWI (khớp bài, [15]):
    tw(T)   = ( Σ_{i∈T} w(i) ) / |T|          # KHÔNG quantity
    W_total = Σ_T tw(T)
    ws(X)   = ( Σ_{T⊇X} tw(T) ) / W_total
    X là FWI  ⟺  ws(X) ≥ ξ
"""

import math
import time
import logging
import traceback
import os
import gc
import collections
from collections import defaultdict
from itertools import combinations
from dataclasses import dataclass
from typing import List, Dict, Any
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

import psutil

# =============================================================================
# CONFIG (PART 2 — chỉ phần engine cần; bỏ PathManager/logging Colab)
# =============================================================================
@dataclass
class OptimizedConfig:
    MAX_MEMORY_USAGE_MB: int = 45000
    BATCH_SIZE: int = 5000
    GC_FREQUENCY: int = 200
    MAX_PATTERN_LENGTH: int = 7
    USE_MULTIPROCESSING: bool = True
    NUM_WORKERS: int = min(4, max(1, mp.cpu_count() - 2))
    PROGRESS_REPORT_INTERVAL: int = 10000

config = OptimizedConfig()


# =============================================================================
# PART 3: CORE FWI MINING ENGINE (ORIGINAL VERSION — chỉ 2 fix + gỡ Colab)
# =============================================================================
class OptimizedWUNNode_v1_Mock:
    def __init__(self, itemset, ws, tids):
        self.itemset = itemset
        self.ws = ws
        self.tids = tids

class MemoryMonitor:
    def __init__(self, max_memory_mb):
        self.max_memory_mb = max_memory_mb
        self.process = psutil.Process(os.getpid())
    def check_memory_usage(self):
        memory_mb = self.process.memory_info().rss / (1024 * 1024)
        if memory_mb > self.max_memory_mb:
            gc.collect()
            if psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024) > self.max_memory_mb:
                raise MemoryError(f"Memory usage ({memory_mb:.1f}MB) exceeds limit ({self.max_memory_mb}MB)")
        return memory_mb

class OptimizedWUNNode_v1:
    __slots__ = ['item_name', 'children', 'pre', 'post', 'weight', 'parent', 'tids']
    def __init__(self, item_name, parent):
        self.item_name, self.parent = item_name, parent; self.children = {}; self.tids = set(); self.pre, self.post, self.weight = -1, -1, 0.0

class OptimizedWUNTree_v1:
    def __init__(self, item_weights):
        self.root = OptimizedWUNNode_v1(None, None); self.node_index = {}; self.item_weights = item_weights; self.node_count = 1; self.memory_monitor = MemoryMonitor(config.MAX_MEMORY_USAGE_MB)
        self.tw_map = {}                                   # FIX B (wiring): tid -> tw(tid)
    def insert_transaction_batch(self, transactions_batch: List[Dict], utilities_batch: List[float], tids_batch: List[str]):
        self.tw_map = dict(zip(tids_batch, utilities_batch))   # FIX B (wiring): utilities_batch = tw_list
        for i, (transaction, utility, tid) in enumerate(zip(transactions_batch, utilities_batch, tids_batch)):
            # Truyền tid (string) vào hàm insert
            self.insert_transaction(transaction, utility, tid)
            if (i + 1) % config.GC_FREQUENCY == 0:
                self.memory_monitor.check_memory_usage()
    def insert_transaction(self, transaction: Dict, utility: float, transaction_id: str): # Chỉ định rõ type
        current = self.root
        for item in transaction.keys():
            if item not in current.children:
                current.children[item] = OptimizedWUNNode_v1(item, current);
                self.node_count += 1
            current = current.children[item];
            current.weight += utility;
            current.tids.add(transaction_id) # Bây giờ transaction_id là "T1", "T2"...
    def build_node_index_optimized(self):
        pre_counter, post_counter = 0, 0
        stack_pre = [self.root]
        while stack_pre:
            node = stack_pre.pop()
            if node.pre == -1: node.pre = pre_counter; pre_counter += 1
            sorted_children = sorted(node.children.keys(), key=lambda x: self.item_weights.get(x, 0), reverse=False)
            for child_item in sorted_children: stack_pre.append(node.children[child_item])
        stack_post1, stack_post2 = [self.root], []
        while stack_post1:
            node = stack_post1.pop(); stack_post2.append(node)
            sorted_children = sorted(node.children.keys(), key=lambda x: self.item_weights.get(x, 0), reverse=True)
            for child_item in sorted_children: stack_post1.append(node.children[child_item])
        while stack_post2:
            node = stack_post2.pop()
            if node.post == -1: node.post = post_counter; post_counter += 1
        all_nodes_q = collections.deque([self.root])
        while all_nodes_q:
            node = all_nodes_q.popleft()
            if node.pre != -1 and node.item_name is not None: self.node_index[node.pre] = node.post
            all_nodes_q.extend(node.children.values())
        return self.node_index
    def get_swun_list_optimized(self, item):
        swun_list, queue = [], collections.deque([self.root])
        while queue:
            node = queue.popleft()
            if node.item_name == item: swun_list.append((node.pre, node.weight, node.tids))
            queue.extend(node.children.values())
        return sorted(swun_list, key=lambda x: x[0])
    def swunl_intersection_optimized(self, swunl_y, swunl_x, ws_y, ws_x, sumtw, min_ws):
        # FIX B — giao theo TIDSET (sửa bug over-prune k≥3 của bản pre/post cũ).
        # tids đã có sẵn trong mỗi entry swunl=(pre, weight, tids); dùng tids + tw_map
        # để tính lại ws đúng cho mọi k. Trả về 1 entry: ws = weight/sumtw, tids = common.
        if not swunl_x or not swunl_y:
            return None
        tids_y = set().union(*(t for _, _, t in swunl_y))
        tids_x = set().union(*(t for _, _, t in swunl_x))
        common = tids_y & tids_x
        if not common:
            return None
        weight = sum(self.tw_map[t] for t in common)      # Σ tw trên giao dịch chứa CẢ hai
        if weight / sumtw < min_ws - 1e-12:               # prune raw + tolerance (KHÔNG round)
            return None
        return [(0, weight, common)]

def compute_tw_optimized(transactions: Dict[str, Dict[str, int]], weights: Dict[str, float]):
    """Tính toán tw, trả về map [tid -> tw]."""
    tw, sumtw = defaultdict(float), 0.0
    transaction_tw_map = {} # Sử dụng map (dict)
    for tid, t in transactions.items(): # Lặp qua items() để lấy cả tid
        s_tk = len(t)
        if s_tk > 0:
            utility = sum(weights.get(item, 0.0) for item in t)   # FIX A — BỎ * qty
            tw_t = utility / s_tk
            sumtw += tw_t
            transaction_tw_map[tid] = tw_t # Lưu tw bằng tid (string)
            for item in t:
                tw[item] += tw_t
        else:
            transaction_tw_map[tid] = 0.0 # Lưu tw bằng tid (string)
    return tw, sumtw, transaction_tw_map # Trả về map

def calculate_ws_from_swunl_fast(swunl, sumtw):
    if not swunl or sumtw == 0: return 0.0
    return sum(weight for _, weight, _ in swunl) / sumtw

class ProgressiveMinor:
    def __init__(self):
        self.patterns_found = 0; self.start_time = time.time()
    def should_continue(self, current_length):
        return current_length < config.MAX_PATTERN_LENGTH
    def report_progress(self):
        self.patterns_found += 1
        if self.patterns_found % config.PROGRESS_REPORT_INTERVAL == 0:
            logging.getLogger(__name__).debug(f"Progress: {self.patterns_found} patterns found.")

def find_fwi_optimized(Prefix, L_k, S_k, tree, sumtw, fwis, seen_patterns, item_order, min_ws, progressive_minor):
    if not progressive_minor.should_continue(len(Prefix)): return
    for i in range(len(L_k) - 1, -1, -1):
        item_i_obj = L_k[i]; Prefix_next = Prefix + item_i_obj['pattern']
        if len(Prefix_next) > config.MAX_PATTERN_LENGTH: continue
        L_next, S_next = [], list(S_k)
        for j in range(i):
            item_j_obj = L_k[j]
            new_swunl = tree.swunl_intersection_optimized(item_i_obj['swunl'], item_j_obj['swunl'], item_i_obj['ws'], item_j_obj['ws'], sumtw, min_ws)
            if new_swunl:
                new_ws = calculate_ws_from_swunl_fast(new_swunl, sumtw)
                if new_ws >= min_ws:
                    new_pattern = sorted(Prefix_next + item_j_obj['pattern']); new_pattern_key = tuple(new_pattern)
                    tids = set().union(*(t for _, _, t in new_swunl))
                    candidate_c = {'pattern': item_j_obj['pattern'], 'ws': new_ws, 'swunl': new_swunl, 'tids': tids}
                    if new_pattern_key not in seen_patterns:
                        fwis.append({'pattern': new_pattern, 'ws': new_ws, 'tids': tids}); seen_patterns.add(new_pattern_key)
                        progressive_minor.report_progress()
                    if abs(new_ws - item_i_obj['ws']) < 1e-9: S_next.append(item_j_obj)
                    else: L_next.append(candidate_c)
        if len(Prefix_next) < config.MAX_PATTERN_LENGTH:
            s_sorted_objs = sorted(S_next, key=lambda obj: item_order.get(obj['pattern'][0]))
            s_sorted_items = [s_obj['pattern'][0] for s_obj in s_sorted_objs]
            l_sorted_objs = sorted(L_next, key=lambda obj: item_order.get(obj['pattern'][0]))
            prefix_next_ws = item_i_obj['ws']
            prefix_next_tids = set().union(*(t for _, _, t in item_i_obj['swunl']))
            if s_sorted_items: find_fwi_same_ws_optimized(Prefix_next, s_sorted_items, prefix_next_ws, prefix_next_tids, fwis, seen_patterns, progressive_minor)
            if l_sorted_objs: find_fwi_optimized(Prefix_next, l_sorted_objs, s_sorted_objs, tree, sumtw, fwis, seen_patterns, item_order, min_ws, progressive_minor)

def find_fwi_same_ws_optimized(Prefix, S, prefix_ws, prefix_tids, fwis, seen_patterns, progressive_minor):
    for r in range(1, len(S) + 1):
        if len(Prefix) + r > config.MAX_PATTERN_LENGTH: continue
        for subset in combinations(S, r):
            new_pattern = sorted(Prefix + list(subset)); new_pattern_key = tuple(new_pattern)
            if new_pattern_key not in seen_patterns:
                fwis.append({'pattern': new_pattern, 'ws': prefix_ws, 'tids': prefix_tids}); seen_patterns.add(new_pattern_key)
                progressive_minor.report_progress()

g_tree, g_swunl_dict, g_ws_dict, g_sumtw, g_min_ws, g_item_order_map, g_item_order_list, g_base_fwis = (None,) * 8

def init_worker(tree, swunl_dict, ws_dict, sumtw, min_ws, item_order_map, item_order_list, base_fwis):
    global g_tree, g_swunl_dict, g_ws_dict, g_sumtw, g_min_ws, g_item_order_map, g_item_order_list, g_base_fwis
    g_tree, g_swunl_dict, g_ws_dict, g_sumtw, g_min_ws, g_item_order_map, g_item_order_list, g_base_fwis = \
        tree, swunl_dict, ws_dict, sumtw, min_ws, item_order_map, item_order_list, base_fwis

def mine_i1_chunk(i1_chunk_indices):
    progressive_minor = ProgressiveMinor()
    fwis = list(g_base_fwis); seen_patterns = {tuple(p['pattern']) for p in fwis}
    initial_fwis_count = len(fwis)
    for item_x_index in i1_chunk_indices:
        item_x = g_item_order_list[item_x_index]
        if not progressive_minor.should_continue(1): break
        Prefix, L, S = [item_x], [], []; ws_x = g_ws_dict.get(item_x, 0)
        for y_index in range(item_x_index):
            item_y = g_item_order_list[y_index]
            swunl_xy = g_tree.swunl_intersection_optimized(g_swunl_dict.get(item_y), g_swunl_dict.get(item_x), g_ws_dict.get(item_y, 0.0), ws_x, g_sumtw, g_min_ws)
            if swunl_xy:
                ws_xy_val = calculate_ws_from_swunl_fast(swunl_xy, g_sumtw)
                if ws_xy_val >= g_min_ws:
                    new_pattern_key = tuple(sorted([item_x, item_y]))
                    if new_pattern_key not in seen_patterns:
                        tids_xy = set().union(*(t for _, _, t in swunl_xy))
                        fwis.append({'pattern': list(new_pattern_key), 'ws': ws_xy_val, 'tids': tids_xy}); seen_patterns.add(new_pattern_key)
                    item_y_obj = {'pattern': [item_y], 'ws': ws_xy_val, 'swunl': swunl_xy}
                    if abs(ws_xy_val - ws_x) < 1e-9: S.append(item_y_obj)
                    else: L.append(item_y_obj)
        s_sorted_objs = sorted(S, key=lambda obj: g_item_order_map.get(obj['pattern'][0]))
        s_sorted_items = [s_obj['pattern'][0] for s_obj in s_sorted_objs]
        l_sorted_objs = sorted(L, key=lambda obj: g_item_order_map.get(obj['pattern'][0]))
        item_x_tids = set().union(*(t for _, _, t in g_swunl_dict.get(item_x,[])))
        if s_sorted_items: find_fwi_same_ws_optimized(Prefix, s_sorted_items, ws_x, item_x_tids, fwis, seen_patterns, progressive_minor)
        if l_sorted_objs: find_fwi_optimized(Prefix, l_sorted_objs, s_sorted_objs, g_tree, g_sumtw, fwis, seen_patterns, g_item_order_map, g_min_ws, progressive_minor)
    return fwis[initial_fwis_count:]

def run_fwi_mining_core(transactions: Dict[str, Dict[str, int]], item_weights: Dict[str, float], min_ws: float) -> List[Dict[str, Any]]:
    logger = logging.getLogger(__name__)
    logger.info(f"Bắt đầu khai phá fwis (phiên bản gốc v5.1) với min_ws = {min_ws:.6f}")
    if not transactions or not item_weights: return []

    # KHỐI MÃ MỚI
    tw, sumtw, transaction_tw_map = compute_tw_optimized(transactions, item_weights) # Sửa 1
    if sumtw == 0: return []

    ws = {item: val / sumtw for item, val in tw.items()}
    I1 = sorted([item for item, w in ws.items() if w >= min_ws], key=ws.get, reverse=True)
    logger.info(f"I1: {len(I1)}") # Sửa 2 (dùng logger)
    item_order_map = {item: i for i, item in enumerate(I1)}

    # Sửa 3: Xử lý giao dịch và giữ lại TIDs
    processed_transactions_map = {}
    for tid, t in transactions.items():
        processed_t = dict(sorted({item: qty for item, qty in t.items() if item in item_order_map}.items(), key=lambda x: item_order_map.get(x[0])))
        if processed_t: # Chỉ thêm nếu giao dịch không rỗng
            processed_transactions_map[tid] = processed_t

    tree = OptimizedWUNTree_v1(item_weights)

    # Sửa 4: Chuẩn bị dữ liệu để đưa TIDs (string) vào cây
    tids_list = list(processed_transactions_map.keys())
    transactions_list = [processed_transactions_map[tid] for tid in tids_list]
    tw_list = [transaction_tw_map[tid] for tid in tids_list]

    # Gọi hàm batch insert đã được sửa đổi
    tree.insert_transaction_batch(transactions_list, tw_list, tids_list)
    tree.build_node_index_optimized()

    swunl_dict = {item: tree.get_swun_list_optimized(item) for item in I1}
    base_fwis = [{'pattern': [item], 'ws': ws[item], 'tids': set.union(*(t for _, _, t in swunl_dict.get(item,[])))} for item in I1]
    final_fwis = list(base_fwis)

    if config.USE_MULTIPROCESSING and config.NUM_WORKERS > 1 and len(I1) > 1:
        logger.info(f"Sử dụng {config.NUM_WORKERS} worker(s) để khai phá...")
        i1_indices = list(range(len(I1)))
        chunk_size = math.ceil(len(i1_indices) / config.NUM_WORKERS)
        chunks = [i1_indices[i:i + chunk_size] for i in range(0, len(i1_indices), chunk_size)]
        init_args = (tree, swunl_dict, ws, sumtw, min_ws, item_order_map, I1, base_fwis)
        with ProcessPoolExecutor(max_workers=config.NUM_WORKERS, initializer=init_worker, initargs=init_args) as executor:
            futures = [executor.submit(mine_i1_chunk, chunk) for chunk in chunks]
            for future in as_completed(futures):
                try:
                    chunk_results = future.result(); final_fwis.extend(chunk_results)
                except Exception as e: logger.error(f"A worker process failed: {e}\n{traceback.format_exc()}")
    else:
        logger.info("Chạy khai phá ở chế độ đơn luồng...")
        init_args = (tree, swunl_dict, ws, sumtw, min_ws, item_order_map, I1, base_fwis)
        init_worker(*init_args)
        single_chunk_results = mine_i1_chunk(list(range(len(I1))))
        final_fwis.extend(single_chunk_results)

    logger.info(f"Khai phá hoàn tất. Tìm thấy {len(final_fwis)} fwis.")
    formatted_fwis = []
    for p in final_fwis:
        formatted_fwis.append(OptimizedWUNNode_v1_Mock(p['pattern'], p['ws'], p.get('tids', set())))

    return formatted_fwis, tree, transaction_tw_map


# =============================================================================
# ADAPTER — API gọn quanh engine (KHÔNG đổi logic PART 3)
# =============================================================================
def mine_fwi(D_sets: Dict[str, set], W: Dict[str, float], xi: float, use_mp: bool = False):
    """
    Mine FWI từ D dạng {tid: set(item)} với weights W tại ngưỡng xi.
    Trả về: list các node (.itemset, .ws, .tids). qty bị bỏ (FWI, tw=Σw/|T|) nên
    dựng {item:1} là đủ. Mặc định đơn luồng (use_mp=False) cho test tất định/nhanh.
    """
    trans = {tid: {i: 1 for i in items} for tid, items in D_sets.items()}
    saved = config.USE_MULTIPROCESSING
    config.USE_MULTIPROCESSING = use_mp
    try:
        result = run_fwi_mining_core(trans, W, xi)
    finally:
        config.USE_MULTIPROCESSING = saved
    if not result:                      # core trả [] khi rỗng / sumtw==0
        return []
    nodes, _tree, _tw_map = result
    return nodes

def fwi_itemsets(nodes) -> set:
    """list node -> set(frozenset(itemset)) để so khớp tập FWI."""
    return {frozenset(n.itemset) for n in nodes}


if __name__ == "__main__":
    # Smoke: golden running example (ξ=0.55) → 9 tập FWI.
    W = {"A": 0.9, "B": 0.4, "C": 0.7, "D": 0.5, "E": 0.2}
    D = {"T1": set("ACDE"), "T2": set("BCE"), "T3": set("ACD"),
         "T4": set("ABCE"), "T5": set("ACDE"), "T6": set("BDE")}
    nodes = mine_fwi(D, W, 0.55)
    got = {"".join(sorted(n.itemset)) for n in nodes}
    exp = {"A", "C", "D", "E", "AC", "AD", "CD", "CE", "ACD"}
    print(f"[miner smoke] #FWI={len(got)} match={got == exp} diff={got ^ exp}")
