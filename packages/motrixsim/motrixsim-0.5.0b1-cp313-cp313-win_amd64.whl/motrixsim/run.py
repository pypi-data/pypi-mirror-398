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

import time

from absl import app, flags


def render_loop(
    phys_dt: float,
    render_fps: float,
    phys_step_func: callable,
    render_func: callable,
):
    """
    Execute a synchronous render loop with decoupled physics and rendering frequencies.

    This function implements a frame-pacing algorithm that separates physics simulation
    from rendering, allowing for higher render framerates than physics timesteps while
    maintaining simulation stability and accuracy.

    The loop uses an accumulator pattern to ensure fixed-timestep physics updates
    regardless of rendering performance, preventing "spiral of death" where slow
    rendering would cause physics to fall behind.

    Args:
        phys_dt (float): Fixed timestep duration for physics simulation in seconds.
            Typical values range from 0.001 to 0.004 (250-1000 Hz) for stable
            physics simulation. Smaller values provide more accuracy but increase
            computational cost.

        render_fps (float): Target rendering framerate in frames per second.
            This determines how frequently the render_func will be called.
            Common values: 30.0, 60.0, 120.0, 144.0. The actual framerate may
            be limited by hardware capabilities.

        phys_step_func (callable): Function that advances the physics simulation
            by exactly one timestep (phys_dt). This function should not take any
            parameters and should handle all physics calculations including:
            - Force and torque integration
            - Constraint solving
            - Collision detection and response
            - Actuator control updates

            Example: lambda: model.step(data) or a wrapped physics engine call.

        render_func (callable): Function that renders the current simulation state.
            This function is called once per frame and should handle all visual
            updates including:
            - Camera transformations
            - Mesh rendering and material updates
            - UI drawing
            - Display synchronization

            Example: lambda: renderer.sync(data) or a graphics library render call.

    Note:
        - This function is blocking and will run indefinitely until interrupted
          by keyboard interrupt (Ctrl+C), window close, or other external signals.
        - The physics simulation runs at a fixed timestep regardless of rendering
          performance to maintain deterministic behavior.
        - Multiple physics steps may be executed per frame if rendering is slow.
        - If rendering is faster than the target FPS, the thread sleeps to maintain
          consistent frame timing and reduce CPU usage.
        - The accumulator-based approach ensures temporal consistency - the same
          simulation will produce identical results regardless of rendering performance.

    Time Management:
        The loop maintains two separate timing domains:
        - Physics domain: Fixed timestep, deterministic advancement
        - Rendering domain: Variable timing with target framerate

        Physics accumulator (phys_remain) accumulates real time and consumes
        it in fixed chunks (phys_dt), ensuring physics advances at the correct
        rate even during frame rate fluctuations.

    Example:
        ```python
        # Setup model and renderer
        model = load_model("scene.xml")
        renderer = RenderApp()
        data = SceneData(model)

        # Run synchronous simulation at 1000 Hz physics, 60 Hz rendering
        render_loop(
            phys_dt=0.001,  # 1ms physics timestep = 1000 Hz
            render_fps=60.0,  # 60 FPS rendering
            phys_step_func=lambda: model.step(data),
            render_func=lambda: renderer.sync(data),
        )
        ```

    Performance Characteristics:
        - CPU usage scales with physics complexity and render_fps
        - Sleep time is calculated to maintain target render framerate
        - Physics steps may accumulate if system cannot keep up
        - Designed for real-time interactive applications
    """
    # Initialize physics accumulator with one timestep to start immediately
    phys_remain = phys_dt

    # Calculate target render frame duration from target framerate
    # e.g., render_fps=60.0 -> render_dt=0.0167 seconds per frame
    render_dt = 1.0 / render_fps

    # Record initial physics timing reference point
    phys_t0 = time.monotonic()

    # Main render loop - runs indefinitely until interrupted
    while True:
        # Mark the beginning of current frame for render timing
        render_t0 = time.monotonic()

        # Calculate elapsed real time since last physics update
        # Add this to our physics accumulator
        elapsed_real_time = time.monotonic() - phys_t0
        phys_remain += elapsed_real_time

        # Execute physics steps to catch up with real time
        # This may run zero, one, or multiple physics steps per frame
        # ensuring simulation stays synchronized with real time regardless
        # of rendering performance
        while phys_remain > phys_dt:
            # Execute one fixed-timestep physics simulation step
            phys_step_func()

            # Consume one physics timestep from accumulator
            phys_remain -= phys_dt

        # Update physics timing reference for next frame calculation
        phys_t0 = time.monotonic()

        # Render the current simulation state (once per frame)
        # This visualizes the most recent physics state
        render_func()

        # Calculate how much time we have left before next frame should start
        # If we're running ahead of schedule, sleep to maintain target framerate
        frame_elapsed_time = time.monotonic() - render_t0
        sleep_time = render_dt - frame_elapsed_time

        # Only sleep if we have spare time (prevents negative sleep times)
        if sleep_time > 0:
            time.sleep(sleep_time)
        # If sleep_time <= 0, we're running behind schedule and skip sleep
        # This allows the loop to catch up on the next frame


if __name__ == "__main__":
    _File = flags.DEFINE_string("file", None, "path to model", required=True)
    _Delay = flags.DEFINE_float("delay", 0.0, "delay seconds before starting the simulation", lower_bound=0.0)

    def main(argv):
        import motrixsim

        render_fps = 60.0
        path = _File.value
        print(f"Loading model from {path}")
        with motrixsim.render.RenderApp() as render:
            # Load the scene model
            model = motrixsim.load_model(path)
            # Create the render instance of the model
            render.launch(model)
            # Create the physics data of the model
            data = motrixsim.SceneData(model)

            if _Delay.value > 0.0:
                print(f"Waiting for {_Delay.value} seconds before starting the simulation...")
                time.sleep(_Delay.value)

            render_loop(
                phys_dt=model.options.timestep,
                render_fps=render_fps,
                phys_step_func=lambda: motrixsim.step(model, data),
                render_func=lambda: render.sync(data),
            )

    app.run(main)
