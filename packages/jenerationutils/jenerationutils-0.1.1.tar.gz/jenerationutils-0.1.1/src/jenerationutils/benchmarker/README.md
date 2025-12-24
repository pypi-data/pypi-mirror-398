# README.md for 'benchmarker' package

# Benchmarker

A lightweight utility for measuring performance metrics in GenAI workflows.

## Overview

The `Benchmarker` class tracks how long your model inferences take and can calculate throughput metrics like **Tokens Per Second** or **Images Per Second**. It can be used as a function wrapper, a decorator, or a context manager.

## Usage

### 1. Function Wrapper
Use this when you want to wrap a single function call and get the results back immediately.

    from benchmarker import Benchmarker

    # Wrap the generator call
    result = Benchmarker.measure_execution_time(your_function, prompt="A space cat")

    print(f"Time taken: {result['execution_time']}")
    print(f"Image Data: {result['output']}")

### 2. Context Manager (The 'With' Block)
Use this to time a specific block of code within a larger script. This is the most flexible approach.

    with Benchmarker() as benchmarker:
        image = model.generate(prompt)
    
    print(f"Inference took: {benchmarker.execution_time} seconds")

### 3. Calculating Throughput
GenAI projects often require tokens-per-second or similar metrics.

    duration = 2.5  # seconds
    tokens_generated = 100
    
    tps = Benchmarker.calculate_throughput(duration, tokens_generated)
    print(f"Throughput: {tps} tokens/sec")

