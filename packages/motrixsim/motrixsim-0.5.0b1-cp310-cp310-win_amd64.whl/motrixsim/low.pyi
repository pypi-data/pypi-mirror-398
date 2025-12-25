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
from enum import Enum

class ActuatorDesc:
    r"""
    Actuator description for low-level actuators.
    
    This class provides access to the properties and state of the actuator description.
    It allows you to retrieve information about the target, integration method, gain type, gain,
    bias, gear, force range, and control range.
    """
    target: ActuatorTarget
    r"""
    ActuatorTarget: The target of the actuator.
    """
    integration: IntegrationType
    r"""
    IntegrationType: The integration method of the actuator.
    """
    gain: builtins.list[builtins.float]
    r"""
    List[float]: The gain parameters (3 elements).
    """
    bias: builtins.list[builtins.float]
    r"""
    List[float]: The bias parameters (3 elements).
    """
    gear: builtins.list[builtins.float]
    r"""
    List[float]: The gear parameters (3 elements).
    """
    force_range: builtins.list[builtins.float]
    r"""
    List[float]: The force range [min, max].
    """
    control_range: builtins.list[builtins.float]
    r"""
    List[float]: The control range [min, max].
    """

class ActuatorTarget:
    r"""
    Actuator target information for low-level actuators.
    
    This class provides access to the properties and state of the actuator target.
    It allows you to retrieve information about the target type and index.
    """
    target_type: builtins.str
    r"""
    str: The type of the actuator target ("floating_base", "joint", "tendon").
    """
    target_id: builtins.int
    r"""
    int: The index of the target.
    """

class Collider:
    r"""
    Collider object representing a collision shape in the scene.
    """
    parent: Entity
    r"""
    Entity: The parent entity (link or mocap).
    """
    shape: builtins.int
    r"""
    Shape: The shape type of the collider, see [`PyShape`].
    """
    size: builtins.list[builtins.float]
    r"""
    List[float]: The size of the shape (3 elements).
    
    Shape-specific size interpretations:
    - Sphere: [radius, 0.0, 0.0]
    - Cylinder: [half_height, radius, 0.0]
    - Capsule: [half_height, radius, 0.0] (half_height is the distance between sphere centers)
    - Cuboid: [half_extents_x, half_extents_y, half_extents_z]
    - InfinitePlane: [0.0, 0.0, 0.0]
    """
    translation: builtins.list[builtins.float]
    r"""
    List[float]: The translation of the collider relative to its parent (3 elements).
    """
    rotation: builtins.list[builtins.float]
    r"""
    List[float]: The rotation of the collider relative to its parent (4 elements).
    """
    priority: builtins.int
    r"""
    int: The collision priority.
    """
    contact_force: ForceDesc
    r"""
    ForceDesc: The contact force model.
    """
    friction: builtins.list[builtins.float]
    r"""
    List[float]: The friction coefficients (3 elements).
    """
    mask: CollisionMask
    r"""
    CollisionMask: The collision mask.
    """
    asset_index: builtins.int
    r"""
    int: The asset index for HField or mesh shapes.
    """
    mesh_scale: builtins.list[builtins.float]
    r"""
    mesh_scale: scaler of mesh asset
    """
    margin: builtins.float
    r"""
    float: Distance threshold for detecting contacts.
    """
    gap: builtins.float
    r"""
    float: Distance band that determines which contacts generate solver constraints.
    """
    condim: builtins.int
    r"""
    int: Contact constraint dimensionality, the maximum condim of the two geoms involved in the
    contact.
    """
    force_mix: builtins.float
    r"""
    float: The mixing factor for the contact force.
    """

class ColliderBound:
    r"""
    Represents the bounding box of a collider.
    """
    min: builtins.list[builtins.float]
    r"""
    List[float]: The minimum corner of the bounding box (3 elements).
    """
    max: builtins.list[builtins.float]
    r"""
    List[float]: The maximum corner of the bounding box (3 elements).
    """
    collider_index: builtins.int
    r"""
    int: The index of the collider this bound belongs to.
    """
    is_plane: builtins.bool
    r"""
    bool: Whether this bound represents an infinite plane.
    """

