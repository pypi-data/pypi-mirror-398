
#pragma once

struct slmCUDAParams {
    // --- optical/scalar precomputes ---

    float k2pi_over_lam_f;    // 2π / (λ f)
    float pi_wl_f2;           // π * w_l * f^2 (or whatever you meant)
    float inv_n_slm;          // 1 / N_SLM
    float inv_aperture_cubed; // 1 / (slm_h * slm_pitch / 2)^3

    float slm_pitch;
    int n_slm;
    int slm_w;
    int slm_h;
    float x_lim;
    float y_lim;
};

__constant__ slmCUDAParams g_slm;