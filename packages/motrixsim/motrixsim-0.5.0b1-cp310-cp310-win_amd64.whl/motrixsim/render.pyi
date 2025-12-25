# Copyright (C) 2020-2025 Motphys Technology Co., Ltd. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import builtins
import numpy
import numpy.typing
import typing
from motrixsim import Camera, SceneModel

class CaptureTask:
    state: builtins.str
    r"""
    str: The state of the capture task.
    
    - `pending` if the capture is processing.
    - `success` if the capture was successful.
    - `failed` if the capture failed.
    - `used` if the captured image has been used and cannot be accessed anymore.
    """
    def take_image(self) -> typing.Optional[Image]:
        r"""
        Try take the image from the capture task.
        
        Returns:
           Option[Image]: The captured image.
           - If the capture is successful, it will return the image and set the state to `Used`.
           - Otherwise, it will return `None` and the state will remain unchanged.
        """

class Color:
    r"""
    A color in RGBA format, where each component is a float in the range [0.0, 1.0].
    """
    r: builtins.float
    r"""
    float: The red component of the color.
    """
    g: builtins.float
    r"""
    float: The green component of the color.
    """
    b: builtins.float
    r"""
    float: The blue component of the color.
    """
    a: builtins.float
    r"""
    float: The alpha component of the color, representing transparency.
    """
    @staticmethod
    def rgb(r:builtins.float, g:builtins.float, b:builtins.float) -> Color:
        r"""
        Create a color with red, green, blue. Each value should be in the range [0.0, 1.0].
        
        Args:
            r (float): Red component.
            g (float): Green component.
            b (float): Blue component.
        Returns:
            Color: The created color.
        """
    @staticmethod
    def white() -> Color: ...

class Image:
    r"""
    Gizmos module for rendering simple shapes in immediate mode.
    """
    pixels: numpy.typing.NDArray[numpy.uint8]
    r"""
    NDArray[byte]: Get the pixels of the image as a 3D numpy array. The shape is `(width,
    height, 3)`.
    """
    def save_to_disk(self, path:builtins.str) -> None:
        r"""
        Save the image to disk with the specified path.
        """

class Input:
    r"""
    The Input object represents the input events of the render app.
    
    This class provides access to the input events of the render app.
    It allows you to check if a key or mouse button is pressed, and get the mouse ray.
    """
    def is_key_just_pressed(self, key:builtins.str) -> builtins.bool:
        r"""
        Check if a key is just pressed.
        Check by inputting the lowercase form of the keyboard keys, such as 'a' 's' 'w' 'd' 'f5' and
        'esc'. The details can be found in the "Supported Keyboard Keys Table" under the "IO
        Input Events" section of the :doc:`/user_guide/main_function/render`.
        
        Args:
            key (str): The key to check.
        
        Returns:
            bool: True if the key is pressed, False otherwise.
        """
    def is_key_pressed(self, key:builtins.str) -> builtins.bool:
        r"""
        Check if a key is just pressed.
        Check by inputting the lowercase form of the keyboard keys, such as 'a' 's' 'w' 'd' 'f5' and
        'esc'. The details can be found in the "Supported Keyboard Keys Table" under the "IO
        Input Events" section of the :doc:`/user_guide/main_function/render`.
        
        Args:
            key (str): The key to check.
        
        Returns:
            bool: True if the key is pressed, False otherwise.
        """
    def is_mouse_just_pressed(self, mouse:builtins.str) -> builtins.bool:
        r"""
        Check if a mouse button is just pressed.
        
        Args:
            mouse (str): The mouse button to check.
        
        Returns:
            bool: True if the mouse button is pressed, False otherwise.
        """
    def mouse_ray(self) -> builtins.list[builtins.float]:
        r"""
        Returns a ray from camera to mouse click position.
        
        Returns:
            List[float]: The ray from camera to mouse click position.
            It is a 6-element array:
            - Origin : (array[0],array[1],array[2])
            - Direction : (array[3],array[4],array[5])
        """
    def is_ctrl_clicked(self, ctrl_id:builtins.int) -> builtins.bool:
        r"""
        Check whether a control with the given ID is clicked.
        
        Args:
            ctrl_id (int): The ID of the control.
        
        Returns:
            bool: True if the control is clicked, False otherwise.
        """

