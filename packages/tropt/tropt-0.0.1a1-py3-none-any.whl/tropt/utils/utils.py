import torch
import gc
import inspect
from torch import nn

# def print_gpu_memory_deep_scan(top_k=10):
#     """
#     Scans ALL tensors with scope awareness.
#     1. Maps named variables to tensors, keeping track of Scope and Name separately.
#     2. Uses GC to find 'Anonymous' tensors (activations/gradients).
#     3. Prints a table with: Size | Shape | Scope | Variable Name.
#     """
    
#     # 1. Map ID -> List of (Scope, Name)
#     named_ids = set()
#     # Dictionary to store aliases: oid -> list of (scope, var_name)
#     name_map = {} 

#     def register_obj(obj, scope, name):
#         if torch.is_tensor(obj) and obj.is_cuda:
#             oid = id(obj)
#             named_ids.add(oid)
#             if oid not in name_map: name_map[oid] = []
#             name_map[oid].append((scope, name))
            
#         elif isinstance(obj, nn.Module):
#             # Recursively register model parameters
#             for n, p in obj.named_parameters():
#                 register_obj(p, scope, f"{name}.{n}")
#             for n, b in obj.named_buffers():
#                 register_obj(b, scope, f"{name}.{n}")

#     # Scan Stack Frames (looks at every function in the call stack)
#     # We slice [1:] to skip the current 'print_gpu_memory_deep_scan' frame
#     for frame_info in inspect.stack()[1:]:
#         func_name = frame_info.function
#         for name, val in frame_info.frame.f_locals.items():
#             if not name.startswith('__'):
#                 register_obj(val, func_name, name)

#     # Scan Globals
#     for name, val in globals().items():
#         if not name.startswith('__'):
#             register_obj(val, "global", name)

#     # 2. Scan ALL Tensors via GC
#     named_tensors = []
#     anon_tensors = []
    
#     total_named_mem = 0
#     total_anon_mem = 0

#     for obj in gc.get_objects():
#         try:
#             if torch.is_tensor(obj) and obj.is_cuda:
#                 mem = obj.element_size() * obj.nelement()
#                 oid = id(obj)
#                 shape_str = str(tuple(obj.shape))
                
#                 if oid in named_ids:
#                     total_named_mem += mem
#                     # Add an entry for EVERY alias this tensor has
#                     for scope, name in name_map[oid]:
#                         named_tensors.append((mem, shape_str, scope, name))
#                 else:
#                     total_anon_mem += mem
#                     anon_tensors.append((mem, shape_str, obj.dtype))
#         except:
#             pass

#     # 3. Print Output
#     print(f"\n{'='*30} GPU Memory & Scopes {'='*30}")
    
#     # --- Top Named Variables ---
#     print(f"{'Memory (MB)':<12} | {'Shape':<20} | {'Scope':<20} | {'Variable Name'}")
#     print("-" * 85)
    
#     # Sort by memory size
#     named_sorted = sorted(named_tensors, key=lambda x: x[0], reverse=True)
    
#     for mem, shape, scope, name in named_sorted[:top_k]:
#         print(f"{mem/1024**2:<12.2f} | {shape:<20} | {scope:<20} | {name}")
    
#     # --- Top Anonymous ---
#     if anon_tensors:
#         print(f"\n{'-'*25} Anonymous (Backward Graph/Internal) {'-'*25}")
#         anon_sorted = sorted(anon_tensors, key=lambda x: x[0], reverse=True)
#         for mem, shape, dtype in anon_sorted[:top_k]:
#             print(f"{mem/1024**2:<12.2f} | {shape:<20} | {'<internal>':<20} | {dtype}")

#     # Totals
#     print(f"\n{'-'*85}")
#     print(f"Named:     {total_named_mem/1024**2:8.2f} MB")
#     print(f"Anonymous: {total_anon_mem/1024**2:8.2f} MB (Activations/ Gradients / Orphans)")
#     print(f"Total:     {(total_named_mem + total_anon_mem)/1024**2:8.2f} MB")
#     print(f"{'='*85}\n")


