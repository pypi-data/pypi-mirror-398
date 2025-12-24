#include "slimcuda_params.cuh"
#include <math_constants.h>

#define PI CUDART_PI
#define TWO_PI CUDART_PI * 2

extern "C"
{
    __device__ void warpReduce(volatile float* par_sum_ptr, int t) {
        par_sum_ptr[t] += par_sum_ptr[t + 32];
        par_sum_ptr[t] += par_sum_ptr[t + 16];
        par_sum_ptr[t] += par_sum_ptr[t + 8];
        par_sum_ptr[t] += par_sum_ptr[t + 4];
        par_sum_ptr[t] += par_sum_ptr[t + 2];
        par_sum_ptr[t] += par_sum_ptr[t + 1];
    }

    __global__ void p_phase_arb(const float* x, const float* y,
                                const float* z, const float* l,
                                const float* th, const float* ir,
                                const int* beammode, const float* slm_x,
                                const float* slm_y, int n_pts,
                                float* p_phase) {
        int idx = threadIdx.x + blockDim.x * blockIdx.x;
        if (idx < g_slm.n_slm) {
            float phi = atan2(slm_y[idx], slm_x[idx]) + PI;
            float xr, yr;
            for (int i = 0; i < n_pts; i++) {
                p_phase[i * g_slm.n_slm + idx] =
                    g_slm.k2pi_over_lam_f * (slm_x[idx] * x[i] + slm_y[idx] * y[i]) +
                    g_slm.pi_wl_f2 * z[i] *
                        (slm_x[idx] * slm_x[idx] + slm_y[idx] * slm_y[idx]);
                switch (beammode[i]) {
                case 1:
                    p_phase[i * g_slm.n_slm + idx] += l[i] * phi;
                    break;
                case 2:
                    xr = slm_x[idx] * cos(th[i]) + slm_y[idx] * sin(th[i]);
                    yr = slm_y[idx] * cos(th[i]) - slm_x[idx] * sin(th[i]);
                    p_phase[i * g_slm.n_slm + idx] +=
                        (g_slm.inv_aperture_cubed * (xr * xr * xr + yr * yr * yr) / ir[i] * 2 + 1) *
                        PI;
                }
            }
        }
    }

    __global__ void wgs_arb(const float* x, const float* y,
                            const float* z, const float* l,
                            const float* th, const float* ir,
                            const int* beammode,
                            int n_pts, const float* w, const float* gs,
                            const float* p_phase, float* phase_final) {
        int idx = threadIdx.x + blockDim.x * blockIdx.x;
        if (idx < g_slm.n_slm) {
            float r_real = 0.0;
            float r_imag = 0.0;
            for (int i = 0; i < n_pts; i++) {
                r_real += w[i] * cosf(p_phase[i * g_slm.n_slm + idx] + gs[i]);
                r_imag += w[i] * sinf(p_phase[i * g_slm.n_slm + idx] + gs[i]);
            }
            // float density_tmp = sqrt(r_real * r_real + r_img * r_img);
            // r_real = r_real / density_tmp;
            // r_img = r_img / density_tmp;
            phase_final[idx] = atan2(r_imag, r_real) + PI;
        }
    }

    __global__ void rs_arb(const float* x, const float* y,
                           const float* z, const float* l,
                           const float* th, const float* ir,
                           const int* beammode,
                           int n_pts, const float* bw,
                           const float* rand, const float* p_phase,
                           float* phase_final) {
        int idx = threadIdx.x + blockDim.x * blockIdx.x;
        if (idx < g_slm.n_slm) {
            float r_real = 0.0;
            float r_imag = 0.0;
            for (int i = 0; i < n_pts; i++) {
                r_real += bw[i] * cosf(p_phase[i * g_slm.n_slm + idx] + rand[i]);
                r_imag += bw[i] * sinf(p_phase[i * g_slm.n_slm + idx] + rand[i]);
            }
            // float density_tmp = w[2] * w[2] * sqrt(r_real * r_real + r_img * r_img);
            // r_real = r_real / density_tmp;
            // r_img = r_img / density_tmp;
            phase_final[idx] = atan2(r_imag, r_real) + PI;
        }
    }

    __global__ void upd_pix(const float* phase, const int* slm_coords,
                            const float* wfc, unsigned char* pixel) {
        int idx = threadIdx.x + blockDim.x * blockIdx.x;
        int pix_id;
        if (idx < g_slm.n_slm) {
            pix_id = slm_coords[idx];
            int temp = phase[idx] / TWO_PI * 256 + wfc[idx];
            pixel[pix_id] = temp % 256;
        }
    }

    __global__ void upd_pix_simp(const float* phase, unsigned char* pixel) {
        int idx = threadIdx.x + blockDim.x * blockIdx.x;
        if (idx < g_slm.n_slm) {
            int temp = phase[idx] / TWO_PI * 256;
            pixel[idx] = temp % 256;
        }
    }

    __global__ void copy_to_2d_apr(const float* phase1d, const int* slm_coords,
                                   float* phase2d, int h1, int w1,
                                   int h2, int w2) {
        int id1d = threadIdx.x + blockDim.x * blockIdx.x;
        int id2d, row1, col1, row2, col2;
        if (id1d < g_slm.n_slm) {
            row1 = slm_coords[id1d] / w1;
            col1 = slm_coords[id1d] % w1;
            row2 = row1 + (h2 - h1) / 2;
            col2 = col1 + (w2 - w1) / 2;
            id2d = row2 * w2 + col2;
            phase2d[id2d] = phase1d[id1d];
        }
    }

    __global__ void copy_to_2d_noapr(const float* phase1d, float* phase2d,
                                     int h1, int w1, int h2, int w2) {
        int id1d = threadIdx.x + blockDim.x * blockIdx.x;
        int id2d, row1, col1, row2, col2;
        if (id1d < g_slm.n_slm) {
            row1 = id1d / w1;
            col1 = id1d % w1;
            row2 = row1 + (h2 - h1) / 2;
            col2 = col1 + (w2 - w1) / 2;
            id2d = row2 * w2 + col2;
            phase2d[id2d] = phase1d[id1d];
        }
    }
    __global__ void efield_reduce_l1(const float* gpu_phase,
                                     const float* pt_phase,
                                     float* epart_real,
                                     float* epart_img,
                                     int n_pts, int grid_dim,
                                     const float* x,
                                     const float* y,
                                     const float* z,
                                     const float* l,
                                     const float* th,
                                     const float* ir,
                                     const int* beammode) {
        __shared__ float sdata[4096];
        __shared__ float tdata[4096];
        int tid = threadIdx.x;
        int i;
        int gridSize = blockDim.x * 2 * gridDim.x;
        for (int j = 0; j < n_pts; j++) {
            sdata[tid] = 0.0;
            tdata[tid] = 0.0;
            i = blockIdx.x * (blockDim.x * 2) + tid;
            while (i < g_slm.n_slm) {
                sdata[tid] += cos(gpu_phase[i] - pt_phase[i + j * g_slm.n_slm]);
                tdata[tid] += sin(gpu_phase[i] - pt_phase[i + j * g_slm.n_slm]);
                if (i + blockDim.x < g_slm.n_slm) {
                    sdata[tid] += cos(gpu_phase[i + blockDim.x] -
                                      pt_phase[i + blockDim.x + j * g_slm.n_slm]);
                    tdata[tid] += sin(gpu_phase[i + blockDim.x] -
                                      pt_phase[i + blockDim.x + j * g_slm.n_slm]);
                }
                i += gridSize;
            }
            __syncthreads();

            // if (tid < 512) {
            //     sdata[tid] += sdata[tid + 512];
            //     tdata[tid] += tdata[tid + 512];
            // }
            // __syncthreads();
            // if (tid < 256) {
            //     sdata[tid] += sdata[tid + 256];
            //     tdata[tid] += tdata[tid + 256];
            // }
            // __syncthreads();
            if (tid < 128) {
                sdata[tid] += sdata[tid + 128];
                tdata[tid] += tdata[tid + 128];
            }
            __syncthreads();
            if (tid < 64) {
                sdata[tid] += sdata[tid + 64];
                tdata[tid] += tdata[tid + 64];
            }
            __syncthreads();

            if (tid < 32) {
                warpReduce(sdata, tid);
                warpReduce(tdata, tid);
            }
            if (tid == 0) {
                epart_real[blockIdx.x + j * grid_dim] = sdata[0];
                epart_img[blockIdx.x + j * grid_dim] = tdata[0];
            }
            __syncthreads();
        }
    }

    __global__ void efield_reduce_l2(const float* epart_real,
                                     const float* epart_img,
                                     int grid_dim,
                                     float* e_abs,
                                     float* gs_phase,
                                     float* wgts) {
        __shared__ float sdata[4096];
        __shared__ float tdata[4096];
        int tid = threadIdx.x;
        int i;
        int gridSize = blockDim.x * 2;
        int j = blockIdx.x;

        sdata[tid] = 0.0;
        tdata[tid] = 0.0;
        i = tid;
        while (i < grid_dim) {
            sdata[tid] += epart_real[i + j * grid_dim];
            tdata[tid] += epart_img[i + j * grid_dim];
            if (i + blockDim.x < grid_dim) {
                sdata[tid] += epart_real[i + blockDim.x + j * grid_dim];
                tdata[tid] += epart_img[i + blockDim.x + j * grid_dim];
            }
            i += gridSize;
        }
        __syncthreads();

        // if (tid < 512) {
        //     sdata[tid] += sdata[tid + 512];
        //     tdata[tid] += tdata[tid + 512];
        // }
        // __syncthreads();
        // if (tid < 256) {
        //     sdata[tid] += sdata[tid + 256];
        //     tdata[tid] += tdata[tid + 256];
        // }
        // __syncthreads();
        if (tid < 128) {
            sdata[tid] += sdata[tid + 128];
            tdata[tid] += tdata[tid + 128];
        }
        __syncthreads();
        if (tid < 64) {
            sdata[tid] += sdata[tid + 64];
            tdata[tid] += tdata[tid + 64];
        }
        __syncthreads();

        if (tid < 32) {
            warpReduce(sdata, tid);
            warpReduce(tdata, tid);
        }
        if (tid == 0) {
            float e_real = g_slm.inv_n_slm * sdata[0];
            float e_imag = g_slm.inv_n_slm * tdata[0];
            float abs_temp = hypotf(e_real, e_imag);
            e_abs[j] = abs_temp;
            gs_phase[j] = atan2f(tdata[0], sdata[0]);
            wgts[j] /= abs_temp;
        }
        __syncthreads();
    }
}