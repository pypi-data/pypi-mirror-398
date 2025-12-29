#include <vector>
#include <iostream>
#include <omp.h>
#include <cstdint>

extern "C" {

    typedef void (*TraceCallback)(uint32_t, uint32_t);
    static TraceCallback g_profiler_callback = nullptr;

    void init_profiler_cb(size_t callback_addr) {
        g_profiler_callback = (TraceCallback)callback_addr;
        std::cout << "C++ Profiler Initialized with callback at " << callback_addr << std::endl;
    }

    void mat_mul_cpu(const float* a, const float* b, float* c, int M, int N, int K) {
        if (g_profiler_callback) g_profiler_callback(1, 0); // Start ID 1
        
        // A is MxK, B is KxN, C is MxN
        
        #pragma omp parallel for collapse(2)
        for (int i = 0; i < M; ++i) {
            for (int j = 0; j < N; ++j) {
                float sum = 0.0f;
                // Naive implementation - can be optimized with blocking/SIMD
                for (int k = 0; k < K; ++k) {
                    sum += a[i * K + k] * b[k * N + j];
                }
                c[i * N + j] = sum;
            }
        }
        
        if (g_profiler_callback) g_profiler_callback(1, 1); // End ID 1
    }

}