class CollisionMask:
    r"""
    Collision mask for filtering collisions between groups.
    """
    group: builtins.int
    r"""
    int: The collision group.
    """
    collide_with: builtins.int
    r"""
    int: The collision mask for which groups to collide with.
    """

class ConstraintDebugData:
    r"""
    Debug data for simulation constraints.
    
    This class provides access to the properties and state of the simulation constraints.
    It allows you to retrieve information about the number of unilateral constraints,
    equality constraints, and active contacts.
    """
    num_equations: builtins.int
    r"""
    int: The number of unilateral constraints.
    """
    num_unilaterals: builtins.int
    r"""
    int: The number of unilateral constraints.
    """
    num_active_contacts: builtins.int
    r"""
    int: The number of active contacts.
    """

class ConvexHull:
    r"""
    Represents a convex hull computed from a set of 3D points.
    
    A convex hull is the smallest convex shape that contains all the input points.
    This structure contains the geometric information needed to represent the hull,
    including vertices, faces, and bounding planes.
    """
    points: builtins.list[builtins.list[builtins.float]]
    r"""
    List[List[float]]: The vertices of the convex hull.
    Each inner list contains 3 elements [x, y, z] representing a 3D point.
    """
    bounding_planes: builtins.list[HullPlane]
    r"""
    List[HullPlane]: The bounding planes of the convex hull.
    Each plane defines a face of the hull using its normal vector and offset.
    """
    face_vertex_indices: builtins.list[builtins.int]
    r"""
    List[int]: The vertex indices for all faces of the hull.
    This is a flattened list where every 3 consecutive indices form a triangular face.
    """
    face_indices_start: builtins.list[builtins.int]
    r"""
    List[int]: The starting index for each face in the face_vertex_indices array.
    Used to efficiently access individual faces from the flattened vertex indices.
    """
    center: builtins.list[builtins.float]
    r"""
    List[float]: The center point of the convex hull (3 elements: x, y, z).
    This is the centroid of all hull vertices.
    """
    volume: builtins.float
    r"""
    float: The volume of the convex hull.
    This represents the 3D volume enclosed by the hull.
    """

class DofLimit:
    r"""
    Position limit information for a degree of freedom (DoF).
    
    This class represents the position limit information for a degree of freedom (DoF) in the
    simulation. It allows you to set the lower and upper position limits, and the force model
    for the limit.
    """
    dof_pos_index: builtins.int
    r"""
    int: The position index of the DoF.
    """
    dof_vel_index: builtins.int
    r"""
    int: The velocity index of the DoF.
    """
    lower: builtins.float
    r"""
    float: The lower position limit.
    """
    upper: builtins.float
    r"""
    float: The upper position limit.
    """
    force: ForceDesc
    r"""
    ForceDesc: The force model for the limit.
    """

class DofSpringDrive:
    r"""
    Spring drive parameters for a degree of freedom (DoF).
    
    This class represents the spring drive parameters for a degree of freedom (DoF) in the
    simulation. It allows you to set the target position, stiffness, damping, and integration type
    for the DoF.
    """
    dof_pos_index: builtins.int
    r"""
    int: The position index of the DoF.
    """
    dof_vel_index: builtins.int
    r"""
    int: The velocity index of the DoF.
    """
    target_pos: builtins.float
    r"""
    float: The target position.
    """
    stiffness: builtins.float
    r"""
    float: The spring stiffness.
    """
    damping: builtins.float
    r"""
    float: The damping coefficient.
    """
    acceleration_mode: builtins.bool
    r"""
    bool: Whether acceleration mode is enabled.
    """
    integration_type: IntegrationType
    r"""
    IntegrationType: The integration type used.
    """

class DofTendon:
    r"""
    DoF tendon in the simulation.
    
    This class represents a tendon that connects to multiple degrees of freedom
    through a series of tendon nodes. The tendon can apply forces across
    multiple DOFs based on the node weights and connections.
    """
    nodes: builtins.list[DofTendonNode]
    r"""
    List[DofTendonNode]: The list of tendon nodes that define the tendon connections.
    """

class DofTendonNode:
    r"""
    DoF tendon node in the simulation.
    
    This class represents a single node in a DoF (Degree of Freedom) tendon,
    which connects a tendon to specific degrees of freedom in the model.
    Each node specifies which DOF to connect to and with what weight.
    """
    dof_pos_index: builtins.int
    r"""
    int: The index of the degree of freedom position.
    """
    dof_vel_index: builtins.int
    r"""
    int: The index of the degree of freedom velocity.
    """
    weight: builtins.float
    r"""
    float: The weight coefficient for this tendon node connection.
    """

