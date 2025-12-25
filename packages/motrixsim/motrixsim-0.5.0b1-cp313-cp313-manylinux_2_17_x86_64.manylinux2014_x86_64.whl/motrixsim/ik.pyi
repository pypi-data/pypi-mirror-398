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
from motrixsim import Link, SceneData, SceneModel

class DlsSolver:
    r"""
    Use Damped Least Squares (DLS) method to solve inverse kinematics problem.
    
    DLS is a robust optimization method that adds regularization to handle singular
    configurations and improve numerical stability. It's also known as Levenberg-Marquardt
    for IK applications.
    
    Args:
       max_iter (int): Maximum number of iterations (default: 100).
       step_size (float): Step size for each iteration (default: 0.5).
       tolerance (float): Tolerance for convergence (default: 1e-3).
       damping (float): Damping parameter for regularization (default: 1e-3).
           - Small values (1e-6 to 1e-4): Near Gauss-Newton behavior
           - Medium values (1e-4 to 1e-2): Good balance for most applications
           - Large values (1e-2 to 1.0): More stable but slower convergence
    """
    def __new__(cls, max_iter:builtins.int=100, step_size:builtins.float=0.5, tolerance:builtins.float=0.0010000000474974513, damping:builtins.float=0.0010000000474974513) -> DlsSolver: ...
    def solve(self, ik_model:typing.Any, data:SceneData, target_pose:typing.Any) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Solve the IK problem for the given chain and target pose.
        
        Args:
            ik_model (IkChain): The IK model. Currently only `IkChain` is supported.
            data (SceneData): The scene data containing the current state.
            target_pose (NDarray[float]): The target pose the end effector want to reach.
                It is a 7-element array with (x, y, z, i, j, k, w) format.
        
        Returns:
          A numpy array with shape `(data.shape, ik_model.num_dof_pos + 2,)`. For each row, the
          first element is the number of iterations used, the second element is the final
          residual, and the remaining elements are the solved DOF positions.
        """

class GaussNewtonSolver:
    r"""
    Use gauss newton iterative method to solve inverse kinematics problem.
    
    Args:
       max_iter (int): Maximum number of iterations (default: 100).
       step_size (float): Step size for each iteration (default: 0.5).
       tolerance (float): Tolerance for convergence (default: 1e-3).
    """
    def __new__(cls, max_iter:builtins.int=100, step_size:builtins.float=0.5, tolerance:builtins.float=0.0010000000474974513) -> GaussNewtonSolver: ...
    def solve(self, ik_model:typing.Any, data:SceneData, target_pose:typing.Any) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Solve the IK problem for the given chain and target pose.
        
        Args:
            ik_model (IkChain): The IK model. Currently only `IkChain` is supported.
            data (SceneData): The scene data containing the current state.
                target_pose (NDarray[float]): The target pose the end effector want to reach.  It is
                a 7-element array with (x, y, z, i, j, k, w) format.
        
        Returns:
          A numpy array with shape `(data.shape, ik_model.num_dof_pos + 2,)`. For each row, the
          first element   is the number of iterations used, the second element is the final
          residual, and the   remaining elements are the solved DOF positions.
        """

class IkChain:
    r"""
    Represents a kinematic chain for inverse kinematics (IK) solving.
    
    Args:
        model (SceneModel): The scene model containing the kinematic structure.
        end_link (str): The name of the end link of the IK chain.
        start_link (Optional[str]): The name of the start link of the IK chain. If not provided,
            the root link will be used.
        end_effector_offset (Optional[ndarray]): A 7-element array representing the end-effector
            offset as a pose (x, y, z, i, j, k, w) in end link's local space. If not provided, no
            offset will be applied.
    Raises:
       RuntimeError: If the IK chain contains unsupported joint types. (Currently only hinge and
            slider are supported.)
    """
    num_dof_pos: builtins.int
    r"""
    Get the number of DoF positions in the IK chain.
    
    Returns:
        int: The number of degree of freedom positions.
    """
    num_dof_vel: builtins.int
    r"""
    Get the number of DoF velocities in the IK chain.
    
    Returns:
        int: The number of degree of freedom velocities.
    """
    num_links: builtins.int
    r"""
    Get the number of links in the IK chain.
    
    Returns:
        int: The number of links in the chain.
    """
    def __new__(cls, model:SceneModel, end_link:builtins.str, start_link:typing.Optional[builtins.str]=None, end_effector_offset:typing.Optional[typing.Any]=None) -> IkChain: ...
    def get_dof_pos(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the DoF positions of the IK chain from the simulation data.
        
        Args:
            data (SceneData): The scene data containing the current state.
        
        Returns:
            ndarray: The DoF positions of the chain. shape = `(*data.shape, num_dof_pos)`.
        """
    def get_dof_vel(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the DoF velocities of the IK chain from the simulation data.
        
        Args:
            data (SceneData): The scene data containing the current state.
        
        Returns:
            ndarray: The DoF velocities of the chain. shape = `(*data.shape, num_dof_vel)`.
        """
    def get_end_effector_pose(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the end effector pose in world coordinates.
        
        Args:
            data (SceneData): The scene data containing the current state.
        
        Returns:
            ndarray: The end effector pose array. shape = `(*data.shape, 7)`. Each pose is a
        7-element         array with `[x, y, z, i, j, k, w]` format.
        """
    def get_end_effector_vel(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the end effector velocity in world coordinates.
        
        Args:
            data (SceneData): The scene data containing the current state.
        
        Returns:
            ndarray: The end effector velocity array. shape = `(*data.shape, 6)`. Each velocity is a
        6-element array with first 3 elements representing angular velocity and last 3 elements
        representing linear velocity.
        """
    def get_end_effector_jac(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the Jacobian matrix of the end effector.
        
        Args:
            data (SceneData): The scene data containing the current state.
        
        Returns:
            ndarray: The Jacobian matrix of the end effector. shape = `(*data.shape, 6,
        num_dof_vel)`.         The first 3 rows are angular velocity, the last 3 rows are linear
        velocity.
        """
    def get_end_point_jac(self, data:SceneData, end_point:typing.Any) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the Jacobian matrix of a specific point fixed to the end link.
        
        Args:
            data (SceneData): The scene data containing the current state.
            end_point (ndarray): A 3-element array representing the point in the end link's local
        frame.
        
        Returns:
            ndarray: The Jacobian matrix of the specified point. shape = `(*data.shape, 6,
        num_dof_vel)`.         The first 3 rows are angular velocity, the last 3 rows are linear
        velocity.
        """
    def get_inertial_matrix(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the joint space inertia matrix of the chain.
        
        Args:
            data (SceneData): The scene data containing the current state.
        
        Returns:
            ndarray: The joint space inertia matrix of the chain. shape = `(*data.shape,
        num_dof_vel, num_dof_vel)`.         A symmetric positive definite matrix.
        """
    def get_bias_force(self, data:SceneData) -> numpy.typing.NDArray[numpy.float32]:
        r"""
        Get the joint space bias force of the chain.
        
        Args:
            data (SceneData): The scene data containing the current state.
        
        Returns:
            ndarray: The joint space bias force of the chain. shape = `(*data.shape, num_dof_vel)`.
        """
    def get_link(self, index:builtins.int) -> Link:
        r"""
        Get the link at the specified index in the IK chain.
        
        Args:
            index (int): The index of the link in the chain (0-based).
        
        Returns:
            Link: The link object at the specified index.
        
        Raises:
            IndexError: If the index is out of bounds.
        """

