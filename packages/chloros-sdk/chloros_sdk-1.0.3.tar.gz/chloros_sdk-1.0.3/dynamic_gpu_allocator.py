"""
Dynamic GPU Allocator for Ray Pipeline
Automatically reallocates GPU resources as threads complete for maximum performance
"""

import threading
import time
from typing import Dict, List, Optional
from enum import Enum

class PipelineStage(Enum):
    EARLY = "early"      # All 4 threads active
    MID_EARLY = "mid_early"  # Thread 1 complete, 2,3,4 active
    MID_LATE = "mid_late"   # Threads 1,2 complete, 3,4 active  
    LATE = "late"        # Only thread 3 or 4 active
    COMPLETE = "complete"

class DynamicGPUAllocator:
    """Manages dynamic GPU allocation as pipeline threads complete"""
    
    def __init__(self, total_gpu_memory: float = 1.0):
        self.total_gpu_memory = total_gpu_memory
        self.active_threads = set([1, 2, 3, 4])
        self.completed_threads = set()
        self.current_stage = PipelineStage.EARLY
        self.lock = threading.Lock()
        
        # Track Ray task futures for dynamic reallocation
        self.thread_futures = {1: [], 2: [], 3: [], 4: []}
        self.reallocation_callbacks = {}
        
        print(f"[DYNAMIC-GPU] 🚀 Dynamic GPU Allocator initialized with {total_gpu_memory} GPU")
    
    def get_gpu_allocation(self, thread_id: int) -> float:
        """Get current GPU allocation for a thread based on pipeline stage"""
        with self.lock:
            stage = self.current_stage
            
            # Dynamic GPU allocation based on active threads
            if stage == PipelineStage.EARLY:
                # All threads active - conservative allocation
                allocations = {
                    1: 0.25,  # Target detection
                    2: 0.30,  # Calibration computation  
                    3: 0.60,  # Calibration application
                    4: 0.40   # Export processing
                }
                
            elif stage == PipelineStage.MID_EARLY:
                # Thread 1 done - redistribute its GPU to remaining threads
                allocations = {
                    2: 0.35,  # +0.05 from Thread 1
                    3: 0.70,  # +0.10 from Thread 1  
                    4: 0.50   # +0.10 from Thread 1
                }
                
            elif stage == PipelineStage.MID_LATE:
                # Threads 1,2 done - more GPU for 3,4
                allocations = {
                    3: 0.85,  # Maximum GPU for calibration (most intensive)
                    4: 0.65   # More GPU for export
                }
                
            elif stage == PipelineStage.LATE:
                # Only one thread active - maximum GPU
                if 3 in self.active_threads:
                    allocations = {3: 1.0}  # Full GPU for calibration
                elif 4 in self.active_threads:
                    allocations = {4: 1.0}  # Full GPU for export
                else:
                    allocations = {}
                    
            else:  # COMPLETE
                allocations = {}
            
            allocation = allocations.get(thread_id, 0.0)
            
            try:
                print(f"[DYNAMIC-GPU] Thread {thread_id} allocation: {allocation:.2f} GPU ({stage.value} stage)")
            except:
                pass  # Silent failure if print fails
            return allocation
    
    def mark_thread_complete(self, thread_id: int):
        """Mark a thread as complete and trigger GPU reallocation"""
        with self.lock:
            if thread_id in self.active_threads:
                self.active_threads.remove(thread_id)
                self.completed_threads.add(thread_id)
                
                old_stage = self.current_stage
                self._update_pipeline_stage()
                
                print(f"[DYNAMIC-GPU] 🏁 Thread {thread_id} completed")
                print(f"[DYNAMIC-GPU] 📊 Active threads: {sorted(self.active_threads)}")
                print(f"[DYNAMIC-GPU] 📈 Stage transition: {old_stage.value} → {self.current_stage.value}")
                
                # Trigger reallocation for remaining active threads
                if self.current_stage != old_stage:
                    self._trigger_gpu_reallocation()
    
    def _update_pipeline_stage(self):
        """Update pipeline stage based on active threads"""
        active_count = len(self.active_threads)
        
        if active_count == 4:
            self.current_stage = PipelineStage.EARLY
        elif active_count == 3 and 1 not in self.active_threads:
            self.current_stage = PipelineStage.MID_EARLY
        elif active_count == 2 and {3, 4}.issubset(self.active_threads):
            self.current_stage = PipelineStage.MID_LATE
        elif active_count == 1:
            self.current_stage = PipelineStage.LATE
        else:
            self.current_stage = PipelineStage.COMPLETE
    
    def _trigger_gpu_reallocation(self):
        """Trigger GPU reallocation for active threads"""
        print(f"[DYNAMIC-GPU] 🔄 Triggering GPU reallocation for active threads: {sorted(self.active_threads)}")
        
        # Notify threads about new GPU allocations
        for thread_id in self.active_threads:
            if thread_id in self.reallocation_callbacks:
                try:
                    callback = self.reallocation_callbacks[thread_id]
                    new_allocation = self.get_gpu_allocation(thread_id)
                    callback(thread_id, new_allocation)
                except Exception as e:
                    print(f"[DYNAMIC-GPU] ❌ Error in reallocation callback for thread {thread_id}: {e}")
    
    def register_reallocation_callback(self, thread_id: int, callback):
        """Register callback for GPU reallocation notifications"""
        self.reallocation_callbacks[thread_id] = callback
        print(f"[DYNAMIC-GPU] 📋 Registered reallocation callback for thread {thread_id}")
    
    def get_optimal_batch_size(self, thread_id: int) -> int:
        """Get optimal batch size based on current GPU allocation"""
        base_sizes = {1: 8, 2: 6, 3: 10, 4: 15}
        gpu_allocation = self.get_gpu_allocation(thread_id)
        
        # Scale batch size based on GPU allocation
        if gpu_allocation >= 0.8:
            multiplier = 2.0  # Double batch size with high GPU
        elif gpu_allocation >= 0.6:
            multiplier = 1.5  # 50% larger batches
        elif gpu_allocation >= 0.4:
            multiplier = 1.2  # 20% larger batches
        else:
            multiplier = 1.0  # Standard batch size
        
        optimal_size = int(base_sizes.get(thread_id, 10) * multiplier)
        try:
            print(f"[DYNAMIC-GPU] Thread {thread_id} optimal batch size: {optimal_size} (GPU: {gpu_allocation:.2f})")
        except:
            pass  # Silent failure if print fails
        
        return optimal_size
    
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        with self.lock:
            total_allocated = sum(self.get_gpu_allocation(tid) for tid in self.active_threads)
            
            return {
                'stage': self.current_stage.value,
                'active_threads': sorted(list(self.active_threads)),
                'completed_threads': sorted(list(self.completed_threads)),
                'total_gpu_allocated': round(total_allocated, 2),
                'gpu_utilization': round(total_allocated / self.total_gpu_memory * 100, 1)
            }
    
    def print_status(self):
        """Print current allocator status"""
        try:
            metrics = self.get_performance_metrics()
            
            print(f"\n[DYNAMIC-GPU] 📊 CURRENT STATUS:")
            print(f"[DYNAMIC-GPU] Stage: {metrics['stage']}")
            print(f"[DYNAMIC-GPU] Active threads: {metrics['active_threads']}")
            print(f"[DYNAMIC-GPU] Completed threads: {metrics['completed_threads']}")
            print(f"[DYNAMIC-GPU] GPU utilization: {metrics['gpu_utilization']}%")
            
            for thread_id in metrics['active_threads']:
                try:
                    allocation = self.get_gpu_allocation(thread_id)
                    batch_size = self.get_optimal_batch_size(thread_id)
                    print(f"[DYNAMIC-GPU]   Thread {thread_id}: {allocation:.2f} GPU, batch size {batch_size}")
                except Exception as thread_error:
                    print(f"[DYNAMIC-GPU]   Thread {thread_id}: Status unavailable ({thread_error})")
        except Exception as e:
            print(f"[DYNAMIC-GPU] ❌ Error printing status: {e}")


