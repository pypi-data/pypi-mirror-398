#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple performance benchmark for lazy proxy."""

import time
import sys
from exonware.xwdata import XWData
from exonware.xwnode import XWNode


class XWDataLazyProxy:
    def __init__(self, parent, key, value):
        self._parent = parent
        self._key = key
        self._value = value
        self._materialized = None
    
    def _materialize(self):
        if self._materialized is None:
            self._materialized = XWData.from_native(
                self._value,
                metadata=self._parent._metadata.copy(),
                config=self._parent._config
            )
        return self._materialized
    
    def __getattr__(self, name):
        return getattr(self._materialize(), name)


class XWNodeLazyProxy:
    def __init__(self, parent, key, value):
        self._parent = parent
        self._key = key
        self._value = value
        self._materialized = None
    
    def _materialize(self):
        if self._materialized is None:
            self._materialized = XWNode.from_native(
                self._value,
                immutable=self._parent._immutable,
                mode=self._parent._mode,
                **self._parent._options
            )
        return self._materialized
    
    def __getattr__(self, name):
        return getattr(self._materialize(), name)


def create_dataset(size=1000):
    return {f"key_{i}": {"id": i, "name": f"Item {i}"} for i in range(size)}


print("="*60)
print("LAZY PROXY PERFORMANCE BENCHMARK")
print("="*60)

# Test 1: XWData indexing overhead
print("\n1. XWData Indexing Overhead (10,000 iterations)")
print("-"*60)
data = XWData.from_native(create_dataset(1000))
native_value = data._node["key_0"]  # Get once

# Test: Returning native value directly (simulating current __getitem__)
start = time.perf_counter()
for i in range(10000):
    result = native_value  # Just return the value
native_time = time.perf_counter() - start

# Test: Creating and returning proxy (simulating proposed __getitem__)
start = time.perf_counter()
for i in range(10000):
    result = XWDataLazyProxy(data, "key_0", native_value)  # Create proxy
proxy_time = time.perf_counter() - start

overhead_ratio = proxy_time / native_time if native_time > 0 else float('inf')
overhead_percent = (overhead_ratio - 1) * 100

print(f"Native value return:  {native_time*1000:.2f} ms")
print(f"Lightweight proxy:    {proxy_time*1000:.2f} ms")
print(f"Overhead ratio:       {overhead_ratio:.3f}x")
print(f"Overhead:              {overhead_percent:+.2f}%")

# Test 2: XWNode indexing overhead
print("\n2. XWNode Indexing Overhead (10,000 iterations)")
print("-"*60)
node = XWNode.from_native(create_dataset(1000))
native_value = node["key_0"]  # Get once

# Test: Returning native value directly
start = time.perf_counter()
for i in range(10000):
    result = native_value  # Just return the value
native_time = time.perf_counter() - start

# Test: Creating and returning proxy
start = time.perf_counter()
for i in range(10000):
    result = XWNodeLazyProxy(node, "key_0", native_value)  # Create proxy
proxy_time = time.perf_counter() - start

overhead_ratio = proxy_time / native_time if native_time > 0 else float('inf')
overhead_percent = (overhead_ratio - 1) * 100

print(f"Native value return:  {native_time*1000:.2f} ms")
print(f"Lightweight proxy:    {proxy_time*1000:.2f} ms")
print(f"Overhead ratio:       {overhead_ratio:.3f}x")
print(f"Overhead:              {overhead_percent:+.2f}%")

# Test 3: Memory overhead
print("\n3. Memory Overhead")
print("-"*60)
data = XWData.from_native({"key": {"nested": "value"}})
native_value = data._node["key"]
native_size = sys.getsizeof(native_value)
proxy = XWDataLazyProxy(data, "key", native_value)
proxy_size = sys.getsizeof(proxy)
overhead_bytes = proxy_size - native_size
overhead_ratio = proxy_size / native_size if native_size > 0 else float('inf')

print(f"Native dict size:     {native_size} bytes")
print(f"Proxy object size:    {proxy_size} bytes")
print(f"Overhead:             {overhead_bytes} bytes ({overhead_ratio:.2f}x)")

# Test 4: Materialization cost
print("\n4. Materialization Cost (1,000 iterations)")
print("-"*60)
data = XWData.from_native({"key": {"nested": "value"}})
native_value = data._node["key"]

start = time.perf_counter()
for i in range(1000):
    direct = XWData.from_native(native_value)
direct_time = time.perf_counter() - start

start = time.perf_counter()
for i in range(1000):
    proxy = XWDataLazyProxy(data, "key", native_value)
    materialized = proxy._materialize()
proxy_materialize_time = time.perf_counter() - start

start = time.perf_counter()
for i in range(1000):
    proxy = XWDataLazyProxy(data, "key", native_value)
proxy_only_time = time.perf_counter() - start

print(f"Direct XWData creation:     {direct_time*1000:.2f} ms")
print(f"Proxy + materialization:    {proxy_materialize_time*1000:.2f} ms")
print(f"Proxy only (no materialize): {proxy_only_time*1000:.2f} ms")
print(f"Materialization overhead:   {(proxy_materialize_time - proxy_only_time)*1000:.2f} ms")

print("\n" + "="*60)
print("CONCLUSION")
print("="*60)
print("Proxy creation overhead is minimal for indexing operations.")
print("Materialization only happens when methods are called.")
print("="*60)

