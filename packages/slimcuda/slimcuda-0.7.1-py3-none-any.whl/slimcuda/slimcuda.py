import numpy as np
# cuda-python (which required pywin32 in windows, ICYMI)
from cuda.bindings import runtime as cudart
from OpenGL.GL import *
import glfw
from .cuda_gl_map import CudaOpenGLMappedArray
from .slimcuda_toolkit import file_path_complete
from .slimcuda_base import SlimCuda_base
import cv2

# -------------------------------------------------------------------------------------------------------------------- #
# class SLiM-CUDA
# Copyright 2022- Jun-Lei Wang [jwangXTS]
# SLM phase pattern generation using CuPy and OpenGL
#
# -------------------------------------------------------------------------------------------------------------------- #


class SlimCuda(SlimCuda_base):
    def __init__(self, wavelength_nm=1064, slm_pitch=8.0, focal_mm=3.333, apertured=False, beam_rad: int = None,
                 gs_iter=15, slm_w=1920, slm_h=1080, sim_scalefactor=1.0, wavefront_compensation=False):
        super().__init__(wavelength_nm, slm_pitch, focal_mm, apertured, beam_rad,
                         gs_iter, slm_w, slm_h, sim_scalefactor, wavefront_compensation)
        # gl window setup
        glfw.init()
        glfw.window_hint(glfw.DECORATED, 0)

        self.win = glfw.create_window(
            self.slm_w, self.slm_h, 'SLM', None, None)

        glfw.make_context_current(self.win)
        glfw.swap_interval(0)

        # gl parameters setup
        glViewport(0, 0, self.slm_w, self.slm_h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, 1.0, 0, 1.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glEnable(GL_DEPTH_TEST)
        glClearColor(1.0, 1.0, 1.0, 1.5)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glEnable(GL_TEXTURE_2D)
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.slm_w,
                     self.slm_h, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        pbo = glGenBuffers(1)
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, pbo)
        glBufferData(GL_PIXEL_UNPACK_BUFFER, self.slm_w
                     * self.slm_h * 4, None, GL_DYNAMIC_COPY)
        glBindTexture(GL_TEXTURE_2D, pbo)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.slm_w,
                        self.slm_h, GL_LUMINANCE, GL_UNSIGNED_BYTE, None)

        # CUDA GL interop buffer
        flags = cudart.cudaGraphicsRegisterFlags.cudaGraphicsRegisterFlagsWriteDiscard
        self.pixel_buffer = CudaOpenGLMappedArray(
            np.uint8, (self.slm_w, self.slm_h), pbo, flags)

        self._closed = False

    def gl_draw(self, phase=None):
        if self.simp_render:
            if phase is None:
                self.upd_pix_simp_ker((self.launch_grid,), (self.launch_block,),
                                      (self.phase_gpu, self.pixel_buffer.map()))
                # phase_to_save = np.reshape(cp.asnumpy(self.phase_gpu), -1)
                # np.savetxt("./t2.txt", phase_to_save.astype(np.float32))
            else:
                self.upd_pix_simp_ker((self.launch_grid,), (self.launch_block,),
                                      (phase, self.pixel_buffer.map()))
        else:
            if phase is None:
                self.upd_pix_ker((self.launch_grid,), (self.launch_block,),
                                 (self.phase_gpu, self.slm_pix_coords, self.wfc, self.pixel_buffer.map()))
                # phase_to_save = np.reshape(cp.asnumpy(self.phase_gpu), -1)
                # np.savetxt("./t2.txt", phase_to_save.astype(np.float32))
            else:
                self.upd_pix_ker((self.launch_grid,), (self.launch_block,),
                                 (phase, self.slm_pix_coords, self.wfc, self.pixel_buffer.map(), ))

        self.pixel_buffer.unmap()
        glfw.poll_events()
        glClearColor(0.0, 0.0, 1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, self.pixel_buffer.gl_buffer)
        glBindTexture(GL_TEXTURE_2D, self.pixel_buffer.gl_buffer)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.slm_w,
                        self.slm_h, GL_LUMINANCE, GL_UNSIGNED_BYTE, None)

        glBegin(GL_QUADS)
        glTexCoord2f(0, 1.0)
        glVertex3f(0, 0, 0)
        glTexCoord2f(0, 0)
        glVertex3f(0, 1.0, 0)
        glTexCoord2f(1.0, 0)
        glVertex3f(1.0, 1.0, 0)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(1.0, 0, 0)
        glEnd()

        glfw.swap_buffers(self.win)

    def gl_capture(self, file_name: str | None = None):
        frame_width, frame_height = glfw.get_framebuffer_size(self.win)
        pixels = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
        print(pixels.shape)
        glReadBuffer(GL_FRONT)
        glReadPixels(0, 0, frame_width, frame_height,
                     GL_RGB, GL_UNSIGNED_BYTE, pixels)
        print(pixels.shape)
        pixels = np.flip(pixels, axis=0)
        print(pixels.shape)
        pixels_bgr = cv2.cvtColor(pixels, cv2.COLOR_RGB2BGR)
        if file_name is None:
            cv2.imwrite('./phase.png', pixels_bgr)

    def close(self):
        if self._closed:
            return
        self._closed = True

        try:
            if self.win is not None:
                glfw.make_context_current(self.win)
        except Exception:
            pass

        try:
            if self.pixel_buffer is not None:
                self.pixel_buffer.unregister()
                self.pixel_buffer = None
        except Exception:
            pass

        try:
            if self.win is not None:
                glfw.destroy_window(self.win)
                self.win = None
        except Exception:
            pass

        try:
            glfw.terminate()
        except Exception:
            pass

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