# import torch
# import gc
# import inspect
# from torch import nn

# def print_gpu_memory_deep_scan(top_k=10):
#     """
#     1. Recursively hunts for tensors inside lists, dicts, and modules.
#     2. Maps found tensors to variable names (e.g., 'batch[0]').
#     3. Uses GC to find any remaining 'Anonymous' leaks.
#     """
    
#     # Track tensor ID -> List of (Scope, Name)
#     name_map = {} 
#     # Track visited containers to prevent infinite recursion (cycles)
#     visited_objs = set()

#     def register_obj(obj, scope, name):
#         oid = id(obj)
#         if oid in visited_objs: return
#         visited_objs.add(oid)

#         if torch.is_tensor(obj):
#             if obj.is_cuda:
#                 if oid not in name_map: name_map[oid] = []
#                 name_map[oid].append((scope, name))
                
#         elif isinstance(obj, (list, tuple)):
#             for i, item in enumerate(obj):
#                 register_obj(item, scope, f"{name}[{i}]")
                
#         elif isinstance(obj, dict):
#             for k, v in obj.items():
#                 register_obj(v, scope, f"{name}[{repr(k)}]")

#         elif isinstance(obj, nn.Module):
#             # Recurse into model but don't expand every single list inside it
#             # to keep names clean (e.g., just 'model.layer1.weight')
#             for n, p in obj.named_parameters():
#                 register_obj(p, scope, f"{name}.{n}")
#             for n, b in obj.named_buffers():
#                 register_obj(b, scope, f"{name}.{n}")

#     # 1. Scan Stack Frames
#     # Skip current frame [1:]
#     for frame_info in inspect.stack()[1:]:
#         func_name = frame_info.function
#         for name, val in frame_info.frame.f_locals.items():
#             if not name.startswith('__'):
#                 # We create a new visited set for each root variable
#                 # so we can explore different paths to the same object
#                 visited_objs = set() 
#                 register_obj(val, func_name, name)

#     # 2. Scan Globals
#     for name, val in globals().items():
#         if not name.startswith('__'):
#             visited_objs = set()
#             register_obj(val, "global", name)

#     # 3. Match with GC
#     named_tensors = []
#     anon_tensors = []
    
#     total_named_mem = 0
#     total_anon_mem = 0
#     named_ids = set(name_map.keys())

#     for obj in gc.get_objects():
#         try:
#             if torch.is_tensor(obj) and obj.is_cuda:
#                 mem = obj.element_size() * obj.nelement()
#                 oid = id(obj)
#                 shape_str = str(tuple(obj.shape))
                
#                 if oid in named_ids:
#                     total_named_mem += mem
#                     for scope, name in name_map[oid]:
#                         named_tensors.append((mem, shape_str, scope, name))
#                 else:
#                     total_anon_mem += mem
#                     anon_tensors.append((mem, shape_str, obj.dtype))
#         except:
#             pass

#     # 4. Print
#     print(f"\n{'='*35} GPU Memory & Containers {'='*35}")
#     print(f"{'Memory (MB)':<12} | {'Shape':<20} | {'Scope':<15} | {'Variable Name'}")
#     print("-" * 90)
    
#     named_sorted = sorted(named_tensors, key=lambda x: x[0], reverse=True)
#     for mem, shape, scope, name in named_sorted[:top_k]:
#         print(f"{mem/1024**2:<12.2f} | {shape:<20} | {scope:<15} | {name}")
    
#     if anon_tensors:
#         print(f"\n{'-'*30} Anonymous / Backward Graph {'-'*30}")
#         anon_sorted = sorted(anon_tensors, key=lambda x: x[0], reverse=True)
#         for mem, shape, dtype in anon_sorted[:top_k]:
#             print(f"{mem/1024**2:<12.2f} | {shape:<20} | {'<internal>':<15} | {dtype}")

#     print(f"\n{'-'*90}")
#     print(f"Named:     {total_named_mem/1024**2:8.2f} MB")
#     print(f"Anonymous: {total_anon_mem/1024**2:8.2f} MB")
#     print(f"Total:     {(total_named_mem + total_anon_mem)/1024**2:8.2f} MB")
#     print(f"{'='*90}\n")


