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
import typing
from motrixsim import SceneModel

class Scene:
    r"""
    A builder for combining and building MSD models.
    
    This class provides a simple API for combining multiple models together
    using `attach`, then building the final simulation model.
    
    Example:
    
    ```text
    import motrixsim as mx
    
    # Load and build directly
    model = mx.from_file("robot.xml").build()
    
    # Attach another model with transformations
    robot = mx.from_file("robot.xml")
    gripper = mx.from_file("gripper.xml")
    robot.attach(
        gripper,
        self_link_name="hand",
        other_prefix="gripper_",
        other_translation=[0.1, 0, 0]
    )
    model = robot.build()
    
    # Combine multiple instances of the same model (other is cloned internally)
    scene = mx.from_file("scene.xml")
    robot = mx.from_file("robot.xml")
    scene.attach(robot, other_prefix="robot1_", other_translation=[1, 0, 0])
    scene.attach(robot, other_prefix="robot2_", other_translation=[2, 0, 0])
    model = scene.build()
    ```
    """
    name: builtins.str
    r"""
    Get the name of this instance.
    
    Returns:
        str: The name of the model.
    """
    def deepcopy(self, slf:Scene) -> Scene:
        r"""
        Deepcopy this Scene.
        
        Returns:
            Scene: A clone of this instance.
        """
    def attach(self, other:Scene, self_link_name:typing.Optional[builtins.str]=None, other_link_name:typing.Optional[builtins.str]=None, other_translation:typing.Optional[typing.Sequence[builtins.float]]=None, other_rotation:typing.Optional[typing.Sequence[builtins.float]]=None, other_prefix:typing.Optional[builtins.str]=None, other_suffix:typing.Optional[builtins.str]=None) -> Scene:
        r"""
        Attach another model to this one.
        
        This method merges another Scene into this one. The other model
        can be optionally attached to a specific link, transformed, and have
        its names prefixed/suffixed to avoid conflicts.
        
        Note:
            The other model is cloned internally, so it can be reused for
            multiple attach calls.
        
        Args:
            other (Scene): The model to attach (cloned internally).
            self_link_name (str, optional): Link in this model to attach to.
                If None, the other model is merged at the root level.
            other_link_name (str, optional): Extract only this subtree from the
                other model before attaching.
            other_translation (list[float], optional): Translation [x, y, z] to
                apply to the other model.
            other_rotation (list[float], optional): Rotation quaternion [x, y, z, w]
                to apply to the other model.
            other_prefix (str, optional): Prefix to add to all names in the other
                model (e.g., "left_" to avoid name conflicts).
            other_suffix (str, optional): Suffix to add to all names in the other
                model.
        
        Raises:
            RuntimeError: If the link is not found or if there are duplicate names.
        
        Example:
        
        ```text
        robot = mx.from_file("robot.xml")
        gripper = mx.from_file("gripper.xml")
        
        # Attach gripper to robot's hand link with prefix
        robot.attach(
            gripper,
            self_link_name="hand",
            other_prefix="gripper_",
            other_translation=[0.05, 0, 0]
        )
        
        # gripper can be reused
        robot.attach(gripper, self_link_name="other_hand", other_prefix="gripper2_")
        
        model = robot.build()
        ```
        """
    def build(self) -> SceneModel:
        r"""
        Build this Scene into a SceneModel ready for simulation.
        
        This compiles all attached models into a single simulation model.
        
        Returns:
            SceneModel: The compiled simulation model.
        
        Raises:
            RuntimeError: If the build fails.
        
        Example:
        
        ```text
        # Simple build
        model = mx.from_file("robot.xml").build()
        
        # Build after attaching models
        robot = mx.from_file("robot.xml")
        gripper = mx.from_file("gripper.xml")
        robot.attach(gripper, self_link_name="hand", other_prefix="gripper_")
        model = robot.build()
        
        data = mx.SceneData(model)
        ```
        """

def from_file(path:builtins.str) -> Scene:
    r"""
    Load a model file and return an Scene for transformation and building.
    
    Args:
        path (str): Path to the model file (MJCF, URDF, or MSD format).
    
    Returns:
        Scene: An instance ready for transformation and building.
    """

def from_str(string:builtins.str, format:builtins.str='mjcf') -> Scene:
    r"""
    Load string and return an Scene for transformation and building.
    
    Args:
        string (str): MJCF/URDF/MSD model string.
        format (str): The format of the model string. One of "mjcf", "urdf", or "msd".
    
    Returns:
        Scene: An instance ready for transformation and building.
    """