class RenderApp:
    r"""
    The RenderApp class is responsible for rendering the simulation scene.
    
    This class provides functionality to load models, update their transformations, and render the
    scene. It also handles the creation and management of the render application.
    """
    opt: RenderOpt
    r"""
    RenderOpt: The options of the render app.
    
    Return the options of the render app, which can be used to configure various settings.
    """
    input: Input
    r"""
    Input: The input module of the render app.
    
    Return the input module for handling user input events.
    """
    ui: RenderUI
    r"""
    RenderUI: The UI module of the render app.
    """
    gizmos: RenderGizmos
    r"""
    RenderGizmos: The gizmos module of the render app.
    
    Return the gizmos module for rendering simple shapes in immediate mode.
    """
    system_camera: SystemCamera
    r"""
    The system camera
    """
    is_closed: builtins.bool
    r"""
    Check if the render app is closed.
    """
    def __new__(cls, log_level:builtins.str='WARN', headless:builtins.bool=False, fps:typing.Optional[builtins.int]=None) -> RenderApp:
        r"""
        Create a new RenderApp instance.
        
        Args:
            log_level (str): The log level for the render app. Default is "WARN".
            headless (bool): Whether to run in headless mode. Default is False.
            fps (Optional[int]): Target frame rate for the renderer in headless mode. If None, uses
        unlimited FPS. Default is None.
        """
    def launch(self, model:SceneModel, batch:builtins.int=1, render_offset:typing.Optional[typing.Sequence[typing.Sequence[builtins.float]]]=None, render_settings:RenderSettings=...) -> None:
        r"""
        Load a model into the render app.
        
        Args:
            model (SceneModel): The scene model to load into the render app.
            batch (int, optional): The number of instances to create. Default is 1.
            render_offset (Optional[List[List[float]]], optional): The offset of each instance in
                render space. Default is None.
        
        Raises:
            RenderClosedError: If the render app is closed.
            InvalidArgumentError: If the file is invalid.
            InvalidFileError: If there are issues with file operations.
            OtherRenderError: For other unexpected errors.
        """
    def sync(self, data:typing.Any) -> None:
        r"""
        Synchronize the render app backend with python data.
        
        Args:
            data (None | SceneData | NDArray): The scene data to synchronize with the renderer.
                This argument accept following types:
                    - None: No data is provided, the render will use the last known transforms.
                    - SceneData: The scene data used to update the render. If you lanched the render
                      with `repeat > 1`, the shape the of data must be `(repeat,)`.
                    - NDArray: A 3D numpy array with shape `(num_instances, num_links, 7)`, where
                      the last dimension represents the pose of each link in the format `[x, y, z,
                      qx, qy, qz, qw]`.
        Raises:
            RenderClosedError: If the render app is closed.
            InvalidArgumentError: If neither datas nor poses is provided correctly.
            InvalidFileError: If there are issues with file operations.
            OtherRenderError: Not launched with model file.
        """
    def set_main_camera(self, camera:typing.Optional[Camera]) -> None:
        r"""
        Set the main camera of the render app.
        
        Args:
            camera (Optional[Camera]): The camera to set as the main camera. If None, the system
            camera will be used.
        """
    def get_camera(self, index:builtins.int) -> typing.Optional[RenderCamera]:
        r"""
        Get a render camera instance.
        """
    def set_all_scene_vis(self, visible:builtins.bool) -> None: ...
    def set_scene_vis(self, indices:typing.Sequence[builtins.int], visible:builtins.bool) -> None: ...
    def __enter__(self) -> RenderApp: ...
    def __exit__(self, exc_type:typing.Any, _exc_val:typing.Any, _exc_tb:typing.Any) -> builtins.bool: ...

