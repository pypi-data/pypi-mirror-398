import cupy as cp
import numpy as np
from time import time, sleep
import math
# cuda-python (which required pywin32 in windows, ICYMI)
# from cuda.bindings import runtime as cudart
from OpenGL.GL import *
# import glfw
# from cuda_gl_map import CudaOpenGLMappedArray
import matplotlib.pyplot as plt
import cv2
from .slimcuda_toolkit import *
from importlib.resources import files
from pathlib import Path
# -------------------------------------------------------------------------------------------------------------------- #
# class SLiM-CUDA
# Copyright 2022- Jun-Lei Wang [jwangXTS]
# SLM phase pattern generation using CuPy and OpenGL
#
# -------------------------------------------------------------------------------------------------------------------- #


def _get_kernel_path(filename: str) -> str:
    """
    Return absolute path to a kernel file in slimcuda/build.
    Works both from source (editable install) and from wheel.
    """
    return str(files("slimcuda").joinpath("build", filename))


# CUDA kernel codes
# with open(file_path_complete('./kernels/slimcuda_og.cu'), 'r') as file:
#     cuda_sourcecode = file.read()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(BASE_DIR, "build")
GPUCORECOUNT, GPUSMCOUNT, GPUCCMAJOR, GPUCCMINOR = get_cuda_core_count()
GPUCC = GPUCCMAJOR * 10 + GPUCCMINOR

SUPPORTED_SMS = {75, 86, 89, 120}  # Turing 7.5, Ampere 8.6, Ada 8.9, Blackwell 12.0
BANNER_ON_PTX = r"""
[SLiM-CUDA] You are using the PUBLIC (PTX) kernel set shipped on PyPI.
           This PTX build prioritizes compatibility and includes legacy kernels.
           For optimized performance on your GPU, a collaborator-only fatbin build exists.
           Contact the author for support.  (Set SLIMCUDA_BANNER=0 to silence this message.)
""".strip("\n")


def _banner_enabled(explicit: bool | None = None) -> bool:
    """
    Priority:
      1) explicit argument
      2) env var SLIMCUDA_BANNER (0/false/off disables)
      3) default True
    """
    if explicit is not None:
        return bool(explicit)
    v = os.getenv("SLIMCUDA_BANNER", "").strip().lower()
    if v in {"0", "false", "off", "no"}:
        return False
    return True


def load_kernels(show_banner: bool | None = None,):
    ptx_path = Path(_get_kernel_path("slimcuda_og.ptx"))
    bin_path = Path(_get_kernel_path("slimcuda_opt.fatbin"))

    if not ptx_path.exists() and not bin_path.exists():
        raise FileNotFoundError(
            f"No kernel binaries found. Expected at least one of:\n"
            f"  {bin_path}\n"
            f"  {ptx_path}"
        )

    banner_ok = _banner_enabled(show_banner)

    # --- Collaborator path: fatbin exists => try it first (regardless of SM list)
    if bin_path.exists():
        try:
            print(f"[SLiM-CUDA] Found fatbin kernels. Attempting to load (GPU SM {GPUCC}).")
            module = cp.RawModule(path=str(bin_path))
            module.compile()

            # Messaging policy:
            # - If SM is not in your supported list, they should contact you anyway.
            if GPUCC not in SUPPORTED_SMS:
                print(
                    f"[SLiM-CUDA] Note: GPU SM {GPUCC} is not in the supported list for this fatbin.\n"
                    f"           If you see issues, contact the author for a tailored build."
                )
            else:
                print(f"[SLiM-CUDA] Loaded optimized fatbin kernels for SM {GPUCC}.")

            return module

        except Exception as e:
            # If fatbin exists but fails to load, fall back to PTX (public path)
            print(
                "[SLiM-CUDA] Failed to load fatbin kernels; falling back to PTX.\n"
                f"           Reason: {type(e).__name__}: {e}"
            )

    # --- Public path: PTX (legacy/obsoleted kernels) always available on PyPI
    if not ptx_path.exists():
        raise FileNotFoundError(
            f"[SLiM-CUDA] PTX not found at {ptx_path} and fatbin load failed/unavailable."
        )

    module = cp.RawModule(path=str(ptx_path))
    module.compile()

    if banner_ok:
        print(BANNER_ON_PTX)

    print(f"[SLiM-CUDA] Loaded legacy PTX kernels (GPU SM {GPUCC}).")
    return module