class Entity:
    r"""
    Entity object representing either a link or a mocap body in the simulation.
    
    This class represents either a link or a mocap body in the simulation.
    """
    ty: builtins.str
    r"""
    str: The type of the entity, either "link" or "mocap".
    """
    index: builtins.int
    r"""
    int: The index of the link or mocap in the model.
    """

class EqualityConnect:
    r"""
    Equality connect constraint in the simulation.
    
    This class provides access to the properties and state of the equality connect constraint.
    It allows you to retrieve information about the active state, entity indices, force model,
    anchor positions, and constraint value.
    """
    active: builtins.bool
    r"""
    bool: Whether the constraint is active.
    """
    entity_a: Entity
    r"""
    Entity: The index of the first entity.
    """
    entity_b: Entity
    r"""
    Entity: The index of the second entity.
    """
    force_model: ForceDesc
    r"""
    ForceDesc: The force model of the constraint.
    """
    anchor_a: builtins.list[builtins.float]
    r"""
    List[float]: The anchor position of the first entity(3 elements).
    """
    anchor_b: builtins.list[builtins.float]
    r"""
    List[float]: The anchor position of the second entity(3 elements).
    """

class EqualityJoint:
    r"""
    Equality constraint for joints in the simulation.
    
    This class provides access to the properties and state of the equality joint constraint.
    It allows you to retrieve information about the active state, joint indices, constraint force,
    and polynomial coefficients.
    """
    active: builtins.bool
    r"""
    bool: Whether the constraint is active.
    """
    joint_a: builtins.int
    r"""
    int: The index of the first joint.
    """
    joint_b: typing.Optional[builtins.int]
    r"""
    int: The index of the second joint, or None if the constraint is between a joint and a
    fixed entity.
    """
    constraint_force: ForceDesc
    r"""
    ForceDesc: The force model of the constraint.
    """
    polycoeff: builtins.list[builtins.float]
    r"""
    List[float]: The polynomial coefficients of the constraint(5 elements).
    """

class EqualityWeld:
    r"""
    Equality weld constraint in the simulation.
    
    This class provides access to the properties and state of the equality weld constraint.
    It allows you to retrieve information about the active state, entity indices, force model,
    anchor positions, relative rotation, and torque scale.
    """
    active: builtins.bool
    r"""
    bool: Whether the constraint is active.
    """
    entity_a: Entity
    r"""
    Entity: The index of the first entity.
    """
    entity_b: Entity
    r"""
    Entity: The index of the second entity.
    """
    force_model: ForceDesc
    r"""
    ForceDesc: The force model of the constraint.
    """
    anchor_a: builtins.list[builtins.float]
    r"""
    List[float]: The anchor position of the first entity(3 elements).
    """
    anchor_b: builtins.list[builtins.float]
    r"""
    List[float]: The anchor position of the second entity(3 elements).
    """
    relative_rotation: builtins.list[builtins.float]
    r"""
    List[float]: The relative rotation of the second entity(4 elements).
    """
    torque_scale: builtins.float
    r"""
    float: The torque scale of the constraint.
    """

class ForceDesc:
    r"""
    Force model description for constraints or limits.
    
    This class represents the force model description for constraints or limits in the simulation.
    It allows you to set the type of force model and the coefficients for the force model.
    """
    force_type: ForceType
    r"""
    ForceType: The type of force model.
    """
    coeff: builtins.list[builtins.float]
    r"""
    List[float]: The coefficients for the force model (length 7).
    """

class FrictionLoss:
    r"""
    Friction loss information for a degree of freedom (DoF) in the simulation.
    """
    dof_vel_index: builtins.int
    r"""
    int: The velocity index of the DoF.
    """
    friction_loss: builtins.float
    r"""
    float: The friction loss value for the DoF.
    """