import torch
import gc
import inspect
from torch import nn

def print_gpu_memory_deep_scan(top_k=10):
    """
    1. Recursively hunts for tensors inside lists, dicts, and modules.
    2. Groups aliases: If the same tensor is 'x' in main and 'y' in func, 
       it appears ONCE with names combined.
    """
    
    # Map: oid -> list of (scope, name)
    name_map = {} 
    visited_objs = set()

    def register_obj(obj, scope, name):
        oid = id(obj)
        if oid in visited_objs: return
        visited_objs.add(oid)

        if torch.is_tensor(obj):
            if obj.is_cuda:
                if oid not in name_map: name_map[oid] = []
                # Avoid adding exact duplicates
                if (scope, name) not in name_map[oid]:
                    name_map[oid].append((scope, name))
                
        elif isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                register_obj(item, scope, f"{name}[{i}]")
                
        elif isinstance(obj, dict):
            for k, v in obj.items():
                register_obj(v, scope, f"{name}[{repr(k)}]")

        elif isinstance(obj, nn.Module):
            for n, p in obj.named_parameters():
                register_obj(p, scope, f"{name}.{n}")
            for n, b in obj.named_buffers():
                register_obj(b, scope, f"{name}.{n}")

    # 1. Scan Stack
    for frame_info in inspect.stack()[1:]:
        func_name = frame_info.function
        for name, val in frame_info.frame.f_locals.items():
            if not name.startswith('__'):
                visited_objs = set() 
                register_obj(val, func_name, name)

    # 2. Scan Globals
    for name, val in globals().items():
        if not name.startswith('__'):
            visited_objs = set()
            register_obj(val, "global", name)

    # 3. Match with GC & Deduplicate
    unique_tensors = []
    anon_tensors = []
    
    total_named_mem = 0
    total_anon_mem = 0
    named_ids = set(name_map.keys())

    for obj in gc.get_objects():
        try:
            if torch.is_tensor(obj) and obj.is_cuda:
                mem = obj.element_size() * obj.nelement()
                oid = id(obj)
                shape_str = str(tuple(obj.shape))
                
                if oid in named_ids:
                    total_named_mem += mem
                    # Combine all aliases into one string
                    aliases = [f"{n} ({s})" for s, n in name_map[oid]]
                    # Taking top 2 aliases to keep table clean, plus count
                    alias_str = ", ".join(aliases[:2])
                    if len(aliases) > 2: alias_str += f" +{len(aliases)-2} others"
                    
                    unique_tensors.append((mem, shape_str, alias_str))
                else:
                    total_anon_mem += mem
                    anon_tensors.append((mem, shape_str, obj.dtype))
        except:
            pass

    # 4. Print
    print(f"\n{'='*35} GPU Memory (Deduped) {'='*35}")
    print(f"{'Memory (MB)':<12} | {'Shape':<20} | {'Variable Names (Scopes)'}")
    print("-" * 90)
    
    # Sort by size
    named_sorted = sorted(unique_tensors, key=lambda x: x[0], reverse=True)
    for mem, shape, names in named_sorted[:top_k]:
        print(f"{mem/1024**2:<12.2f} | {shape:<20} | {names}")
    
    if anon_tensors:
        print(f"\n{'-'*30} Anonymous / Backward Graph {'-'*30}")
        anon_sorted = sorted(anon_tensors, key=lambda x: x[0], reverse=True)
        for mem, shape, dtype in anon_sorted[:top_k]:
            print(f"{mem/1024**2:<12.2f} | {shape:<20} | {dtype}")

    print(f"\n{'-'*90}")
    print(f"Named:     {total_named_mem/1024**2:8.2f} MB")
    print(f"Anonymous: {total_anon_mem/1024**2:8.2f} MB")
    print(f"Total:     {(total_named_mem + total_anon_mem)/1024**2:8.2f} MB")
    print(f"{'='*90}\n")

# -----------------------------