class SlimCuda_base:
    def __init__(self, wavelength_nm=1064, slm_pitch=8.0, focal_mm=3.333, apertured=False, beam_rad: int = None,
                 gs_iter=15, slm_w=1920, slm_h=1080, sim_scalefactor=1.0, wavefront_compensation=False):
        self.wavelength = wavelength_nm * 0.001
        self.f = focal_mm * 1000.0
        self.slm_pitch = slm_pitch
        self.apertured = False  # depreciating this property.
        self.sim_scalefactor = sim_scalefactor if sim_scalefactor >= 1.0 else 1.0
        self.slm_w = slm_w
        self.slm_h = slm_h

        if not beam_rad:
            self.beam_rad = self.slm_h * self.slm_pitch / 2
        else:
            self.beam_rad = beam_rad * 1000

        self.gs_iter = gs_iter

        xlim = (self.slm_w - 1.0) / 2
        ylim = (self.slm_h - 1.0) / 2
        xc, yc = cp.meshgrid(cp.linspace(-xlim, xlim, self.slm_w, dtype=cp.float32),
                             cp.linspace(-ylim, ylim, self.slm_h, dtype=cp.float32))
        xc = cp.reshape(xc * self.slm_pitch, -1)
        yc = cp.reshape(yc * self.slm_pitch, -1)
        if self.apertured:
            rc2 = xc ** 2 + yc ** 2
            coords = cp.where(rc2 <= self.slm_h ** 2 * self.slm_pitch ** 2 / 4)
            self.xc = xc[coords[0]]
            self.yc = yc[coords[0]]
            self.slm_pix_coords = cp.asarray(coords[0], dtype=cp.int32)
        else:
            self.xc = xc
            self.yc = yc
            self.slm_pix_coords = cp.arange(
                0, self.slm_w * self.slm_h, dtype=cp.int32)

        self.n_slm = self.xc.shape[0]
        self.launch_block = 256
        self.launch_grid = math.ceil(self.n_slm / self.launch_block)
        # self.e_grid_dim = (self.n_slm + self.launch_block *
        #                    2 - 1) // (self.launch_block * 2)
        self.e_grid_dim = GPUSMCOUNT * 4

        module = load_kernels()

        self.simp_render = not wavefront_compensation
        self.upd_pix_ker = module.get_function('upd_pix')
        self.upd_pix_simp_ker = module.get_function('upd_pix_simp')
        self.pt_phase_arbitrary_ker = module.get_function('p_phase_arb')
        self.wgs_2_ker = module.get_function('wgs_arb')
        self.rs_arb_ker = module.get_function('rs_arb')
        self.copy_to_2d_apr_ker = module.get_function('copy_to_2d_apr')
        self.copy_to_2d_noapr_ker = module.get_function('copy_to_2d_noapr')
        self.e_field_l1_ker = module.get_function('efield_reduce_l1')
        self.e_field_l2_ker = module.get_function('efield_reduce_l2')

        g_slm_ptr = module.get_global('g_slm')

        slm_dtype = np.dtype([
            ("k2pi_over_lam_f", np.float32),
            ("pi_wl_f2", np.float32),
            ("inv_n_slm", np.float32),
            ("inv_aperture_cubed", np.float32),
            ("slm_pitch", np.float32),
            ("n_slm", np.int32),
            ("slm_w", np.int32),
            ("slm_h", np.int32),
            ("x_lim", np.float32),
            ("y_lim", np.float32),
        ])

        params = np.zeros(1, dtype=slm_dtype)

        params["k2pi_over_lam_f"] = 2.0 * np.pi / self.wavelength / self.f
        params["pi_wl_f2"] = np.pi / self.wavelength / self.f ** 2
        params["inv_n_slm"] = 1. / self.n_slm,
        params["inv_aperture_cubed"] = 1. / \
            ((self.slm_h * self.slm_pitch / 2) ** 3)

        params["slm_pitch"] = self.slm_pitch
        params["n_slm"] = self.n_slm
        params["slm_w"] = self.slm_w
        params["slm_h"] = self.slm_h
        params["x_lim"] = (self.slm_w - 1.0) / 2
        params["y_lim"] = (self.slm_h - 1.0) / 2

        cp.cuda.runtime.memcpy(
            g_slm_ptr.ptr,              # dst: device pointer
            params.ctypes.data,      # src: host pointer
            params.nbytes,           # number of bytes
            cp.cuda.runtime.memcpyHostToDevice,
        )

        self.beam_weight = np.asarray([0.20, 1.0, 0.60], dtype=np.float32)

        # CuPy memory alloc
        self.phase_gpu = cp.zeros(self.n_slm, dtype=cp.float32)
        self.p_phase = None
        if wavefront_compensation:
            wf = np.reshape(cv2.imread('./wfc.bmp', cv2.IMREAD_GRAYSCALE), -1)
            if self.apertured:
                self.wfc = cp.asarray(
                    wf[cp.asnumpy(coords[0])], dtype=cp.float32)
            else:
                self.wfc = cp.asarray(wf, dtype=cp.float32)
        else:
            self.wfc = cp.zeros(self.n_slm, dtype=cp.float32)

        self.x_gpu = None
        self.y_gpu = None
        self.z_gpu = None

    def gen_perf_string(self, header, time, ints, ints_adj):
        effi = np.sum(ints) * 100
        unif = (1 - (np.max(ints_adj) - np.min(ints_adj))
                / (np.max(ints_adj) + np.min(ints_adj))) * 100
        return f'{header}: Time: {time * 1000:.2f} ms, Efficiency: {effi:.2f}%, Uniformity: {unif:.2f}%. '

    def rs(self, x, y, z, assess=False, simulate=False, rel_e=None, param_transfer=True):
        l = np.zeros_like(x, dtype=np.float32)
        th = np.zeros_like(l)
        ir = np.zeros_like(l)
        bm = np.zeros_like(x, dtype=np.int32)
        return self.rs_arb(x, y, z, l, th, ir, bm, assess=assess, simulate=simulate, rel_e=rel_e)

    def rs_all(self, x, y, z, assess=False, simulate=False, beammode=0, l=None, th=None, ir=None):
        bm = np.ones_like(x, dtype=np.int32) * beammode
        if l is None:
            l = np.zeros_like(x, dtype=np.float32)
        if th is None:
            th = np.zeros_like(x, dtype=np.float32)
        if ir is None:
            ir = np.zeros_like(x, dtype=np.float32)
        return self.rs_arb(x, y, z, l, th, ir, bm, assess=assess, simulate=simulate)

    def rs_lg(self, x, y, z, l, assess=False, simulate=False):
        th = np.zeros_like(l)
        ir = np.zeros_like(l)
        bm = np.ones_like(x, dtype=np.int32)
        return self.rs_arb(x, y, z, l, th, ir, bm, assess=assess, simulate=simulate, )

    def rs_airy(self, x, y, z, th, ir, assess=False, simulate=False):
        l = np.zeros_like(x, dtype=np.float32)
        bm = np.ones_like(x, dtype=np.int32) * 2
        return self.rs_arb(x, y, z, l, th, ir, bm, assess=assess, simulate=simulate, )

    def rs_arb(self, x, y, z, l, th, ir, beammode, assess=False, simulate=False, weightadj=False, rel_e=None):
        start = time()
        n_pts = x.shape[0]
        x_gpu = cp.asarray(x)
        y_gpu = cp.asarray(y)
        z_gpu = cp.asarray(z)
        l_gpu = cp.asarray(l)
        th_gpu = cp.asarray(th)
        ir_gpu = cp.asarray(ir)
        bm_gpu = cp.asarray(beammode, dtype=cp.int32)
        rand = cp.random.random(n_pts, dtype=cp.float32) * 2 * cp.pi
        self.p_phase = cp.zeros((n_pts, self.n_slm), dtype=cp.float32)
        self.pt_phase_arbitrary_ker((self.launch_grid,), (self.launch_block,),
                                    (x_gpu, y_gpu, z_gpu, l_gpu, th_gpu, ir_gpu, bm_gpu, self.xc, self.yc,
                                     n_pts, self.p_phase))
        # phase_to_save = cp.asnumpy(self.p_phase)
        # np.savetxt("./p_phase1.txt",phase_to_save.reshape(-1))
        if weightadj:
            bw_gpu = cp.asarray(self.beam_weight[beammode], dtype=cp.float32)
        elif rel_e is None:
            bw_gpu = cp.ones(n_pts, dtype=cp.float32)
        else:
            rel_e = rel_e / np.max(rel_e)
            bw_gpu = cp.asarray(rel_e, dtype=cp.float32)

        self.rs_arb_ker((self.launch_grid,), (self.launch_block,),
                        (x_gpu, y_gpu, z_gpu, l_gpu, th_gpu, ir_gpu, bm_gpu, n_pts, bw_gpu, rand, self.p_phase, self.phase_gpu))
        self.gl_draw()
        perf_str = self.rs_performance_assess(
            'Arbitrary Beam ', start, n_pts, x_gpu, y_gpu, z_gpu, l_gpu, th_gpu, ir_gpu, bm_gpu) if assess else ''
        sim_str = self.simulate(assess=assess) if simulate else ''
        return perf_str + sim_str

    def rs_performance_assess(self, header, t_start, n_pts, xg, yg, zg, lg, thg, irg, bmg, rel_e=None):
        # print(self.e_grid_dim)
        epart_real = cp.zeros(self.e_grid_dim * n_pts, dtype=cp.float32)
        epart_imag = cp.zeros(self.e_grid_dim * n_pts, dtype=cp.float32)
        e_abs = cp.zeros(n_pts, dtype=np.float32)
        gs = cp.zeros_like(e_abs)
        wgts = cp.zeros_like(e_abs)
        self.e_field_l1_ker((self.e_grid_dim,), (self.launch_block,),
                            (self.phase_gpu, self.p_phase, epart_real, epart_imag, n_pts, self.e_grid_dim, xg, yg, zg, lg, thg, irg, bmg))
        self.e_field_l2_ker((n_pts,), (self.launch_block,),
                            (epart_real, epart_imag, self.e_grid_dim, e_abs, gs, wgts))
        ints = e_abs ** 2
        ints_c = cp.asnumpy(ints)
        if rel_e is None:
            ints_adj_c = ints_c
        else:
            ints_adj_c = ints_c / rel_e ** 2
        return header + 'RS Time: %.2f ms, Efficiency: %.2f%%, Uniformity: %.2f%%. ' % (
            (time() - t_start) * 1000, np.sum(ints_c) * 100,
            (1 - (np.amax(ints_adj_c) - np.amin(ints_adj_c)) / (np.amax(ints_adj_c) + np.min(ints_adj_c))) * 100)

    def wgs_e_field(self, epart_real, epart_imag, e_abs, n_pts, gs_phase, wgts, xg, yg, zg, lg, thg, irg, bmg):
        self.e_field_l1_ker((self.e_grid_dim,), (self.launch_block,),
                            (self.phase_gpu, self.p_phase, epart_real, epart_imag, n_pts, self.e_grid_dim, xg, yg, zg, lg, thg, irg, bmg))
        self.e_field_l2_ker((n_pts,), (self.launch_block,),
                            (epart_real, epart_imag, self.e_grid_dim, e_abs, gs_phase, wgts,))
        ints = e_abs ** 2
        return gs_phase, wgts, ints

    def wgs(self, x, y, z, n_iter=None, rel_e=None, assess=False, step_assess=False, simulate=False):
        l = np.zeros_like(x, dtype=np.float32)
        th = np.zeros_like(l)
        ir = np.zeros_like(l)
        bm = np.zeros_like(x, dtype=np.int32)
        return self.wgs_arb(x, y, z, l, th, ir, bm, n_iter=n_iter, rel_int=rel_e, assess=assess, step_assess=step_assess, simulate=simulate)

    def wgs_all(self, x, y, z, n_iter=None, assess=False, step_assess=False, simulate=False, beammode=0, l=None,
                th=None, ir=None):
        bm = np.ones_like(x, dtype=np.int32) * beammode
        if l is None:
            l = np.zeros_like(x, dtype=np.float32)
        if th is None:
            th = np.zeros_like(x, dtype=np.float32)
        if ir is None:
            ir = np.zeros_like(x, dtype=np.float32)
        return self.wgs_arb(x, y, z, l, th, ir, bm, n_iter=n_iter, assess=assess, step_assess=step_assess, simulate=simulate)

    def wgs_arb(self, x, y, z, l, th, ir, beammodes, n_iter=None, assess=False, step_assess=False, simulate=False,
                weightadj=False, rel_int=None):
        if not n_iter:
            n_iter = self.gs_iter
        st1 = time()
        n_pts = x.shape[0]
        x_gpu = cp.asarray(x)
        y_gpu = cp.asarray(y)
        z_gpu = cp.asarray(z)
        ints = None

        gs_phase = cp.random.random(n_pts, dtype=cp.float32) * np.pi * 2.0
        epart_real = cp.zeros(n_pts * self.e_grid_dim, dtype=cp.float32)
        epart_imag = cp.zeros(n_pts * self.e_grid_dim, dtype=cp.float32)
        e_abs = cp.zeros_like(x_gpu, dtype=cp.float32)
        wgts = cp.ones(n_pts, dtype=cp.float32) / n_pts
        use_weighting = False

        if weightadj:
            # Default beam weights
            bw_host = np.asarray(self.beam_weight[beammodes], dtype=np.float32)
            use_weighting = True
        elif rel_int is not None:
            rel_int = np.asarray(rel_int, dtype=np.float32)
            if rel_int.shape[0] != n_pts:
                raise ValueError(
                    f"rel_int length ({rel_int.shape[0]}) must match n_pts ({n_pts})"
                )
            max_ri = np.max(rel_int)
            if max_ri > 0:
                bw_host = rel_int / max_ri
                use_weighting = True
            else:
                # Degenerate case: all zeros or negative → fall back to ones
                bw_host = np.ones(n_pts, dtype=np.float32)
        else:
            # No weighting requested
            bw_host = np.ones(n_pts, dtype=np.float32)

        bw_gpu = cp.asarray(bw_host, dtype=cp.float32)
        if use_weighting:
            wgts = cp.multiply(wgts, bw_gpu)
            wgts = wgts / cp.sum(wgts)

        l_gpu = cp.asarray(l)
        th_gpu = cp.asarray(th)
        ir_gpu = cp.asarray(ir)
        bm_gpu = cp.asarray(beammodes, dtype=cp.int32)
        self.p_phase = cp.zeros((n_pts, self.n_slm), dtype=cp.float32)
        self.pt_phase_arbitrary_ker((self.launch_grid,), (self.launch_block,),
                                    (x_gpu, y_gpu, z_gpu, l_gpu, th_gpu, ir_gpu, bm_gpu, self.xc, self.yc,
                                     n_pts, self.p_phase))
        for i in range(n_iter):
            start = time()
            self.wgs_2_ker((self.launch_grid,), (self.launch_block,),
                           (x_gpu, y_gpu, z_gpu, l_gpu, th_gpu, ir_gpu, bm_gpu, n_pts, wgts, gs_phase, self.p_phase, self.phase_gpu))
            gs_phase, wgts, ints = self.wgs_e_field(
                epart_real, epart_imag, e_abs, n_pts, gs_phase, wgts, x_gpu, y_gpu, z_gpu, l_gpu, th_gpu, ir_gpu, bm_gpu)
            if use_weighting:
                wgts = bw_gpu * wgts
            wgts = wgts / cp.sum(wgts)
            self.gl_draw()
            if step_assess:
                ints_adj = ints / bw_gpu ** 2
                ints_c = cp.asnumpy(ints)
                ints_adj_c = cp.asnumpy(ints_adj)
                assess_str = self.gen_perf_string(
                    f'Iter {i + 1}', time() - start, ints_c, ints_adj_c)
                print(assess_str)
        perf_str = ''
        if assess:
            ints_adj = ints / bw_gpu ** 2
            ints_c = cp.asnumpy(ints)
            ints_adj_c = cp.asnumpy(ints_adj)
            perf_str = self.gen_perf_string(
                f'WGS ({n_iter} Iters.)', time() - st1, ints_c, ints_adj_c)
        sim_str = self.simulate(assess=assess) if simulate else ''
        return perf_str + sim_str

    def gl_draw(self, phase=None):
        pass

    def gl_capture(self):
        pass

    def simulate(self, assess=False, zOffset=None, fig=None, ax=None, plotrange=100):
        st = time()
        # Simulation canvas setting: in order to obtain higher resolution in frequency domain (hence the spatial
        # resolution at the Fourier plane), a larger-than-necessary real-space and square canvas is generated for
        # beam and phase mask. Beam and mask are both (re)calculated with correct geometries before Fourier transform.
        # By default, self.slm_w is used for simulation canvas size, giving a frequency resolution of
        #                               f * lamda / sim_l / slm_pitch [um/pixel].
        # Should a higher resolution be deemed necessary, self.sim_scalefactor is used to set.

        sim_l = int(self.slm_w * self.sim_scalefactor)

        e0 = cp.zeros((sim_l, sim_l), dtype=cp.float32)
        lim = (sim_l - 1.0) / 2
        xc, yc = cp.meshgrid(cp.linspace(-lim, lim, sim_l, dtype=cp.float32) * self.slm_pitch,
                             cp.linspace(-lim, lim, sim_l, dtype=cp.float32) * self.slm_pitch)

        e0[cp.where(xc ** 2 + yc ** 2 < self.beam_rad ** 2)] = 1
        k = 2 * np.pi / self.wavelength
        ff = self.f
        phase2d = cp.zeros((sim_l, sim_l), dtype=cp.float32)
        if self.apertured:
            self.copy_to_2d_apr_ker((self.launch_grid,), (self.launch_block,),
                                    (self.phase_gpu, self.slm_pix_coords, phase2d, self.slm_h, self.slm_w,
                                     sim_l, sim_l))
        else:
            self.copy_to_2d_noapr_ker((self.launch_grid,), (self.launch_block,), (
                self.phase_gpu, phase2d, self.slm_h, self.slm_w, sim_l, sim_l))
        if zOffset is None:
            e_focus = cp.exp(1j * 2 * k * ff) / (1j * self.wavelength * ff) * cp.fft.fftshift(
                cp.fft.fft2(e0 * cp.exp(1j * phase2d)))
        else:
            fx = xc / sim_l * self.wavelength * ff
            fy = yc / sim_l * self.wavelength * ff
            e_focus = cp.exp(1j * k * (2 * ff + zOffset + fx ** 2 + fy ** 2)) / (
                1j * self.wavelength * ff) * cp.fft.fftshift(cp.fft.fft2(
                    e0 * cp.exp(1j * (phase2d - np.pi * zOffset / (self.wavelength * ff ** 2) * (xc ** 2 + yc ** 2)))))

        i_focus = cp.abs(e_focus ** 2)
        perf_str = 'Simulation time: %.2f ms, ' % (
            (time() - st) * 1000) if assess else ''
        st = time()
        if fig is None:
            plt.style.use('dark_background')
            fig = plt.figure(figsize=(12, 9))
            ax = fig.add_subplot(1, 1, 1)
            external_show = False
        else:
            external_show = True
        ax.grid(alpha=0.2)

        range = plotrange // 2
        ticks_array = np.arange(-range, range + 1, 10)

        x_50 = ticks_array / self.wavelength / \
            self.f * sim_l * self.slm_pitch + sim_l / 2
        y_50 = ticks_array / self.wavelength / \
            self.f * sim_l * self.slm_pitch + sim_l / 2
        ax.set_xlim(x_50[0], x_50[-1])
        ax.set_ylim(y_50[0], y_50[-1])
        ax.set_xticks(x_50)
        ax.set_xticklabels(ticks_array)
        ax.set_yticks(y_50)
        ax.set_yticklabels(ticks_array)
        ax.set_xlabel('[μm]')
        ax.set_ylabel('[μm]')
        if zOffset is None:
            ax.set_title(
                'Hologram Reconstruction Simulation / Relative Intensity at Fourier Plane')
        else:
            ax.set_title(
                'Hologram Reconstruction Simulation / Relative Intensity at Z = %.2f μm' % zOffset)
        im = ax.imshow(i_focus.get(), cmap='inferno', interpolation='spline36')
        perf_str += ' simulation plot time: %.2f ms.' % (
            (time() - st) * 1000) if assess else ''
        if not external_show:
            cb = fig.colorbar(im, orientation='vertical')
            plt.show()
        return perf_str

    def __del__(self):
        pass