class HullPlane:
    r"""
    Represents a plane that bounds a convex hull.
    
    A hull plane is defined by its normal vector and an offset distance from the origin.
    The plane equation is: normal · point + offset = 0
    """
    normal: builtins.list[builtins.float]
    r"""
    List[float]: The normal vector of the plane (3 elements: x, y, z).
    The normal vector points outward from the convex hull.
    """
    offset: builtins.float
    r"""
    float: The offset distance of the plane from the origin.
    Used in the plane equation: normal · point + offset = 0
    """

class LinkLower:
    r"""
    LinkLower
    
    This class represents a link in the simulation.
    """
    ty: builtins.str
    r"""
    str: The low-level entity type, could be "link" or "mocap".
    """
    index: builtins.int
    r"""
    int: The index of lower "link" or "mocap"
    """
    num: builtins.int
    r"""
    int: When lower type is "link", there maybe multiple lower links for a high-level
    link; When lower type is "mocap", this is always 1.
    """
    l2h_transform: builtins.list[builtins.float]
    r"""
    List[float]: first 3 elements are the translation, next 4 elements are the
    quaternion rotation. Only valid when ty is "link".
    """

class LowContact:
    r"""
    Low-level contact information between two colliders in the simulation.
    
    This class provides low-level access to the contact information between two colliders in the
    simulation. It allows you to retrieve information about the colliders involved, the contact
    normal, and the penetration depth.
    """
    collider_index_a: builtins.int
    r"""
    int: The index of the first collider.
    """
    collider_index_b: builtins.int
    r"""
    int: The index of the second collider.
    """
    normal: builtins.list[builtins.float]
    r"""
    List[float]: The contact normal vector [x, y, z].
    """
    depth: builtins.float
    r"""
    float: The penetration depth at the contact point.
    """
    def __repr__(self) -> builtins.str: ...

class LowData:
    r"""
    Low-level simulation data object.
    
    This class provides low-level access to the simulation data, including DoF positions,
    velocities, and other low-level data.
    """
    dof_positions: numpy.typing.NDArray[numpy.float32]
    r"""
    ndarray[float]: The DoF positions.
    
    Get the DoF positions with low-level data.
    
    Note:
        The dof_positions array contains the position coordinates for all degrees of freedom
        in the simulation, concatenated in order. The format composition varies by joint type:
            - **Floating base/free body**: 7 elements [tx, ty, tz, qx, qy, qz, qw] where
              tx,ty,tz
          are translation coordinates and qx,qy,qz,qw form a quaternion (with qw as the
          scalar/last element)
            - **Ball joint**: 4 elements [qx, qy, qz, qw] representing quaternion rotation
            - **Hinge joint**: 1 element representing angular position around the joint axis
            - **Slide joint**: 1 element representing linear position along the joint axis
        The array format is: [floating_base_dofs..., joint1_dofs..., joint2_dofs..., ...]
        where joints are ordered according to their indices in the model.
    
    Example:
        For a model with floating base + ball joint + slide joint:
        ```text
        dof_pos = [tx, ty, tz, qx, qy, qz, qw,  // 7 for floating base
                   qx, qy, qz, qw,            // 4 for ball joint
                   pos]                       // 1 for slide joint
        Total length = 12 elements
        ```
    """
    dof_velocities: numpy.typing.NDArray[numpy.float32]
    r"""
    ndarray[float]: The DoF velocities.
    
    Get the DoF velocities with low-level data.
    """
    def set_dof_positions_unchecked(self, pos:typing.Any) -> None:
        r"""
        Set the DoF positions with low-level data.
        
        Args:
            pos (ndarray[float]): The DoF positions.
        
        Note:
            The pos array must follow the same format as `dof_positions`:
                - **Floating base/free body**: 7 elements [tx, ty, tz, qx, qy, qz, qw]
                - **Ball joint**: 4 elements [qx, qy, qz, qw] representing quaternion rotation
                - **Hinge joint**: 1 element for angular position
                - **Slide joint**: 1 element for linear position
            Elements are concatenated in order:
            [floating_base_dofs...,joint1_dofs...,joint2_dofs...,     ...]
        """
    def get_debug_constraints(self) -> ConstraintDebugData:
        r"""
        ConstraintDebugData: The debug constraints.
        
        Get the debug constraints with low-level data.
        """
    def get_contacts(self) -> builtins.list[LowContact]:
        r"""
        Get the contacts with low-level data.
        
        Returns:
            List[LowContact]: The contacts.
        """