# Global allocator instance
_gpu_allocator = None

def get_gpu_allocator(reset_for_test=False) -> DynamicGPUAllocator:
    """Get the global GPU allocator instance"""
    global _gpu_allocator
    if _gpu_allocator is None or reset_for_test:
        print(f"[GPU-ALLOCATOR] 🔍 Initializing GPU allocator (reset_for_test={reset_for_test})...")
        
        # Detect GPU memory with timeout protection
        try:
            print(f"[GPU-ALLOCATOR] 🔍 Attempting to import PyTorch...")
            
            # CRITICAL FIX: Import PyTorch with timeout to avoid hanging on no-GPU systems
            import signal
            import sys
            
            def timeout_handler(signum, frame):
                raise TimeoutError("PyTorch import timed out")
            
            # Set timeout for import (only on Unix-like systems)
            if sys.platform != 'win32':
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(3)  # 3 second timeout
            
            try:
                import torch
                if sys.platform != 'win32':
                    signal.alarm(0)  # Cancel timeout
                print(f"[GPU-ALLOCATOR] 🔍 PyTorch imported successfully")
            except TimeoutError:
                print(f"[GPU-ALLOCATOR] ⚠️ PyTorch import timed out - using CPU-only mode")
                _gpu_allocator = DynamicGPUAllocator(total_gpu_memory=0.0)
                return _gpu_allocator
            
            print(f"[GPU-ALLOCATOR] 🔍 Checking CUDA availability...")
            
            # CRITICAL FIX: Check CUDA with timeout protection
            cuda_available = False
            try:
                # Simple check with implicit timeout via exception handling
                cuda_available = torch.cuda.is_available()
            except Exception as cuda_error:
                print(f"[GPU-ALLOCATOR] ⚠️ CUDA check failed: {cuda_error}")
                cuda_available = False
            
            if cuda_available:
                print(f"[GPU-ALLOCATOR] 🔍 CUDA is available, getting device properties...")
                try:
                    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                    gpu_units = min(1.0, gpu_memory / 4.0)  # 1.0 GPU unit per 4GB
                    device_name = torch.cuda.get_device_name(0)
                    print(f"[GPU-ALLOCATOR] 🎯 Detected GPU: {device_name} ({gpu_memory:.1f}GB)")
                    print(f"[GPU-ALLOCATOR] 🔍 Creating DynamicGPUAllocator with {gpu_units} GPU units...")
                    _gpu_allocator = DynamicGPUAllocator(total_gpu_memory=gpu_units)
                    print(f"[GPU-ALLOCATOR] ✅ GPU allocator created successfully")
                except Exception as gpu_error:
                    print(f"[GPU-ALLOCATOR] ⚠️ GPU property detection failed: {gpu_error}, using CPU-only mode")
                    _gpu_allocator = DynamicGPUAllocator(total_gpu_memory=0.0)
            else:
                print(f"[GPU-ALLOCATOR] ⚠️ CUDA not available, using CPU-only mode")
                _gpu_allocator = DynamicGPUAllocator(total_gpu_memory=0.0)
        except ImportError as e:
            print(f"[GPU-ALLOCATOR] ⚠️ PyTorch not available ({e}), using CPU-only mode")
            _gpu_allocator = DynamicGPUAllocator(total_gpu_memory=0.0)
        except Exception as e:
            print(f"[GPU-ALLOCATOR] ⚠️ GPU detection failed ({e}), using CPU-only mode")
            import traceback
            print(f"[GPU-ALLOCATOR] 📋 Exception traceback: {traceback.format_exc()}")
            _gpu_allocator = DynamicGPUAllocator(total_gpu_memory=0.0)
    else:
        print(f"[GPU-ALLOCATOR] 🔍 Using existing GPU allocator instance")
    
    return _gpu_allocator

