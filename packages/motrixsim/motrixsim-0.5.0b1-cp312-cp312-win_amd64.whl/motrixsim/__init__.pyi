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
from motrixsim.low import LowData, LowSceneModel
from . import ik
from . import low
from . import msd
from . import render
from . import viewer

class Actuator:
    r"""
    The Actuator object represents a controllable actuator in the simulation.
    
    This class provides access to the properties and methods of an actuator, allowing users to
    query its name, index, control range, and set the control value.
    """
    name: typing.Optional[builtins.str]
    r"""
    Optional[str]: The name of the actuator.
    
    Return "None" if not set.
    """
    index: builtins.int
    r"""
    int: The index of the actuator in the simulation world.
    """
    ctrl_range: typing.Optional[builtins.list[builtins.float]]
    r"""
    Optional[Tuple[float, float]]: The control range of the actuator.
    
    Returns None if not set.
    """
    target_type: builtins.str
    r"""
    str: The type of the actuator target.
    
    valid values are:
    
    - "floating_base": For floating base actuators.
    - "joint": For joint actuators.
    - "tendon": For tendon actuators.
    """
    target_name: builtins.str
    r"""
    str: The name of the actuator target. (e.g., joint name, tendon name).
    """
    typ: builtins.str
    r"""
    str: The type of the actuator.
    
    valid values are:
    
    - "general":  General actuator.
    - "position": Position servo. The ctrl represents the target position
    - "velocity": Velocity servo. The ctrl represents the target velocity
    - "motor": The ctrl represents the torque or force
    """
    def set_ctrl(self, data:SceneData, ctrl:typing.Any) -> None:
        r"""
        Set the control value of the actuator.
        
        Args:
            data (SceneData): The scene data to store the control value.
            ctrl (float | NDArray[float]): The control value to set. If the data has batch
                dimension, `ctrl` must have the same shape as the data.
        """
    def get_ctrl(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the control value of the actuator.
        
        Args:
            data (SceneData): The scene data.
        Returns:
            NDArray[float]: The current control value of the actuator. shape = `(*data.shape, )`
        """

class Body:
    r"""
    The Body object represents a rigid body in the scene.
    
    This class provides access to the properties and state of a rigid body in the simulation.
    It allows you to retrieve information about the body's name, floating base, pose, and DoF
    positions and velocities.
    """
    name: typing.Optional[builtins.str]
    r"""
    Optional[str]: The name of the body.
    
    Return `None` if not present.
    """
    floatingbase: typing.Optional[FloatingBase]
    r"""
    Optional[FloatingBase]: The floating base object.
    
    Return `None` if not present.
    
    Note:
      In mjcf, a body is free moving if it has `<freejoint>`
    """
    is_mocap: builtins.bool
    r"""
    bool: Whether the body is a mocap (kinematic) body.
    
    Return True if the body has no joints and fixed to the world, `False` otherwise.
    """
    mocap: typing.Optional[Mocap]
    r"""
    Convert this body to a mocap object if it is a mocap body.
    
    Returns:
        Optional[PyMocap]: The mocap object if this body is a mocap, `None` otherwise.
    """
    num_joint_dof_pos: builtins.int
    r"""
    int: The number of DoF positions of all joints on the body.
    
    Note:
       If the body has floating base, the floating base DoF positions are NOT included
    """
    num_joint_dof_vel: builtins.int
    r"""
    int: The number of DoF velocities of all joints on the body.
    
    Note:
        If the body has floating base, the floating base DoF velocities are NOT included
    """
    num_links: builtins.int
    r"""
    int: The number of links that belong to this body.
    """
    num_joints: builtins.int
    r"""
    int: The number of joints that belong to this body.
    
    Note:
        The `<freejoint>` is not counted as a joint in motrixsim but a floating base.
    """
    base_link: Link
    r"""
    Link: The base link of this body.
    """
    def get_pose(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the world pose of the body.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: shape = `(*data.shape, 7)`.  Each pose is a 7-element array with `[x, y,
            z, i, j, k, w]`.
        """
    def get_position(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the world position of the body.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: shape = `(*data.shape, 3)`.
        """
    def get_rotation(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the world rotation of the body as a quaternion.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: shape = `(*data.shape, 4)`. Each rotation is a 4-element array with `[i,
            j, k, w]`.
        """
    def get_rotation_mat(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the world rotation of the body as a rotation matrix.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: shape = `(*data.shape, 3, 3)`.
        """
    def get_joint_dof_pos(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the DoF positions of all joints on the body.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: The DoF positions. shape = (`*data.shape`, :meth:`num_joint_dof_pos`).
        
        Note:
            If the body has floating base, the floating base DoF positions are NOT included.
        """
    def get_joint_dof_vel(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the DoF velocities of all joints on the body.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: The DoF velocities. shape = (`*data.shape`,:meth:
                `body.num_joint_dof_vel`).
        
        Note:
            If the body has floating base, the floating base DoF velocities are NOT included.
        """
    def get_dof_pos_indices(self, include_floatingbase:builtins.bool=True) -> numpy.typing.NDArray[numpy.uint32]:
        r"""
        Get the indices of the DoF positions of the body.
        
        Args:
            include_floatingbase (bool): Whether to include the floating base DoF positions
                indices. If `False`, only the joint DoF positions indices are returned.
        Returns:
           NDArray[int]: The DoF position indices. if include_floatingbase is true, shape =
                (:meth:`num_joint_dof_pos` + 6,), else shape = (:meth:`num_joint_dof_pos`,).
        """
    def get_dof_vel_indices(self, include_floatingbase:builtins.bool=True) -> numpy.typing.NDArray[numpy.uint32]:
        r"""
        Get the indices of the DoF velocities of the body.
        
        Args:
            include_floatingbase (bool): Whether to include the floating base DoF velocities
                indices. If `False`, only the joint DoF velocities indices are returned.
        Returns:
           NDArray[int]: The DoF velocity indices. if include_floatingbase is true, shape =
                (:meth:`num_joint_dof_vel` + 6,), else shape = (:meth:`num_joint_dof_vel`,).
        """
    def set_dof_vel(self, data:SceneData, dof_vel:typing.Any, include_floatingbase:builtins.bool=True) -> None:
        r"""
        Set the DoF velocities of the body.
        
        Args:
            data (SceneData): The scene data to modify.
            dof_vel (NDArray[float]): The DoF velocities to set. Shape = (:meth:`num_joint_dof_vel`
                + 6,) if `include_floatingbase` is `True`, else shape =(:meth:`num_joint_dof_vel`,).
            include_floatingbase (bool): Whether the provided `dof_vel` includes the floating base
              DoF velocities. If `True`, the first 6 elements of `dof_vel` are treated as the
              floating base DoF velocities.
        """
    def set_dof_pos(self, data:SceneData, dof_pos:typing.Any, include_floatingbase:builtins.bool=True) -> None:
        r"""
        Set the DoF positions of the body.
        
        Args:
            data (SceneData): The scene data to modify.
            dof_pos (NDArray[float]): The DoF positions to set. Shape = `(num_joint_dof_pos + 7,)`
                if `include_floatingbase` is `True`, else shape = (num_joint_dof_pos,).
            include_floatingbase (bool): Whether the provided `dof_pos` includes the floating base
              DoF positions. If `True`, the first 7 elements of `dof_pos` are treated as the
              floating base DoF positions.
        """

class Camera:
    r"""
    The Camera object in the scene.
    """
    model: SceneModel
    r"""
    SceneModel: The scene model that this camera belongs to.
    """
    index: builtins.int
    r"""
    int: The index of the camera in the :func:`motrixsim.SceneModel.cameras`.
    """
    name: typing.Optional[builtins.str]
    r"""
    Option[str]: Get the name of the camera.
    """
    near_plane: builtins.float
    r"""
    float: Get the far plane distance of the camera.
    """
    far_plane: builtins.float
    r"""
    float: Get the far plane distance of the camera.
    """
    position_track: builtins.str
    r"""
    str: Get or set the position track mode of the camera.
    
    Possible values are:
    
    - "free": Free to move in all directions.
    - "fixed_local": Fixed the relative position to parent in local frame.
    - "fixed_world": Fixed the relative position to parent in world frame.
    """
    rotation_track: builtins.str
    r"""
    str: Get or set the rotation track mode of the camera.
    
    Possible values are:
    
    - "free": Free to rotate.
    - "fixed_local": Fixed the relative rotation to parent in local frame.
    - "fixed_world": Fixed the relative rotation to parent in world frame.
    - "look_at_link": Always look at the target link. This mode requires setting the
      `track_target_link` attribute.
    """
    track_target_link: typing.Optional[Link]
    r"""
    Optional[Link]: Get or set the link that the camera looks at.
    
    Note:
        This attribute is only valid when the rotation track mode is "look_at_link".
    """
    render_target: builtins.str
    r"""
    str: Get the render target of the camera, either "window" or "image".
    """
    depth_only: builtins.bool
    r"""
    bool: Whether the camera is in depth-only mode.
    """
    def set_near_far(self, near:builtins.float, far:builtins.float) -> None:
        r"""
        Set the near and far plane of the camera.
        
        Args:
           near (float): The near plane distance. Must be positive.
           far (float): The far plane distance. Must be larger than near.
        """
    def get_pose(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the world pose of the camera.
        
        Args:
           data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: shape = `(*data.shape, 7)`. Each pose is represented as a 7 elements
                array with `[x, y, z, qx, qy, qz,qw]` format.
        """
    def set_render_target(self, target:builtins.str, w:builtins.int=400, h:builtins.int=300) -> None:
        r"""
        Set the render target of the camera.
        
        Args:
           target (str): The render target, either "window" or "image".
        
           w (int): The width of the image if the target is "image". ignored if the target is
           "window".   
        
           h (int): The height of the image if the target is "image". ignored if the target is
           "window".
        
        Note:
           This method must be called before you launch the render application.
        """

class CameraMgr:
    model: SceneModel
    r"""
    SceneModel: The scene model that this camera manager belongs to.
    """
    cameras: builtins.list[Camera]
    r"""
    List[Camera]: All the cameras defined in the model.
    """

class ContactQuery:
    num_contacts: numpy.typing.NDArray[numpy.uint32]
    r"""
    int: The number of contacts in the world.
    """
    def is_colliding(self, geom_pairs:typing.Any) -> numpy.typing.NDArray[numpy.bool_]:
        r"""
        Given a list of geometry pairs, check if they are colliding.
        
        Args:
           geom_pairs (NDArray[u32]): Pairs of geometry
                indices to check for collision. Shape = (N, 2) where N is the number of pairs.
            
        Returns:
            NDArray[bool]: Array of booleans indicating whether each pair is colliding.
        """

class DisjointIndices:
    size: builtins.int
    r"""
    The number of elements in the disjoint index set. Alias to `len(set)`.
    """
    def __new__(cls, indices:typing.Any) -> DisjointIndices:
        r"""
        Create disjoint indices from a list of indices or a bool mask.
        
        Args:
            indices (ArrayLike[int] | ArrayLike[bool]): The list of indices.
            - If type is `ArrayLike[int]`, it creates disjoint indices from the list of indices.
            - If type is `ArrayLike[bool]`, it creates disjoint indices from the index of the true
              values.
        """
    def __len__(self) -> builtins.int: ...

class FloatingBase:
    r"""
    The FloatingBase object represents a floating base in the scene.
    
    This class provides access to the properties and state of a floating base in the scene.
    It allows you to retrieve information about the base's name, DoF velocities and positions,
    and to set its world translation and rotation.
    """
    model: SceneModel
    r"""
    SceneModel: The scene model this floating base belongs to.
    """
    index: builtins.int
    r"""
    int: The index of the floatingbase in the :func:`motrixsim.SceneModel.floating_bases`.
    """
    name: typing.Optional[builtins.str]
    r"""
    Optional[str]: The name of the floating base.
    
    Return `None` if not set.
    """
    dof_vel_start: builtins.int
    r"""
    int: The DoF velocity address of the floating base in the
        :meth:`motrixsim.SceneData.dof_vel`.
    """
    dof_vel_indices: builtins.list[builtins.int]
    r"""
    List[int]: The DoF velocity indices of the floating base. size = 6.
    """
    dof_pos_start: builtins.int
    r"""
    int: The DoF position address of the floating base in the
        :meth:`motrixsim.SceneData.dof_pos`.
    """
    dof_pos_indices: builtins.list[builtins.int]
    r"""
    List[int]: The DoF position indices of the floating base. size = 7.
    """
    def get_dof_vel(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the DoF velocities of the floating base.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: The DoF velocities with (vx,vy,vz wx,wy,wz) format. shape = (data.shape,
            6).
        """
    def get_dof_pos(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the DoF positions of the floating base.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: The DoF positions with (x,y,z, i,j,k,w) format. shape = (data.shape, 7).
        """
    def set_translation(self, data:SceneData, translation:typing.Any) -> None:
        r"""
        Set the world translation of the floating base.
        
        Args:
            data (SceneData): The scene data to store the translation.
            translation (NDArray[float]): The translation [x, y, z]. shape = (data.shape, 3).
        
        Notes:
            This function only updates the DoF position of the floating base. The actual
            translation of links is updated through the forward kinematic phase.
        """
    def set_rotation(self, data:SceneData, quat:typing.Any) -> None:
        r"""
        Set the world rotation of the floating base.
        
        Args:
            data (SceneData): The scene data to store the rotation.
            quat (NDArray[float]): The quaternion [i, j, k, w]. shape = (data.shape, 4).
        
        Notes:
            This function only updates the DoF position of the floating base. The actual rotation
            is updated through the forward kinematic phase.
        """
    def get_translation(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Extract the world translation of the floating base from the dof position array.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: The world translation. shape = (data.shape, 3)
        """
    def get_rotation(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Extract the world rotation of the floating base from the dof position array.
        
        Args:
            data (SceneData): The scene data.
        
        Returns:
            NDArray[float]: A quaternion representing the rotation in the format `[i, j, k, w]`.
        """
    def get_global_linear_velocity(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Extract the world linear velocity of the floating base from the dof velocity array.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: The world linear velocity. shape = (data.shape, 3)
        """
    def get_global_angular_velocity(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Extract the world angular velocity of the floating base from the dof velocity array.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: The world angular velocity. shape = (data.shape, 3)
        """
    def get_local_angular_velocity(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Extract the local angular velocity of the floating base from the dof velocity array.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray(float): The local angular velocity. shape = (data.shape, 3)
        """
    def set_global_linear_velocity(self, data:SceneData, vel:typing.Any) -> None:
        r"""
        Set the global linear velocity of the floating base to dof velocity array directly.
        
        Args:
            data (SceneData): The scene data to store the velocity.
            vel (ArrayLink[float]): The world linear velocity to set. shape = (data.shape, 3)
        
        Note:
          This method only updates the dof velocity array.
        """
    def set_global_angular_velocity(self, data:SceneData, vel:typing.Any) -> None:
        r"""
        Set the global angular velocity of the floating base to dof velocity array directly.
        
        Args:
            data (SceneData): The scene data to store the velocity.
            vel (ArrayLink[float]): The global angular velocity to set. shape = (data.shape, 3)
        
        Note:
            This method only updates the dof velocity array.
        """
    def set_local_angular_velocity(self, data:SceneData, vel:typing.Any) -> None:
        r"""
        Set the local angular velocity of the floating base to dof velocity array directly.
        
        Args:
            data (SceneData): The scene data to store the velocity.
            vel (ArrayLink(float)): The local angular velocity, shape = (data.shape, 3).
        
        Note:
            This method only updates the dof velocity array.
        """

class Geom:
    r"""
    The Geom object represents a geometry in the scene.
    
    This class provides access to the properties and state of a geometry in the scene.
    It allows you to retrieve information about the geom and colliders belong to it.
    """
    model: SceneModel
    r"""
    SceneModel: The scene model that this geom belongs to.
    """
    index: builtins.int
    r"""
    int: The index of the geom in the :func:`motrixsim.SceneModel.geoms`.
    """
    name: typing.Optional[builtins.str]
    r"""
    The name of the geom. Must be unique within the scene.
    
    Returns:
        Optional[str]: The name of the geom, or "None" if not set.
    """
    def get_pose(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the world pose of the geom.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: shape = `(*data.shape, 7)`. Each pose is represented as a 7 elements
                with `[x, y, z, i, j, k, w]` format.
        """
    def get_linear_velocity(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the world linear velocity of the geom.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]:  shape = `(*data.shape, 3)`. The last axis is the linear velocity with
                `[vx, vy, vz]` format.
        """
    def get_angular_velocity(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the world angular velocity of the geom.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: shape = `(*data.shape, 3)`. The last axis is the angular velocity with
                `[wx, wy, wz]` format.
        """

class HField:
    r"""
    The HField object represents a height field terrain in the scene.
    
    This class provides access to height field (terrain) data used for ground interactions,
    terrain following, and surface-based physics. Height fields provide an efficient way
    to represent large terrain surfaces with elevation data.
    """
    model: SceneModel
    r"""
    SceneModel: The scene model that this hfield belongs to.
    """
    index: builtins.int
    r"""
    int: The index of the hfield in the scene.
    """
    name: typing.Optional[builtins.str]
    r"""
    The name of the hfield. Must be unique within the scene.
    
    Returns:
        Optional[str]: The name of the hfield, or "None" if not set.
    """
    nrow: builtins.int
    r"""
    int: The number of rows in the height field grid.
    """
    ncol: builtins.int
    r"""
    int: The number of columns in the height field grid.
    """
    height_matrix: numpy.typing.NDArray[numpy.float32]
    r"""
    Get the height matrix data as a numpy array.
    
    Note:
        The returned array is a copy of the internal data. Modifying it will not affect the
        hfield.
    
    Returns:
        NDArray[float]: A 2D numpy array of shape (nrow, ncol) containing the height values.
    """
    bound: numpy.typing.NDArray[numpy.float32]
    r"""
    Get the bounding box of the height field in local space.
    
    Returns:
        NDArray[float]: A 1D numpy array of shape (6,) representing the bounding box
            in the format `[-extent_x, -extent_y, 0, extent_x, extent_y, size_z]`.
    """
    def get(self, row:builtins.int, col:builtins.int) -> builtins.float:
        r"""
        Get the height value at the specified row and column.
        
        Args:
            row (int): The row index (0-based).
            col (int): The column index (0-based).
        Returns:
            float: The height value at the specified grid cell.
        """

class Joint:
    r"""
    The Joint object represents a joint in the scene.
    
    This class provides access to the properties and state of a joint in the scene.
    It allows you to retrieve information about the joint's name, link index, number of DoF
    velocities and positions, and DoF velocity and position addresses.
    """
    model: SceneModel
    r"""
    SceneModel: The scene model this joint belongs to.
    """
    index: builtins.int
    r"""
    int: The index of the joint in the :func:`motrixsim.SceneModel.joints`.
    """
    name: typing.Optional[builtins.str]
    r"""
    Optional[str]: The name of the joint.
    
    Return the name of the joint, or `None` if not set.
    """
    link_index: builtins.int
    r"""
    int: The index of the link this joint is attached to.
    """
    link: Link
    r"""
    Link: The link this joint is attached to.
    """
    num_dof_vel: builtins.int
    r"""
    int: The number of velocity DoFs of the joint.
    """
    num_dof_pos: builtins.int
    r"""
    int: The number of position DoFs of the joint.
    """
    dof_vel_index: builtins.int
    r"""
    int: The velocity DoF address of the joint.
    
    Return the starting index of the velocity DoFs.
    """
    dof_pos_index: builtins.int
    r"""
    int: The position DoF address of the joint.
    
    Return the starting index of the position DoFs.
    """
    range: numpy.typing.NDArray[numpy.float32]
    r"""
    NDArray[float]: The range limits of the joint.
    
    Returns a 2-element array containing the lower and upper bounds of the joint range.
    Array format: [lower_bound, upper_bound]
    If the joint has no limits, returns [f32::NEG_INFINITY, f32::INFINITY].
    
    Example:
        >>> joint.range
        array([[-1.57,  1.57]])  # Hinge joint with ±π/2 limits
    """
    axis: numpy.typing.NDArray[numpy.float32]
    r"""
    NDArray[float]: The motion axis of the joint.
    
    Returns a 3-element array representing the motion axis of the joint in the
    successor body coordinate frame. This is primarily used for hinge and slide joints.
    
    Note:
        The axis is normalized automatically when the joint is created.
        For spherical joints, the axis concept doesn't apply in the same way
        as they have full rotational freedom.
    
    Example:
        >>> joint.axis
        array([0., 0., 1.])  # Hinge joint rotating around Z-axis
        array([1., 0., 0.])  # Slide joint moving along X-axis
    """
    def get_dof_pos(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the DoF positions of the joint.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: The DoF positions. shape = (data.shape, :meth:`num_dof_pos`)
        """
    def get_dof_vel(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the DoF velocities of the joint.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: The DoF velocities. shape = (data.shape, :meth:`num_dof_vel`)
        """
    def set_dof_pos(self, data:SceneData, position:typing.Any) -> None:
        r"""
        Set the DoF positions of the joint.
        
        Args:
            data (SceneData): The scene data to store the new positions.
            position (NDArray[float]): The new DoF positions. shape = (data.shape,
                :meth:`num_dof_pos`)
        """
    def set_dof_vel(self, data:SceneData, velocity:typing.Any) -> None:
        r"""
        Set the DoF velocities of the joint.
        
        Args:
            data (SceneData): The scene data to store the new velocities.
            velocity (NDArray[float]): The new DoF velocities. shape = (data.shape,
                :meth:`num_dof_vel`)
        """

class Link:
    r"""
    The Link object represents a kinematic link in the scene.
    
    This class provides access to the properties and state of a kinematic link in the scene.
    It allows you to retrieve information about the link's name, index, joint indices, number of
    joints, and the joints associated with the link.
    """
    model: SceneModel
    r"""
    SceneModel: The scene model that this link belongs to.
    """
    index: builtins.int
    r"""
    int: The index of the link in the :func:`motrixsim.SceneModel.links`.
    """
    name: typing.Optional[builtins.str]
    r"""
    The name of the link. Must be unique within the scene.
    
    Returns:
        Optional[str]: The name of the link, or "None" if not set.
    """
    joint_indices: builtins.list[builtins.int]
    r"""
    The joint indices of this link in the :func:`motrixsim.SceneModel.joints`.
    
    Returns:
        List[int]: The size of the list must be equal to  :meth:`num_joints`
    """
    num_joints: builtins.int
    r"""
    The number of joints associated with this link.
    
    Returns:
        int: the number of joints associated with this link.
    """
    mass: builtins.float
    r"""
    Get the mass of the link.
    
    Returns:
        Real: The mass of the link.
    """
    center_of_mass: numpy.typing.NDArray[numpy.float32]
    r"""
    Get the center of mass of the link in the link local frame.
    
    Returns:
        NDArray[float]: shape = (3,). The center of mass position
    """
    def joints(self) -> builtins.list[Joint]:
        r"""
        The joints associated with this link.
        
        Returns:
            List[Joint]: A list of joint objects.
        """
    def get_joint(self, index:builtins.int) -> typing.Optional[Joint]:
        r"""
        Get the joint at the specified index if the link has multiple joints.
        
        Args:
            index (int): The local index of the joint.
        
        Returns:
            Optional[Joint]: The joint object, or "None" if not found.
        """
    def get_pose(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the world pose of the link.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: shape = `(*data.shape, 7)`. Each pose is represented as a 7 elements
                with `[x, y, z, i, j, k, w]` format.
        """
    def get_position(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the world position of the link.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: shape = `(*data.shape, 3)`.
        """
    def get_rotation(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the world rotation of the link as a quaternion (i, j, k, w).
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: A numpy array with shape `(*data.shape, 4)`.
        """
    def get_rotation_mat(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the world rotation matrix of the link.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: A numpy array with shape `(*data.shape, 3, 3)`.
        """
    def get_linear_velocity(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the world linear velocity of the link.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]:  shape = `(*data.shape, 3)`. The last axis is the linear velocity with
                `[vx, vy, vz]` format.
        """
    def get_angular_velocity(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the world angular velocity of the link.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: shape = `(*data.shape, 3)`. The last axis is the angular velocity with
                `[wx, wy, wz]` format.
        """
    def set_mass(self, mass:builtins.float) -> builtins.bool:
        r"""
        Set the custom mass for a link.
        
        Args:
            mass (Real): The new mass.
        
        Returns:
            bool: True if the set operation success. False if fail due to the
            setting opearation on a Mocap type link or an internal virtual link.
        
        Note:
           This function change the model directly.
        """

class Mocap:
    r"""
    The Mocap object represents a motion capture body in the scene. it can will participate in the
    collision and apply force to other bodies, but will not be affected by the physics simulation.
    """
    model: SceneModel
    r"""
    SceneModel: The scene model this mocap belongs to.
    """
    body: Body
    r"""
    Body: The body associated with this mocap.
    """
    def set_pose(self, data:SceneData, pose:typing.Any) -> None:
        r"""
        Set the pose of the mocap.
        
        Args:
          data (SceneData): The scene data to store the pose.
          pose (NDArray[float]): The pose to set, as a 7-element array (x, y, z, qx, qy, qz, qw).
            shape = (data.shape,7)
        """

class Options:
    r"""
    The Options object represents the simulation options.
    
    This class is used to configure the simulation options. You can access it through
    `model.options`.
    """
    timestep: builtins.float
    r"""
    float: The delta time for each simulation step.
    
    Raises:
        `ValueError`: The set timestep is not positive.
    """
    gravity: numpy.typing.NDArray[numpy.float32]
    r"""
    NDArray[float]: The gravity vector applied to the simulation.
    
    A numpy array of shape (3,) or a list of three floats representing the  gravity vector.
    """
    max_iterations: builtins.int
    r"""
    int: The maximum number of iterations for the solver.
    
    Raises:
        `ValueError`: The set max iterations is zero.
    """
    solver_tolerance: builtins.float
    r"""
    float: The tolerance for the solver.
    
    Raises:
        `ValueError`: The set tolerance is not positive.
    """
    disable_gravity: builtins.bool
    r"""
    bool: Is the gravity disabled in the simulation?
    """
    disable_contacts: builtins.bool
    r"""
    bool: Is all contact constraints disabled in the simulation?
    """
    disable_impedance: builtins.bool
    r"""
    bool: Is impedance effects disabled in the simulation?
    """
    def __str__(self) -> builtins.str: ...

class SceneData:
    r"""
    The SceneData object represents the simulation state.
    
    This class provides access to the dynamic state of the simulation, including joint positions,
    velocities, and other runtime data. Users can query or modify the simulation state, reset the
    scene to its initial state, and access low-level simulation data for advanced use cases. The
    state can be accessed via properties such as `qpos`, `qvel`, and via methods like `reset()`.
    For advanced control, the `low` property exposes the low-level data object.
    """
    shape: tuple
    r"""
    Tuple[int]: The shape of the data.
    
    If the data is batched, the shape is (batch_size,). If not batched, the shape is ().
    """
    dof_vel: numpy.typing.NDArray[numpy.float32]
    r"""
    NDArray[float]: The dof velocity array of the world.
    
    Array of DoF velocities. shape = `(*data.shape, num_dof_vel)`
    """
    dof_pos: numpy.typing.NDArray[numpy.float32]
    r"""
    NDArray[float]: The dof position array of the world.
    
    Array of DoF positions. shape = `(*data.shape, num_dof_pos)`
    
    Note:
        The dof_pos array contains position coordinates for all degrees of freedom in the
        simulation, with format varying by joint type:
            - **Floating base/free body**: 7 elements [tx, ty, tz, qx, qy, qz, qw]
            - **Ball joint**: 4 elements [qx, qy, qz, qw] for quaternion rotation
            - **Hinge joint**: 1 element for angular position
            - **Slide joint**: 1 element for linear position
        Elements are concatenated in order:
        [floating_base_dofs...,joint1_dofs...,joint2_dofs...,     ...]
    """
    actuator_ctrls: numpy.typing.NDArray[numpy.float32]
    r"""
    NDArray[float]: The all the actuator control values. (Get&Set)
    
    Array of actuator control values. shape = `(*data.shape, num_ctrls)`.
    
    
    Note:
        If the model is created from `MJCF`, the order of the control values matches the order
        of actuators in the MJCF file.
    
    Raises:
        TypeError: When the shape of the setted values is not invalid.
    """
    low: LowData
    r"""
    LowData: The low-level data object for advanced simulation control.
    
    Note:
        Only modify the low-level data if you understand the implications.
        Incorrect modifications may lead to unstable simulation behavior.
    """
    def __new__(cls, model:SceneModel, batch:typing.Sequence[builtins.int]=[]) -> SceneData:
        r"""
        Create a new SceneData object.
        
        Args:
            model (SceneModel): The scene model.
            batch (Tuple[int], optional): If provided, a batched SceneData will be created. It is
            useful when you want to simulate multiple independent instances of the same model in
            parallel.
        
        Returns:
            SceneData: The created scene data object.
        """
    def set_dof_pos(self, dof_pos:typing.Any, model:SceneModel) -> None:
        r"""
        Set the dof position for the whole world data.
        
        Args:
            dof_pos (NDArray[float]): The dof position array to set. shape = `(*data.shape,
                num_dof_pos)`.
            model (SceneModel): The scene model to validate the dof position.
        Raises:
           Exception: When the dof position data is invalid.(e.g. quaternion not normalized)
        
        Note:
            The dof_pos array must follow the same format as the getter method:
                - **Floating base/free body**: 7 elements [tx, ty, tz, qx, qy, qz, qw]
                - **Ball joint**: 4 elements [qx, qy, qz, qw] for quaternion rotation
                - **Hinge joint**: 1 element for angular position
                - **Slide joint**: 1 element for linear position
            Elements should be concatenated in
        order:`[floating_base_dofs...,joint1_dofs...,joint2_dofs...,...]`
        """
    def set_dof_vel(self, dof_vel:typing.Any) -> None:
        r"""
        Set the dof velocity for the whole world data.
        
        Args:
            dof_vel (NDArray[float]): The dof velocity array to set. shape = `(*data.shape,
                num_dof_vel)`.
        """
    def reset(self, model:SceneModel) -> None:
        r"""
        Reset the scene data with the given model.
        
        Reinitializes all simulation state variables using the provided model.
        
        Args:
            model (SceneModel): The scene model to reset the data with.
        """
    def __getitem__(self, index:typing.Any) -> SceneData: ...
    def get(self, index:typing.Any) -> SceneData:
        r"""
        Get sub-data by index. Alias to `__getitem__`
        
        Args:
            index (int | ndarray[bool] | DisjointIndices): The index to select. Following types are
        supported:
                 - int: Select a single element. Raise error if the data has no batch dimension.
                 - ndarray[bool]: Select multiple elements based on a boolean mask.
                 - DisjointIndices: Select multiple non-contiguous elements.
        """

class SceneModel:
    r"""
    The SceneModel object represents the entire simulation world.
    
    This class provides a high-level interface to access and manipulate the simulation world model,
    including all bodies, joints, actuators, links, and sites. Users can query the scene structure
    and configuration, modify simulation options, and access components through properties
    (`joints`, `options`) or methods (`get_body()`, `get_sensor_values()`).
    """
    num_dof_vel: builtins.int
    r"""
    int: The number of DoF velocities in the world.
    
    Note:
        This value may be different from the [`num_dof_pos`] because for some joint (like ball
        joint), we use Quaternion to represent the rotation, which has 4 components.
    """
    num_dof_pos: builtins.int
    r"""
    int: The number of DoF positions in the world.
    """
    num_bodies: builtins.int
    r"""
    int: The number of bodies in the world.
    """
    num_links: builtins.int
    r"""
    int: The number of links in the world.
    
    Note:
        The `worldbody` in MJCF is not considered as a link.
    """
    num_geoms: builtins.int
    r"""
    int: The number of geoms in the world.
    """
    num_hfields: builtins.int
    r"""
    int: The number of height fields in the world.
    """
    num_joints: builtins.int
    r"""
    int: The number of joints in the world.
    
    Note:
        `freejoint` in MJCF is not considered as a joint but a floating base.
    """
    num_actuators: builtins.int
    r"""
    int: The number of actuators in the world.
    """
    num_sites: builtins.int
    r"""
    int: The number of sites in the world.
    """
    num_sensors: builtins.int
    r"""
    int: The number of sensors in the world.
    """
    joint_dof_vel_indices: builtins.list[builtins.int]
    r"""
    List[int]: The start dof index for each joint in the dof velocities array.
    
    A list of start indices for each joint's dof velocities in the dof velocities array.
    
    Note:
        The DoF of floating base is not included.
    """
    joint_dof_vel_nums: builtins.list[builtins.int]
    r"""
    List[int]: The size of DoF velocities of each joint.
    
    List of velocity DoF sizes for each joint.
    size = num_joints.
    """
    joint_dof_pos_indices: builtins.list[builtins.int]
    r"""
    List[int]: The start dof index for each joint in the dof positions array.
    
    A list of start indices for each joint's dof positions in the dof positions array.
    size = num_joints.
    
    Note:
        The DoF of floating base is not included.
    """
    joint_dof_pos_nums: builtins.list[builtins.int]
    r"""
    List[int]: The number of DoF positions for each joint.
    
    List of position DoF sizes for each joint.
    size = num_joints
    """
    joint_limits: numpy.typing.NDArray[numpy.float32]
    r"""
    NDArray[float]: The joint position limits for each joint.
    
    A 2-dimensional numpy array with shape (2, num_joints).
    
    The first dimension is the minimum position limit, and the second dimension is the
    maximum position limit.
    If the limits are not set for a joint, `-inf, inf` will be used as the limits.
    """
    options: Options
    r"""
    Options: The simulation options of the model.
    """
    links: builtins.list[Link]
    r"""
    List[Link]: The list of all links in the world.
    """
    geoms: builtins.list[Geom]
    r"""
    List[Geom]: The list of all geoms in the world.
    """
    link_names: builtins.list[typing.Optional[builtins.str]]
    r"""
    List[Optional[str]]: The list of all link names in the world.
    
    A list of link names, can be `None` if the link does not have a name.
    """
    geom_names: builtins.list[typing.Optional[builtins.str]]
    r"""
    List[Optional[str]]: The list of all geoms names in the world.
    
    A list of geom names, can be `None` if the geom does not have a name.
    """
    actuator_ctrl_limits: numpy.typing.NDArray[numpy.float32]
    r"""
    NDArray[float]: The actuator control ranges.
    
    Return a 2-dimensional numpy array with shape (2, num_actuators).
    The first dimension is the minimum control value, and the second dimension is the
    maximum control value.
    If the limits do not set for a actuator, `(-inf, inf)` will be used as the limits.
    """
    actuator_names: builtins.list[typing.Optional[builtins.str]]
    r"""
    List[Optional[str]]: The list of actuator names in the world.
    
    Return list of actuator names, can be `None` if the actuator does not have a name.
    """
    actuators: builtins.list[Actuator]
    r"""
    Get all actuators defined in the model.
    
    Returns:
      List[Actuator]: A list of all actuator objects in the world.
    """
    floating_bases: builtins.list[FloatingBase]
    r"""
    List[FloatingBase]: The list of all floating bases in the world.
    """
    sites: builtins.list[Site]
    r"""
    List[Site]: The list of all sites in the world.
    """
    site_names: builtins.list[builtins.str]
    r"""
    List[str]: The list of all site names in the world.
    """
    joints: builtins.list[Joint]
    r"""
    List[Joint]: The list of all joints in the world.
    """
    joint_names: builtins.list[typing.Optional[builtins.str]]
    r"""
    List[Optional[str]]: The list of all joint names in the world.
    
    Return list of joint names, can be `None` if the joint does not have a name.
    """
    bodies: builtins.list[Body]
    r"""
    List[Body]: The list of all bodies in the world.
    
    Note:
        don't confuse the body in motrixsim with the body in mjcf. See
        :doc:`/user_guide/kinematics/body` for more details.
    """
    body_names: builtins.list[typing.Optional[builtins.str]]
    r"""
    List[Optional[str]]: The list of all body names in the world.
    
    Return list of body names, can be `None` if the body does not have a name.
    """
    low: LowSceneModel
    r"""
    LowSceneModel: The low-level model for advanced or internal simulation access.
    
    This property exposes the underlying low-level scene model, which provides direct access
    to internal simulation data and advanced features.
    
    Note:
        Do not use this property unless you know what you are doing.
    """
    cameras: builtins.list[Camera]
    r"""
    All the cameras in the scene.
    """
    def get_link_poses(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the world poses of all links.
        
        Args:
            data (SceneData): Scene data.
        
        Returns:
            NDArray[float]: A numpy array with shape `(*data.shape,num_links, 7)`. Each pose is
            composed of `[x, y, z, i, j, k, w]`,
        """
    def get_link_rotation_mats(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get all link rotation matrices.
        
        Args:
            data (SceneData): Scene data.
        
        Returns:
            NDArray[float]: A numpy array with shape `(*data.shape,num_links, 3, 3)`. Each rotation
        matrix is in column-major order.
        """
    def get_link_index(self, name:builtins.str) -> typing.Optional[builtins.int]:
        r"""
        Get the link index by its name.
        
        Args:
            name (str): Name of the link.
        
        Returns:
            Optional[int]: Index of the link, or `None` if not found.
        """
    def get_link(self, arg:typing.Any) -> typing.Optional[Link]:
        r"""
        Get a link by name or index.
        
        Args:
            key (str or int): Name or index of the link.
        
        Returns:
            Optional[Link]: The link object, or `None` if not found.
        """
    def get_geom(self, arg:typing.Any) -> typing.Optional[Geom]:
        r"""
        Get a geom by name or index.
        
        Args:
            key (str or int): Name or index of the geom.
        
        Returns:
            Optional[Geom]: The geom object, or `None` if not found.
        """
    def get_hfield_index(self, name:builtins.str) -> typing.Optional[builtins.int]:
        r"""
        Get hfield index by its name.
        
        Args:
            name (str): Name of the hfield.
        
        Returns:
            Optional[int]: Index of the hfield, or `None` if not found.
        """
    def get_hfield(self, slf:SceneModel, arg:typing.Any) -> typing.Optional[HField]:
        r"""
        Get an hfield by name or index.
        
        Args:
            key (str or int): Name or index of the hfield.
        
        Returns:
            Optional[HField]: The hfield object, or `None` if not found.
        """
    def get_actuator_index(self, name:builtins.str) -> typing.Optional[builtins.int]:
        r"""
        Get actuator index by its name.
        
        Args:
            name (str): Name of the actuator.
        
        Returns:
            Optional[int]: Index of the actuator, or `None` if not found.
        """
    def get_actuator(self, arg:typing.Any) -> typing.Optional[Actuator]:
        r"""
        Get an actuator by name or index.
        
        Args:
            key (str or int): Name or index of the actuator.
        
        Returns:
            Optional[Actuator]: The actuator object, or `None` if not found.
        """
    def get_sensor_value(self, id:builtins.str, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the value of a specific sensor by its ID.
        
        Args:
            id (str): Sensor ID.
            data (SceneData): Scene data.
        
        Returns:
            NDArray[float]: Sensor values. shape = `(*data.shape, sensor_value_size)`
        """
    def get_actuator_ctrls(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Alias to :meth:`SceneData.actuator_ctrls`
        """
    def get_site_index(self, name:builtins.str) -> typing.Optional[builtins.int]:
        r"""
        Get site index by name.
        
        Args:
            name (str): Name of the site.
        
        Returns:
            Optional[int]: Index of the site, or `None` if not found.
        """
    def get_site(self, key:typing.Any) -> typing.Optional[Site]:
        r"""
        Get a site by name or index.
        
        Args:
            key (str or int): Name or index of the site.
        
        Returns:
            Optional[Site]: The site object, or `None` if not found.
        """
    def get_joint_index(self, name:builtins.str) -> typing.Optional[builtins.int]:
        r"""
        Get the joint index by its name.
        
        Args:
            name (str): Name of the joint.
        
        Returns:
            Optional[int]: Index of the joint, or `None` if not found.
        """
    def get_joint(self, key:typing.Any) -> typing.Optional[Joint]:
        r"""
        Get a joint by name or index.
        
        Args:
            key (str or int): Name or index of the joint.
        
        Returns:
            Optional[Joint]: The joint object, or `None` if not found.
        """
    def get_body(self, key:typing.Any) -> typing.Optional[Body]:
        r"""
        Get a body by name or index.
        
        Args:
            key (str or int): Name or index of the body.
        
        Returns:
            Optional[Body]: The body object, or `None` if not found.
        """
    def get_body_index(self, name:builtins.str) -> typing.Optional[builtins.int]:
        r"""
        Get the body index by its name.
        
        Args:
            name (str): Name of the body.
        
        Returns:
            Optional[int]: Index of the body, or `None` if not found.
        """
    def get_geom_index(self, name:builtins.str) -> typing.Optional[builtins.int]:
        r"""
        Get the geometry index by its name.
        
        Args:
            name (str): Name of the geometry.
        
        Returns:
            Optional[int]: Index of the geometry, or `None` if not found.
        """
    def get_contact_query(self, data:SceneData) -> ContactQuery:
        r"""
        Get a contact query object for the current model and data.
        
        Args:
           data (SceneData): Scene data.
        
        Returns:
          ContactQuery: A contact query object that can be used to query contacts in the world.
        """
    def compute_init_dof_pos(self) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Compute the initial DoF positions for the world.
        
        Returns:
            NDArray[float]: shape=(num_dof_pos,). Initial DoF positions.
        """
    def step(self, data:SceneData) -> None:
        r"""
        Advance the simulation by one step using the current model and data.
        
        Note:
            If the data has batch dimension, motrixsim will run simulation in parallel
        """
    def forward_kinematic(self, data:SceneData) -> None:
        r"""
        Perform forward kinematic calculations using the current model and data.
        
        Note:
          This method only updates the world poses of all links and bodies based on the current
          joint positions.
        """

class Site:
    r"""
    The Site object represents a reference point or marker in the scene.
    """
    index: builtins.int
    r"""
    int: The index of the site in the site list.
    """
    model: SceneModel
    r"""
    The model that this site belongs to.
    """
    parent_link: typing.Optional[Link]
    r"""
    Link: The parent link of the site, or `None` if the site is attached to the world frame.
    """
    name: typing.Optional[builtins.str]
    r"""
    Optional[str]: The name of the site, or `None` if not set.
    """
    local_pos: numpy.typing.NDArray[numpy.float32]
    r"""
    NDArray[float]: The local position of the site in the parent frame in (x, y, z).
    """
    local_quat: numpy.typing.NDArray[numpy.float32]
    r"""
    NDArray[float]: The local orientation of the site as a quaternion (i, j, k, w).
    """
    def get_pose(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the pose of the site in the world frame.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: The pose of the site in the world frame. shape = `(*data.shape,7)`. The
            last axis is 7-element array with `[x, y, z, i, j, k, w]`.
        """
    def get_position(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the position of the site in the world frame.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: The position of the site in the world frame. shape = `(*data.shape,3)`.
        """
    def get_rotation_mat(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the rotation matrix of the site in the world frame.
        
        Args:
            data (SceneData): The scene data to query.
        
        Returns:
            NDArray[float]: The rotation matrix of the site in the world frame. shape =
                `(*data.shape,3,3)`.
        """

def forward_kinematic(model:SceneModel, data:SceneData) -> None:
    r"""
    Run forward kinematic only.
    
    Args:
        model (SceneModel): The scene model.
        data (SceneData): The scene data.
    """

def load_mjcf_str(mjcf:builtins.str) -> SceneModel:
    r"""
    Load a model from a string containing MJCF data.
    
    Args:
       mjcf (str): The MJCF data as a string.
    
    Returns:
       SceneModel: The loaded scene model.
    """

def load_model(path:builtins.str) -> SceneModel:
    r"""
    Load a model from the given file path.
    
    Args:
        path (str): The path to the model file.
        currently mjcf and urdf are supported.
    
    Returns:
        SceneModel: The loaded scene model.
    """

def step(model:SceneModel, data:SceneData) -> None:
    r"""
    Advance the simulation by one step.
    
    Args:
        model (SceneModel): The scene model.
        data (SceneData): The scene data.
    """