class LowSceneModel:
    r"""
    Low-level scene model.
    
    This class provides low-level access to the scene model, including links, joints, colliders,
    and other low-level data.
    """
    link_joint_translations: builtins.list[builtins.float]
    r"""
    List[float]: The link joint translations of the model in cartesian coordinates
    
    size = num_links * 3.
    """
    link_joint_rotations: builtins.list[builtins.float]
    r"""
    List[float]: The link joint rotations of the model in cartesian coordinates.
    
    A list of 9-element arrays, each representing a 3x3 rotation matrix in column-major order,
    size = num_joints * 9.
    
    Each rotation is represented as a 3x3 matrix in column-major order.
    """
    link_parent_indices: builtins.list[builtins.int]
    r"""
    List[int]: The indices of the parent links of each link.
    
    A list of integers, where each integer is the index of the parent link of the
    corresponding link, size = num_links.
    
    If a link has no parent, the value is -1.
    """
    link_joint_indices: builtins.list[builtins.int]
    r"""
    List[int]: The indices of the joints of each link.
    
    A list of integers, where each integer is the index of the joint of the
    corresponding link, size = num_links.
    
    If a link is fixed, the value is -1.
    """
    link_inertias: builtins.list[builtins.float]
    r"""
    List[float]: The spatial inertias of all links.
    
    size = num_links * 10.
    
    Each spatial inertia consists of 10 elements: mass (1), h (3), inertia (6).
    where:
    - h = mass * center_of_mass.
    - inertia = [Ixx, Iyy, Izz, Ixy, Ixz, Iyz] at the center of mass.
    """
    joint_types: builtins.list[builtins.int]
    r"""
    List[int]: The joint types of all joints.
    
    The type of each joint as an integer.
    """
    joint_axes: builtins.list[builtins.float]
    r"""
    List[float]: The axes of all joints.
    
    size = num_joints * 3.
    
    Each joint has a 3D axis, and we flatten them into a single list.
    """
    joint_dof_pos_indices: builtins.list[builtins.int]
    r"""
    List[int]: The position indices of all joint DoFs.
    
    The position index for each joint DoF.
    """
    joint_dof_vel_indices: builtins.list[builtins.int]
    r"""
    List[int]: The velocity indices of all joint DoFs.
    
    The velocity index for each joint DoF.
    """
    joint_armatures: builtins.list[builtins.float]
    r"""
    List[float]: The armature values of all joints.
    
    The armature value for each joint.
    """
    dof_springs: builtins.list[DofSpringDrive]
    r"""
    List[DofSpringDrive]: The list of all DoF spring constraints in the model.
    
    Return all DoF spring constraints.
    """
    dof_limits: builtins.list[DofLimit]
    r"""
    List[DofLimit]: The list of all DoF position limits in the model.
    
    Return all DoF position limits.
    """
    spherical_limits: builtins.list[SphericalLimit]
    r"""
    List[SphericalLimit]: The list of all spherical angle limits in the model.
    
    Return all spherical angle limits.
    """
    friction_losses: builtins.list[FrictionLoss]
    r"""
    List[FrictionLoss]: The friction losses for all DoFs.
    
    Return the friction loss for each DoF.
    """
    equality_joints: builtins.list[EqualityJoint]
    r"""
    List[EqualityJoint]: The list of all equality joint constraints.
    
    Return all equality joint constraints.
    """
    equality_welds: builtins.list[EqualityWeld]
    r"""
    List[EqualityWeld]: The list of all equality weld constraints.
    
    Return all equality weld constraints.
    """
    equality_connects: builtins.list[EqualityConnect]
    r"""
    List[EqualityConnect]: The list of all equality connect constraints.
    
    Return all equality connect constraints.
    """
    dof_tendons: builtins.list[DofTendon]
    r"""
    List[DofTendon]: The list of all DoF tendons.
    
    Return all DoF tendons.
    """
    tendon_springs: builtins.list[TendonSpringConstraint]
    r"""
    List[TendonSpringConstraint]: The list of all tendon spring constraints.
    
    Return all tendon spring constraints.
    """
    tendon_limits: builtins.list[TendonLimitConstraint]
    r"""
    List[TendonLimitConstraint]: The list of all tendon limit constraints.
    
    Return all tendon limit constraints.
    """
    link_low_maps: builtins.list[LinkLower]
    r"""
    List[LinkLower]: The low-level link mapping for all links.
    """
    colliders: builtins.list[Collider]
    r"""
    List[Collider]: The colliders of the model.
    """
    collider_local_aabbs: builtins.list[ColliderBound]
    meshs: builtins.list[Mesh]
    r"""
    List[Mesh]: The meshs of the model.
    """
    actuators: builtins.list[ActuatorDesc]
    r"""
    List[ActuatorDesc]: The actuators of the model.
    """
    low_sensors: builtins.list[LowSensor]
    r"""
    List[LowSensor]: The low-level sensors of the model.
    """
    mocaps: builtins.list[Mocap]
    r"""
    List[Mocap]: The mocap objects in the model.
    """
    pairs_to_ignore: builtins.list[tuple[builtins.int, builtins.int]]
    r"""
    List[Tuple[int, int]]: The pairs of colliders to ignore.
    """
    def get_sensor_frames(self) -> builtins.list[SensorFrame]:
        r"""
        The sensor frames of the model.
        
        Returns:
            List[SensorFrame]: The sensor frames in the model.
        """
    def get_collider_indices(self, name:builtins.str) -> typing.Optional[builtins.list[builtins.int]]:
        r"""
        Get the collider indices by geom name.
        
        Args:
            name (str): Name of the geom.
        
        Returns:
            Optional[List[int]]: Indices of the colliders belong to the geom, or `None` if not
            found.
        
        Note:
            One high-level geom may decompose into multiple low-level colliders.
        """

