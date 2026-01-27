#include <cuda_runtime.h>
#include <stdio.h>

#define M 1024
#define K 1024
#define N 1024

#define TILE_M 128
#define TILE_N 128

__global__ void matmul_tile_kernel(
    const float* A,
    const float* B,
    float* C,
    int tile_row,
    int tile_col
) {
    int row = tile_row * TILE_M + blockIdx.y * blockDim.y + threadIdx.y;
    int col = tile_col * TILE_N + blockIdx.x * blockDim.x + threadIdx.x;

    if (row < M && col < N) {
        float sum = 0.0f;
        for (int i = 0; i < K; i++) {
            sum += A[row * K + i] * B[i * N + col];
        }
        C[row * N + col] = sum;
    }
}

int main() {
    size_t sizeA = M * K * sizeof(float);
    size_t sizeB = K * N * sizeof(float);
    size_t sizeC = M * N * sizeof(float);

    float *A, *B, *C;
    float *dA, *dB, *dC;

    A = (float*)malloc(sizeA);
    B = (float*)malloc(sizeB);
    C = (float*)malloc(sizeC);

    for (int i = 0; i < M * K; i++) A[i] = 1.0f;
    for (int i = 0; i < K * N; i++) B[i] = 1.0f;

    cudaMalloc(&dA, sizeA);
    cudaMalloc(&dB, sizeB);
    cudaMalloc(&dC, sizeC);

    cudaMemcpy(dA, A, sizeA, cudaMemcpyHostToDevice);
    cudaMemcpy(dB, B, sizeB, cudaMemcpyHostToDevice);

    dim3 block(16, 16);

    int num_tile_rows = (M + TILE_M - 1) / TILE_M;
    int num_tile_cols = (N + TILE_N - 1) / TILE_N;

    for (int tr = 0; tr < num_tile_rows; tr++) {
        for (int tc = 0; tc < num_tile_cols; tc++) {

            dim3 grid(
                (TILE_N + block.x - 1) / block.x,
                (TILE_M + block.y - 1) / block.y
            );

            matmul_tile_kernel<<<grid, block>>>(
                dA, dB, dC, tr, tc
            );
        }
    }

    cudaDeviceSynchronize();

    cudaMemcpy(C, dC, sizeC, cudaMemcpyDeviceToHost);

    cudaFree(dA);
    cudaFree(dB);
    cudaFree(dC);
    free(A);
    free(B);
    free(C);

    return 0;
}
