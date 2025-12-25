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

import typing
from motrixsim import SceneModel

def launch(model:typing.Optional[SceneModel]=None, data:typing.Optional[typing.Any]=None, callback:typing.Optional[typing.Any]=None) -> None:
    r"""
    Launch a managed viewer with optional model and data.
    
    This function provides a simplified interface similar to MuJoCo's managed viewer.
    It blocks until the viewer window is closed, automatically handling the physics
    simulation loop and rendering.
    
    Args:
        model (SceneModel, optional): The scene model to simulate and visualize.
                                      If not provided, loads a default sample model.
        data (SceneData, optional): The scene data containing the initial state.
                                    If not provided, creates default data from the model.
        callback (callable, optional): A callback function called at each physics step.
    """