class LowSensor:
    r"""
    Low-level sensor object for simulation.
    
    This class provides access to the properties and state of the low-level sensor.
    It allows you to retrieve information about the sensor name, location, reference, and type.
    """
    name: builtins.str
    r"""
    str: The name of the sensor.
    """
    loc: SiteLocation
    r"""
    SiteLocation: The location of the sensor.
    """
    ref_to: RefTo
    r"""
    RefTo: The reference of the sensor.
    """
    type_: SiteSensorType
    r"""
    SiteSensorType: The type of the sensor.
    """

class Mesh:
    r"""
    Mesh struct for collision.
    """
    vertices: builtins.list[builtins.float]
    r"""
    List of vertex coordinates stored sequentially (x, y, z ...).
    Every three f32 values represent a 3D position.
    """
    triangles: builtins.list[builtins.int]
    r"""
    List of triangle indices.
    Every three u32 values form one triangle,
    where each index refers to a vertex in `vertices`.
    """
    bound: builtins.list[builtins.float]
    r"""
    Axis-aligned bounding box of the mesh.
    Stored as [xmin, ymin, zmin, xmax, ymax, zmax].
    """
    name: builtins.str
    r"""
    Mesh name or label, mainly used for debugging or identification.
    """

class Mocap:
    r"""
    Mocap
    
    This class represents a mocap body in the simulation.
    """
    pose: builtins.list[builtins.float]
    r"""
    List[float]: The pose of the mocap in the world frame. 3 for translation, 4 for quaternion
    rotation (7 elements).
    """

class RefTo:
    r"""
    Reference to a location in the simulation.
    
    This class provides access to the properties and state of the reference to a location.
    It allows you to retrieve information about the reference type and ID.
    """
    ref_type: builtins.str
    r"""
    str: The type of the reference.
    """
    ref_id: builtins.int
    r"""
    int: The ID of the reference.
    """

class SensorFrame:
    r"""
    Sensor frame in the simulation.
    
    This class provides access to the properties and state of the sensor frame.
    It allows you to retrieve information about the link index, translation, and rotation.
    """
    link_index: builtins.int
    r"""
    int: The index of the link.
    """
    translation: builtins.list[builtins.float]
    r"""
    List[float]: The translation of the sensor frame(3 elements).
    """
    rotation: builtins.list[builtins.float]
    r"""
    List[float]: The rotation of the sensor frame(9 elements).
    """

class SiteLocation:
    r"""
    Site location in the simulation.
    
    This class provides access to the properties and state of the site location.
    It allows you to retrieve information about the location type and ID.
    """
    location_type: builtins.str
    r"""
    str: The type of the location.
    """
    location_id: builtins.int
    r"""
    int: The ID of the location.
    """

