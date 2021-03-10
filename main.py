"""
Shadow mapping example from:
https://www.opengl-tutorial.org/intermediate-tutorials/tutorial-16-shadow-mapping/
"""
import math
from pathlib import Path
from pyrr import Matrix44, matrix44, Vector3

import moderngl
import moderngl_window
from moderngl_window import geometry

from base import CameraWindow


class ShadowMapping(CameraWindow):
    title = "Shadow Mapping"
    resource_dir = (Path(__file__) / '../resources').resolve()

    print(resource_dir)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.camera.projection.update(near=1, far=200)
        self.wnd.mouse_exclusivity = True

        # Offscreen buffer
        offscreen_size = 1024, 1024
        self.offscreen_depth = self.ctx.depth_texture(offscreen_size)
        self.offscreen_depth.compare_func = ''
        self.offscreen_depth.repeat_x = False
        self.offscreen_depth.repeat_y = False
        self.offscreen_color = self.ctx.texture(offscreen_size, 4)

        self.offscreen = self.ctx.framebuffer(
            color_attachments=[self.offscreen_color],
            depth_attachment=self.offscreen_depth,
        )

        # Scene geometry
        self.floor = geometry.cube(size=(25.0, 1.0, 25.0))
        self.wall = geometry.cube(size=(1.0, 5, 25), center=(-12.5, 2, 0))
        self.another_wall = geometry.cube(size=(5, 1, 25), center=(0, 5, 0))
        self.cube = geometry.cube(size=(2, 1, 5), center=(2, 5, -10))
        self.sphere = geometry.sphere(radius=5.0, sectors=64, rings=32)
        self.sun = geometry.sphere(radius=1.0)

        # Programs
        self.raw_depth_prog = self.load_program('programs/shadow_mapping/raw_depth.glsl')
        self.basic_light = self.load_program('programs/shadow_mapping/directional_light.glsl')
        self.basic_light['shadowMap'].value = 0
        self.basic_light['color'].value = 1.0, 1.0, 1.0, 1.0
        self.weird_light = self.load_program('programs/shadow_mapping/directional_light.glsl')
        self.weird_light['shadowMap'].value = 0
        self.weird_light['color'].value = 1.0, 1.0, 1.0, 1.0
        self.shadowmap_program = self.load_program('programs/shadow_mapping/shadowmap.glsl')
        self.texture_prog = self.load_program('programs/texture.glsl')
        self.texture_prog['texture0'].value = 0
        self.sun_prog = self.load_program('programs/cube_simple.glsl')
        self.sun_prog['color'].value = 1, 1, 0, 1
        self.lightpos = 0, 0, 0

        self.proge = self.load_program('programs/shadow_mapping/shadowmap.glsl')
        # self.proge['color'].value = 1.0, 1.0, 1.0, 1.0


    def render(self, time, frametime):
        self.ctx.enable_only(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
        self.lightpos = Vector3((math.sin(time) * 20, 15, math.cos(time) * 20), dtype='f4')
        # self.lightpos = Vector3((20, 15, 20), dtype='f4')
        scene_pos = Vector3((0, 0, 0), dtype='f4')

        # --- PASS 1: Render shadow map
        self.offscreen.clear()
        self.offscreen.use()

        depth_projection = Matrix44.orthogonal_projection(-20, 20, -20, 20, -20, 40, dtype='f4')
        depth_view = Matrix44.look_at(self.lightpos, (0, 0, 0), (0, 1, 0), dtype='f4')
        depth_mvp = depth_projection * depth_view
        self.shadowmap_program['mvp'].write(depth_mvp)

        self.floor.render(self.shadowmap_program)
        self.wall.render(self.shadowmap_program)
        self.cube.render(self.shadowmap_program)

        rotation = Matrix44.from_eulers((0.0, 0.0, 0.0), dtype='f4')
        translation = Matrix44.from_translation((0.0, 0.0, 0.0), dtype='f4')
        modelview = translation * rotation

        self.another_wall.render(self.shadowmap_program)

        #self.another_wall.render(self.shadowmap_program)
        self.sphere.render(self.shadowmap_program)

        # --- PASS 2: Render scene to screen
        self.wnd.use()
        self.basic_light['m_proj'].write(self.camera.projection.matrix)
        self.basic_light['m_camera'].write(self.camera.matrix)
        self.basic_light['m_model'].write(Matrix44.from_translation(scene_pos, dtype='f4'))
        bias_matrix = Matrix44(
            [[0.5, 0.0, 0.0, 0.0],
             [0.0, 0.5, 0.0, 0.0],
             [0.0, 0.0, 0.5, 0.0],
             [0.5, 0.5, 0.5, 1.0]],
            dtype='f4',
        )

        self.basic_light['m_shadow_bias'].write(matrix44.multiply(depth_mvp, bias_matrix))
        self.basic_light['lightDir'].write(self.lightpos)

        self.weird_light['m_proj'].write(self.camera.projection.matrix)
        self.weird_light['m_camera'].write(self.camera.matrix)
        self.weird_light['m_model'].write(modelview)
        self.weird_light['m_shadow_bias'].write(matrix44.multiply(depth_mvp, bias_matrix))
        self.weird_light['lightDir'].write(self.lightpos)

        self.offscreen_depth.use(location=0)
        self.floor.render(self.basic_light)
        self.wall.render(self.basic_light)
        self.cube.render(self.basic_light)
        self.another_wall.render(self.basic_light)
        self.sphere.render(self.basic_light)

        # Render the sun position
        self.sun_prog['m_proj'].write(self.camera.projection.matrix)
        self.sun_prog['m_camera'].write(self.camera.matrix)
        self.sun_prog['m_model'].write(Matrix44.from_translation(self.lightpos + scene_pos, dtype='f4'))
        self.sun.render(self.sun_prog)


if __name__ == '__main__':
    moderngl_window.run_window_config(ShadowMapping)