class RenderCamera:
    def capture(self) -> CaptureTask:
        r"""
        Request a capture from this camera. This operation is asynchronous and you need to query the
        result by the returned `CaptureTask`.
        
        Returns:
            CaptureTask: An async task that can be used to check the capture state and get the
            captured image.
        """

class RenderGizmos:
    r"""
    Gizmos module for rendering simple shapes in immediate mode.
    """
    def draw_sphere(self, radius:builtins.float, pos:typing.Any, color:Color=...) -> None:
        r"""
        Draw a sphere at the given position with the specified radius and color.
        
        Args:
            radius (float): The radius of the sphere.
            pos (list[float] | NDArray): The position of the sphere in 3D space.
            color (Color): The color of the sphere.
        """
    def draw_cuboid(self, size:typing.Any, pos:typing.Any, rot:typing.Any, color:Color=...) -> None:
        r"""
        Draw a cuboid.
        
        Args:
            size (list[float] | NDArray): Size of the cuboid in 3D space.
            pos (list[float] | NDArray): Position of the cuboid in 3D space.
            rot (list[float] | NDArray): Rotation of the cuboid as a quaternion (x, y, z, w).
            color (Color): Color of the cuboid.
        """
    def draw_cylinder(self, half_height:builtins.float, radius:builtins.float, pos:typing.Any, rot:typing.Any, color:Color=...) -> None:
        r"""
        Draw a cylinder.
        
        Args:
            half_height (float): The half height of the cylinder.
            radius (float): The radius of the cylinder.
            pos (list[float] | NDArray): Position of the cylinder in 3D space.
            rot (list[float] | NDArray): Rotation of the cylinder as a quaternion (x, y, z, w).
            color (Color): Color of the cylinder.
        """
    def draw_capsule(self, half_height:builtins.float, radius:builtins.float, pos:typing.Any, rot:typing.Any, color:Color=...) -> None:
        r"""
        Draw a capsule.
        
        Args:
            half_height (float): The half height of the capsule.
            radius (float): The radius of the capsule.
            pos (list[float] | NDArray): Position of the capsule in 3D space.
            rot (list[float] | NDArray): Rotation of the capsule as a quaternion (x, y, z, w).
            color (Color): Color of the capsule.
        """
    def draw_ray(self, start:typing.Any, vector:typing.Any, color:Color=...) -> None:
        r"""
        Draw a ray.
        
        Args:
            start (list[float] | NDArray): The start point of the ray in 3D space.
            vector (list[float] | NDArray): The direction of the ray.
            color (Color): Color of the ray.
        """
    def draw_line(self, start:typing.Any, end:typing.Any, color:Color=...) -> None:
        r"""
        Draw a line.
        
        Args:
            start (list[float] | NDArray): The start point of the line in 3D space.
            end (list[float] | NDArray): The end point of the line.
            color (Color): Color of the line.
        """
    def draw_arrow(self, start:typing.Any, end:typing.Any, color:Color=...) -> None:
        r"""
        Draw a arrow.
        
        Args:
            start (list[float] | NDArray): The start point of the arrow in 3D space.
            end (list[float] | NDArray): The end point of the arrow.
            color (Color): Color of the arrow.
        """
    def draw_rect(self, width:builtins.float, height:builtins.float, pos:typing.Any, rot:typing.Any, color:Color=...) -> None:
        r"""
        Draw a rectangle.
        
        Args:
            width (float): The width of the rectangle.
            height (float): The height of the rectangle.
            pos (list[float] | NDArray): Position of the rectangle in 3D space.
            rot (list[float] | NDArray): Rotation of the rectangle as a quaternion (x, y, z, w).
            color (Color): Color of the rectangle.
        """
    def draw_grid(self, pos:typing.Any, rot:typing.Any, x_count:builtins.int=2, y_count:builtins.int=2, z_count:builtins.int=2, spacing:typing.Optional[typing.Any]=None, color:Color=...) -> None:
        r"""
        Draw a rectangle.
        
        Args:
            pos (list[float] | NDArray): Position of the rectangle in 3D space.
            rot (list[float] | NDArray): Rotation of the rectangle as a quaternion (x, y, z, w).
            x_count (unsigned int): The number of grid cells along the x-axis.
            y_count (unsigned int): The number of grid cells along the y-axis.
            z_count (unsigned int): The number of grid cells along the z-axis.
            spacing (list[float] | NDArray): The spacing(x,y,z) between the grid cells.
            color (Color): Color of the rectangle.
        """
    def draw_axes(self, pos:typing.Optional[typing.Any]=None, rot:typing.Optional[typing.Any]=None, length:builtins.float=1.0) -> None:
        r"""
        Draw the XYZ axes at the given position and rotation.
        
        Args:
            pos (list[float] | ndarray, optional): the position of axes with (x,y,z) format.
            rot (list[float] | ndarray, optional): the rotation of axes as a quaternion (x, y, z,
            length (float): the length of each axis.
        w).
        """

