"""
Type stubs for PlannerInterface
This file provides type hints and documentation for IDE autocomplete
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
from numpy.typing import NDArray

class Pose:
    """Represents a 3D pose with position and orientation"""
    p: NDArray[np.float64]  # Position [x, y, z]
    q: NDArray[np.float64]  # Quaternion [w, x, y, z]

    def __init__(self) -> None: ...
    def inv(self) -> Pose: ...
    def distance(self, other: Pose) -> float: ...

class GoalType:
    """Enum for goal constraint types"""
    JOINTS: int
    POSE: int

class GoalConstraint:
    """Goal constraint for motion planning"""
    type: GoalType
    joints: List[NDArray[np.float64]]
    poses: List[Pose]

    def __init__(self, type: GoalType, data: List) -> None: ...

class Trajectory:
    """Represents a robot trajectory"""
    positions: List[List[float]]
    velocities: List[List[float]]
    accelerations: List[List[float]]
    times: List[float]

    def __init__(self) -> None: ...

class PlannerInterface:
    """
    Main interface for motion planning with IMS

    Provides methods to:
    - Add/remove robots and objects
    - Create and configure planners
    - Plan single and multi-agent motions
    - Query planning world state
    - Compute forward and inverse kinematics
    - Check collisions
    """

    def __init__(self) -> None:
        """Constructs a default PlannerInterface"""
        ...

    # Robot management
    def add_articulation(
        self,
        name: str,
        end_effector: str,
        urdf_path: str,
        srdf_path: str = "",
        link_names: List[str] = [],
        joint_names: List[str] = [],
        gravity: NDArray[np.float64] = np.array([0, 0, 0]),
        planned: bool = True
    ) -> None:
        """
        Adds an articulation to the planning world

        Args:
            name: name of the articulation
            end_effector: name of the end effector
            urdf_path: path to the URDF file
            srdf_path: path to the SRDF file (default: "")
            link_names: names of the links (default: [])
            joint_names: names of the joints (default: [])
            gravity: gravity vector (default: [0, 0, 0])
            planned: whether the articulation is planned (default: true)
        """
        ...

    def remove_articulation(self, name: str) -> None:
        """
        Removes an articulation from the planning world

        Args:
            name: name of the articulation
        """
        ...

    def set_base_pose(self, name: str, pose: Pose) -> None:
        """
        Sets the base pose of the articulation

        Args:
            name: name of the articulation
            pose: pose of the articulation
        """
        ...

    # Object management
    def add_mesh(
        self,
        name: str,
        mesh_path: str,
        scale: NDArray[np.float64] = np.ones(3),
        pose: Pose = Pose(),
        convex: bool = False
    ) -> None:
        """
        Adds a mesh to the planning world

        Args:
            name: name of the mesh
            mesh_path: path to the mesh file
            scale: scale of the mesh (default: [1, 1, 1])
            pose: pose of the mesh (default: identity)
            convex: whether to load the mesh as a convex mesh (default: false)
        """
        ...

    def add_box(
        self,
        name: str,
        size: NDArray[np.float64],
        pose: Pose = Pose()
    ) -> None:
        """
        Adds a box to the planning world

        Args:
            name: name of the box
            size: size of the box [length, width, height]
            pose: pose of the box (default: identity)
        """
        ...

    def add_sphere(
        self,
        name: str,
        radius: float,
        pose: Pose = Pose()
    ) -> None:
        """
        Adds a sphere to the planning world

        Args:
            name: name of the sphere
            radius: radius of the sphere
            pose: pose of the sphere (default: identity)
        """
        ...

    def add_cylinder(
        self,
        name: str,
        radius: float,
        height: float,
        pose: Pose = Pose()
    ) -> None:
        """
        Adds a cylinder to the planning world

        Args:
            name: name of the cylinder
            radius: radius of the cylinder
            height: height of the cylinder
            pose: pose of the cylinder (default: identity)
        """
        ...

    def remove_object(self, name: str) -> None:
        """
        Removes an object from the planning world

        Args:
            name: name of the object
        """
        ...

    # Planning world queries
    def get_articulation_names(self) -> List[str]:
        """
        Get names of all articulations in the planning world

        Returns:
            List of articulation names
        """
        ...

    def get_object_names(self) -> List[str]:
        """
        Get names of all objects in the planning world

        Returns:
            List of object names
        """
        ...

    def has_articulation(self, name: str) -> bool:
        """
        Check if articulation exists

        Args:
            name: name of the articulation

        Returns:
            True if articulation exists
        """
        ...

    def has_object(self, name: str) -> bool:
        """
        Check if object exists

        Args:
            name: name of the object

        Returns:
            True if object exists
        """
        ...

    def is_articulation_planned(self, name: str) -> bool:
        """
        Check if articulation is being planned

        Args:
            name: name of the articulation

        Returns:
            True if being planned
        """
        ...

    def set_articulation_planned(self, name: str, planned: bool) -> None:
        """
        Set whether articulation is being planned

        Args:
            name: name of the articulation
            planned: whether to plan for this articulation
        """
        ...

    # Object attachment
    def is_object_attached(self, name: str) -> bool:
        """
        Check if object is attached to a robot

        Args:
            name: name of the object

        Returns:
            True if attached
        """
        ...

    def attach_object(
        self,
        name: str,
        art_name: str,
        link_id: int,
        touch_links: Optional[List[str]] = None
    ) -> None:
        """
        Attach object to robot link

        Args:
            name: name of the object
            art_name: name of the articulation
            link_id: index of the link to attach to
            touch_links: optional list of link names that touch the object
        """
        ...

    def detach_object(self, name: str, also_remove: bool = False) -> bool:
        """
        Detach object from robot

        Args:
            name: name of the object
            also_remove: whether to also remove the object from the world

        Returns:
            True if successful
        """
        ...

    def detach_all_objects(self, also_remove: bool = False) -> bool:
        """
        Detach all attached objects

        Args:
            also_remove: whether to also remove objects from the world

        Returns:
            True if successful
        """
        ...

    # Collision checking
    def is_state_colliding(self, articulation_name: str = "") -> bool:
        """
        Check if current state is in collision

        Args:
            articulation_name: optional name of specific articulation to check

        Returns:
            True if collision detected
        """
        ...

    def is_robot_colliding_with_objects(self, art_name: str) -> bool:
        """
        Check if robot is colliding with objects

        Args:
            art_name: name of the articulation

        Returns:
            True if collision detected
        """
        ...

    def distance_to_self_collision(self) -> float:
        """
        Get minimum distance to self-collision

        Returns:
            Minimum distance
        """
        ...

    def distance_to_robot_collision(self) -> float:
        """
        Get minimum distance to environment collision

        Returns:
            Minimum distance
        """
        ...

    def distance_to_collision(self) -> float:
        """
        Get minimum distance to any collision

        Returns:
            Minimum distance
        """
        ...

    def set_allowed_collision(self, name1: str, name2: str, allowed: bool) -> None:
        """
        Set allowed collision between two objects

        Args:
            name1: first object name
            name2: second object name
            allowed: whether to allow collision
        """
        ...

    # State management
    def set_qpos(self, name: str, qpos: NDArray[np.float64]) -> None:
        """
        Set joint positions for articulation

        Args:
            name: name of the articulation
            qpos: joint positions
        """
        ...

    def set_qpos_all(self, state: NDArray[np.float64]) -> None:
        """
        Set joint positions for all planned articulations

        Args:
            state: concatenated joint positions
        """
        ...

    def update_attached_bodies_pose(self) -> None:
        """Update poses of all attached bodies based on current robot state"""
        ...

    # Kinematics
    def compute_fk(self, articulation_name: str, qpos: NDArray[np.float64]) -> Pose:
        """
        Compute forward kinematics for an articulation

        Args:
            articulation_name: name of the articulation
            qpos: joint positions (numpy array or list)

        Returns:
            End effector pose
        """
        ...

    def compute_ik(
        self,
        articulation_name: str,
        ee_pose: List[float],
        init_state_val: List[float]
    ) -> Tuple[bool, List[float]]:
        """
        Compute inverse kinematics using CLIK with joint limits

        Args:
            articulation_name: name of the articulation
            ee_pose: desired end effector pose [x, y, z, roll, pitch, yaw]
            init_state_val: initial joint configuration

        Returns:
            Tuple of (success: bool, joint_state: list)
            - success: True if IK succeeded, False otherwise
            - joint_state: resulting joint configuration
        """
        ...

    # Planning
    def make_planner(
        self,
        articulation_names: List[str],
        planner_context: Dict[str, str]
    ) -> None:
        """
        Makes a planner with given articulation names and configuration

        Args:
            articulation_names: names of the articulations
            planner_context: configuration of the planner
                - planner_id: The name of the planner to use
                - heuristic: The name of the heuristic to use
                - weight: Weight for weighted A*
                - time_limit: Maximum planning time in seconds
        """
        ...

    def plan(self, start: List[float], goal_constraint: GoalConstraint) -> Trajectory:
        """
        Plan a motion for a single agent

        Args:
            start: Start state for the agent
            goal_constraint: Goal constraint for the agent

        Returns:
            Planned trajectory
        """
        ...

    def plan_multi(
        self,
        start_states: Dict[str, List[float]],
        goal_constraints: Dict[str, GoalConstraint]
    ) -> Dict[str, Trajectory]:
        """
        Plan motions for multiple agents simultaneously

        Args:
            start_states: Dictionary mapping agent names to their start states
            goal_constraints: Dictionary mapping agent names to their goal constraints

        Returns:
            Dictionary mapping agent names to their planned trajectories
        """
        ...

    # Reset
    def reset(self, reset_robots: bool = True) -> None:
        """
        Reset the planner interface

        Args:
            reset_robots: If true, removes all articulations and objects.
                         If false, only resets planning data (caches, grid) but keeps robots and objects.
        """
        ...

    def print_available_planners(self) -> None:
        """Print list of available planners"""
        ...