def mark_thread_complete(thread_id: int):
    """Mark a thread as complete (convenience function)"""
    allocator = get_gpu_allocator()
    allocator.mark_thread_complete(thread_id)

def get_dynamic_gpu_allocation(thread_id: int) -> float:
    """Get current GPU allocation for a thread (convenience function)"""
    allocator = get_gpu_allocator()
    return allocator.get_gpu_allocation(thread_id)

def get_dynamic_batch_size(thread_id: int) -> int:
    """Get optimal batch size for a thread (convenience function)"""
    allocator = get_gpu_allocator()
    return allocator.get_optimal_batch_size(thread_id)

def print_gpu_status():
    """Print current GPU allocation status (convenience function)"""
    allocator = get_gpu_allocator()
    allocator.print_status()


# Test function
if __name__ == "__main__":
    print("🧪 Testing Dynamic GPU Allocator")
    
    allocator = DynamicGPUAllocator()
    
    print("\n1️⃣ Initial state (all threads active):")
    allocator.print_status()
    
    print("\n2️⃣ Thread 1 completes:")
    allocator.mark_thread_complete(1)
    allocator.print_status()
    
    print("\n3️⃣ Thread 2 completes:")
    allocator.mark_thread_complete(2)
    allocator.print_status()
    
    print("\n4️⃣ Thread 3 completes:")
    allocator.mark_thread_complete(3)
    allocator.print_status()
    
    print("\n✅ Dynamic GPU allocation test completed!")