class RenderOpt:
    r"""
    The RenderOpt object represents the options of the render app.
    """
    def is_left_panel_vis(self) -> builtins.bool:
        r"""
        Check if the left panel is visible.
        
        Returns:
            bool: True if the left panel is visible, False otherwise.
        """
    def set_left_panel_vis(self, enabled:builtins.bool) -> None:
        r"""
        Set the visibility of the left panel.
        
        Args:
            enabled (bool): True to show the left panel, False to hide it.
        """

class RenderSettings:
    r"""
    The global render settings for render app.
    """
    simplify_render_mesh: builtins.bool
    r"""
    Wether to simplify render mesh when loading the model.
    """
    enable_shadow: builtins.bool
    r"""
    Whether to render shadows for lights.
    """
    enable_ssao: builtins.bool
    r"""
    Whether to enable SSAO(Screen Space Ambient Occlusion) effect.
    """
    enable_oit: builtins.bool
    r"""
    Whether to enable OIT(Order Independent Transparency) effect.
    """
    share_lights_between_envs: builtins.bool
    r"""
    Whether to share lights between multiple simulation worlds, for performance optimization.
    If false, each simulation world will have its own set of lights, which may cost more
    rendering resources, or out of memory crash depends on the number of simulation worlds and
    scene complexity.
    """
    def __new__(cls, simplify_render_mesh:builtins.bool, enable_shadow:builtins.bool, enable_ssao:builtins.bool, enable_oit:builtins.bool, share_lights_between_envs:builtins.bool) -> RenderSettings: ...
    @staticmethod
    def quality() -> RenderSettings:
        r"""
        Get a render settings with high quality.
        """
    @staticmethod
    def performance() -> RenderSettings:
        r"""
        Get a render settings with high performance.
        """

class RenderUI:
    r"""
    The RenderUI object represents the user interface of the render app.
    
    This class provides access to the user interface of the render app.
    It allows you to add buttons, toggles, and other UI elements to the render app.
    """
    def add_button(self, label:builtins.str, on_click:typing.Any) -> builtins.int:
        r"""
        Add a button to the user interface.
        
        Args:
            label (str): The label of the button.
            on_click (PyAny): The callback function to be called when the button is clicked.
        
        Returns:
            int: The ID of the button.
        """
    def add_toggle(self, label:builtins.str, default:builtins.bool, on_changed:typing.Any) -> builtins.int:
        r"""
        Add a toggle to the user interface.
        
        Args:
            label (str): The label of the toggle.
            default (bool): The default state of the toggle.
            on_changed (PyAny): The callback function to be called when the toggle is changed.
        """

class SystemCamera:
    ...

class InvalidArgumentError(RenderError): ...

class InvalidFileError(RenderError): ...

class OtherRenderError(RenderError): ...

class RenderClosedError(RenderError): ...

class RenderError(Exception): ...