class SiteSensorType:
    r"""
    Site sensor type in the simulation.
    
    This class provides access to the properties and state of the site sensor type.
    It allows you to retrieve information about the sensor type.
    """
    sensor_type: builtins.str
    r"""
    str: The type of the sensor.
    """

class SphericalLimit:
    r"""
    Position limit information for spherical (ball) joints.
    
    Limits the total angular deviation of a spherical joint from its neutral
    orientation. The constraint forms a cone around the joint's reference axis,
    with the limit value specifying the maximum allowed rotation angle (radians).
    """
    dof_pos_index: builtins.int
    r"""
    int: The starting index of this joint's dof positions.
    """
    dof_vel_index: builtins.int
    r"""
    int: The starting index of this joint's dof velocities.
    """
    limit: builtins.float
    r"""
    float: Maximum allowed rotation angle (radians).
    """
    force: ForceDesc
    r"""
    ForceDesc: The force model for the limit.
    """

class TendonLimitConstraint:
    r"""
    Tendon limit constraint in the simulation.
    
    This class defines limits for tendon length or tension. When the tendon
    exceeds the specified limits, constraint forces are applied to maintain
    the constraints.
    """
    tendon_index: builtins.int
    r"""
    int: The index of the tendon this constraint applies to.
    """
    lower: builtins.float
    r"""
    float: The lower limit for the tendon constraint.
    """
    upper: builtins.float
    r"""
    float: The upper limit for the tendon constraint.
    """
    limit_force: ForceDesc
    r"""
    ForceDesc: The force model for the limit constraint.
    """

class TendonSpringConstraint:
    r"""
    Tendon spring constraint in the simulation.
    
    This class defines a spring-damper system for tendon control.
    The tendon will try to maintain the target length using the specified
    stiffness and damping parameters.
    """
    tendon_index: builtins.int
    r"""
    int: The index of the tendon this constraint applies to.
    """
    target_length: builtins.float
    r"""
    float: The target length for the tendon spring.
    """
    stiffness: builtins.float
    r"""
    float: The stiffness coefficient of the spring.
    """
    damping: builtins.float
    r"""
    float: The damping coefficient of the spring-damper system.
    """

class ForceType(Enum):
    r"""
    Enum representing different types of force models.
    
    This enum defines the types of force models that can be used in the simulation.
    """
    Hard = ...
    ForceSpring = ...
    AccelerationSpring = ...
    ImpedanceSpring = ...

class IntegrationType(Enum):
    r"""
    Integration type for simulation.
    """
    Explicit = ...
    r"""
    Explicit integration method.
    """
    ImplicitVelocity = ...
    r"""
    Implicit velocity integration method.
    """
    Implicit = ...
    r"""
    Fully implicit integration method.
    """

class Shape(Enum):
    r"""
    The shape type of a collider.
    
    Enum Values:
        Sphere: A spherical collision shape
        Cylinder: A cylindrical collision shape
        Capsule: A capsule collision shape (cylinder with hemispherical ends)
        Cuboid: A box-shaped collision shape
        InfinitePlane: An infinite plane collision shape
        HField: A height field collision shape for terrain
    """
    Sphere = ...
    r"""
    Sphere shape.
    """
    Cylinder = ...
    r"""
    Cylinder shape.
    """
    Capsule = ...
    r"""
    Capsule shape.
    """
    Cuboid = ...
    r"""
    Cuboid shape.
    """
    InfinitePlane = ...
    r"""
    InfinitePlane shape.
    """
    HField = ...
    r"""
    HField shape.
    """
    Mesh = ...
    r"""
    Mesh shape
    """

    @staticmethod
    def types() -> builtins.list[Shape]:
        r"""
        Returns all shape types as a list.
        
        Returns:
            List[Shape]: All shape types.
        """

    @staticmethod
    def type_names() -> builtins.list[builtins.str]:
        r"""
        Returns all shape type names as a list of strings.
        
        Returns:
            List[str]: All shape type names.
        """

class SpringParamsType(Enum):
    r"""
    Enum representing different types of spring parameters.
    
    This enum defines the types of spring parameters that can be used in the simulation.
    """
    StiffnessDamping = ...
    FrequencyDampingRatio = ...

