from typing import Any, List
import ims.pyims as pyims
import numpy as np
import mujoco as mj
import warnings

GENESIS = False
PYBULLET = False
MUJOCO = False
SAPIEN = False
SWIFT = False

# Genesis
try:
    import genesis as gs
    GENESIS = True
except ImportError:
    warnings.warn(
        "Genesis is not installed. To use SRMP with Genesis: pip install genesis-world",
        category=ImportWarning,
        stacklevel=1,
    )

# PyBullet
try:
    import pybullet as p
    import pybullet_data  # optional, but common
    PYBULLET = True
except ImportError:
    warnings.warn(
        "PyBullet is not installed. To use SRMP with PyBullet: pip install pybullet",
        category=ImportWarning,
        stacklevel=1,
    )

# MuJoCo (mujoco-py)
try:
    import mujoco_py as mp
    MUJOCO = True
except ImportError:
    warnings.warn(
        "mujoco-py is not installed. To use SRMP with MuJoCo: pip install mujoco-py",
        category=ImportWarning,
        stacklevel=1,
    )

# SAPIEN
try:
    import sapien
    from sapien import ActorBuilder  # noqa: F401
    SAPIEN = True
except ImportError:
    warnings.warn(
        "SAPIEN is not installed. To use SRMP with SAPIEN: pip install sapien",
        category=ImportWarning,
        stacklevel=1,
    )

# Swift
try:
    import swift
    SWIFT = True
except ImportError:
    warnings.warn(
        "Swift is not installed. To use SRMP with Swift: pip install swift",
        category=ImportWarning,
        stacklevel=1,
    )
class PlannerInterface(pyims.PlannerInterface):
    def __init__(self):
        super().__init__()
        self.planner_list_single_agent = {"wAstar": "Weighted A*",
                             "ARAstar": "Anytime repairing A*",
                             "MHAstar": "Multi-heuristic A*",
                             "wPASE": "Weighted PASE (parallel search)",
                             "Astar": "A*"}
        self.planner_list_multi_agent = {"E-CBS": "Enhanced Conflict-Based Search",
                                         "xECBS":  "Experience Accelerated ECBS"}

    def read_sim(self,
                 sim: Any,
                 sim_type: str,
                 articulations: List[Any] = None):
        """
        Read the simulation world objects from sim of type sim_type
        :param sim: Any, the simulation object
        :param sim_type: str, the type of the simulation object ("sapien", "genesis", "swift", "pybullet", "mujoco")
        :param articulations:
        :return: None
        """
        assert sim_type in ["sapien", "genesis", "swift", "pybullet", "mujoco"], \
            "sim_type should be one of ['sapien', 'genesis', 'swift', 'pybullet', 'mujoco']"
        if sim_type == "sapien":
            self._read_sapien(sim, articulations)
        elif sim_type == "genesis":
            self._read_genesis(sim, articulations)
        elif sim_type == "swift":
            self._read_swift(sim, articulations)
        elif sim_type == "pybullet":
            self._read_pybullet(sim, articulations)
        elif sim_type == "mujoco":
            self._read_mujoco(sim, articulations)

    def _read_sapien(self, sim, articulations: List = None) -> None:
        assert SAPIEN, "Sapien is not installed. If you want to use srmp with Sapien, run ```pip install sapien```"

        # Get the objects in the world.
        mesh_idx = 0
        box_idx = 0
        sphere_idx = 0
        cylinder_id = 0
        for actor in sim.get_all_actors():
            vis_component, coll_component = actor.get_components()
            # for render_shape in vis_component.render_shapes:
            #     if isinstance(render_shape, sapien.render.RenderShapeTriangleMesh):
            #         pose_mesh = actor.get_pose() * render_shape.get_local_pose()
            #         pose_mesh = pyims.Pose(p=np.array(pose_mesh.p), q=np.array(pose_mesh.q))
            #         scale_mesh = render_shape.get_scale()
            #         path_mesh = render_shape.filename
            #         key = (path_mesh, tuple(pose_mesh.p), tuple(pose_mesh.q), tuple(scale_mesh))
            #         if key in added_mesh_path_pose_scale:
            #             continue
            #         added_mesh_path_pose_scale.add(key)
            #         name_mesh = f"mesh_{mesh_idx}"
            #         mesh_idx += 1
            #         self.add_mesh(name_mesh, mesh_path=render_shape.filename, scale=scale_mesh, pose=pose_mesh)

            for coll_shape in coll_component.get_collision_shapes():
                print("Collision shape: ", coll_shape)

                if isinstance(coll_shape, sapien.physx.PhysxCollisionShapeBox):
                    size = [e*2 for e in coll_shape.half_size]
                    # pose_box_local = sapien.Pose(p=coll_shape.half_size, q=[0, 0, 0, 1])
                    pose_box_local = coll_shape.local_pose
                    pose_box = actor.get_pose()  # * pose_box_local
                    pose = pyims.Pose(p=np.array(pose_box.p), q=np.array(pose_box.q))
                    self.add_box("box" + str(box_idx), size, pose)
                    box_idx += 1
                    print("Added", "box" + str(box_idx), "size", size, "pose", pose)

                elif isinstance(coll_shape, sapien.physx.PhysxCollisionShapeSphere):
                    radius = coll_shape.radius
                    pose_sphere_local = coll_shape.local_pose
                    pose_sphere = actor.get_pose()  # * pose_sphere_local
                    pose = pyims.Pose(p=np.array(pose_sphere.p), q=np.array(pose_sphere.q))
                    self.add_sphere("sphere" + str(box_idx), radius, pose)
                    sphere_idx += 1
                    print("Added", "sphere" + str(sphere_idx), "radius", radius, "pose", pose)

                elif isinstance(coll_shape, sapien.physx.PhysxCollisionShapeCylinder):
                    radius = coll_shape.radius
                    height = coll_shape.half_length * 2
                    pose_cylinder_local = coll_shape.local_pose
                    pose_cylinder = actor.get_pose()  # * pose_cylinder_local
                    pose = pyims.Pose(p=np.array(pose_cylinder.p), q=np.array(pose_cylinder.q))
                    self.add_cylinder("cylinder" + str(box_idx), radius, height, pose)
                    cylinder_id += 1
                    print("Added", "cylinder" + str(cylinder_id - 1), "radius", radius, "height", height, "pose", pose)

                elif isinstance(coll_shape, sapien.physx.PhysxCollisionShapePlane):
                    pose_plane_local = coll_shape.local_pose
                    pose_plane = actor.get_pose()  # * pose_plane_local
                    print(actor.get_pose(), "|", pose_plane_local, "|", pose_plane)
                    pose = pyims.Pose(p=np.array(pose_plane.p), q=np.array([1, 0, 0, 0]))
                    # Move the plane slightly down.
                    pose.p[2] -= 0.005
                    self.add_box("plane" + str(box_idx), [10, 10, 0.001], pose)
                    box_idx += 1
                    print("Added", "plane" + str(box_idx - 1), "size", [10, 10, 0.001], "pose", pose)

                elif isinstance(coll_shape, sapien.physx.PhysxCollisionShapeConvexMesh):
                    pose_mesh = actor.get_pose() * coll_shape.get_local_pose()
                    pose_mesh = pyims.Pose(p=np.array(pose_mesh.p), q=np.array(pose_mesh.q))
                    scale = getattr(coll_shape, "get_scale", lambda: np.array([1.0, 1.0, 1.0]))()
                    # get vertices and triangles
                    vertices = coll_shape.get_vertices()
                    triangles = coll_shape.get_triangles()
                    name = f"convex_mesh_{mesh_idx}"
                    self.add_mesh(name, vertices=vertices, triangles=triangles, scale=scale, pose=pose_mesh)
                    mesh_idx += 1
                    print("Added", name, "pose", pose_mesh)

                elif isinstance(coll_shape, sapien.physx.PhysxCollisionShapeTriangleMesh):
                    pose_mesh = actor.get_pose() * coll_shape.get_local_pose()
                    pose_mesh = pyims.Pose(p=np.array(pose_mesh.p), q=np.array(pose_mesh.q))
                    scale = getattr(coll_shape, "get_scale", lambda: np.array([1.0, 1.0, 1.0]))()
                    vertices = coll_shape.get_vertices()
                    triangles = coll_shape.get_triangles()
                    name = f"mesh_{mesh_idx}"
                    self.add_mesh(name, vertices=vertices, triangles=triangles, scale=scale, pose=pose_mesh)
                    mesh_idx += 1
                else:
                    raise ValueError(f"Collision shape type {coll_shape} is not supported")

    def _read_genesis(self, sim, articulations: List = None):
        assert GENESIS, "Genesis is not installed. If you want to use srmp with Genesis, run ```pip install genesis-world```"
        assert isinstance(sim, gs.Scene), "sim should be of type genesis.Scene"
        sim_state = sim.get_state()
        for entity in sim_state.scene.entities:
            if isinstance(entity.morph, gs.morphs.Plane):
                pose = pyims.Pose(p=np.array(entity.base_link.pos) - np.array([0, 0, -0.002]),
                                  q=np.array(entity.base_link.quat))
                self.add_box("plane", [10, 10, 0.001], pose)
            elif isinstance(entity.morph, gs.morphs.Box):
                pose = pyims.Pose(p=np.array(entity.base_link.pos), q=np.array(entity.base_link.quat))
                self.add_box("box" + str(entity.uid), np.array(entity.morph.size), pose)
            elif isinstance(entity.morph, gs.morphs.Mesh):
                pose = pyims.Pose(p=np.array(entity.base_link.pos), q=np.array(entity.base_link.quat))
                self.add_mesh("mesh" + str(entity.uid), mesh_path=entity.morph.file, scale=entity.morph.scale, pose=pose)
            elif isinstance(entity.morph, gs.morphs.Cylinder):
                pose = pyims.Pose(p=np.array(entity.base_link.pos), q=np.array(entity.base_link.quat))
                self.add_cylinder("cylinder" + str(entity.uid), entity.morph.radius, entity.morph.height, pose)
            elif isinstance(entity.morph, gs.morphs.Sphere):
                pose = pyims.Pose(p=np.array(entity.base_link.pos), q=np.array(entity.base_link.quat))
                self.add_sphere("sphere" + str(entity.uid), entity.morph.radius, pose)
            elif isinstance(entity.morph, gs.morphs.MJCF):
                continue #TODO FIX THIS
            elif isinstance(entity.morph, gs.morphs.URDF):
                continue #TODO FIX THIS
            else:
                raise ValueError(f"Entity type {entity.morph} is not supported")

    def _read_swift(self, sim: Any, articulations):
        raise NotImplementedError("Swift simulation is not supported yet")

    def _read_pybullet(self, sim: Any, articulations: List = None):
        if articulations is None:
            articulations = []
        assert PYBULLET, "Pybullet is not installed. If you want to use srmp with Pybullet, run ```pip install pybullet```"
        assert isinstance(sim, int), "sim should be of type int"
        for i in range(p.getNumBodies()):
            body_info = p.getBodyInfo(i)
            body_name = body_info[1].decode("utf-8")
            if body_name in articulations:
                continue
            col_data = p.getCollisionShapeData(i, -1, sim)[0]
            if col_data[2] == p.GEOM_PLANE:
                pose = pyims.Pose(p=np.array([0, 0, -0.0001]), q=np.array([1, 0, 0, 0]))
                self.add_box("plane" + str(i), [30, 30, 0.0001], pose)
            elif col_data[2] == p.GEOM_BOX:
                size = col_data[3]
                position_orientation = p.getBasePositionAndOrientation(i)
                orientation = np.array(position_orientation[1])
                pose = pyims.Pose(p=np.array(position_orientation[0]),
                                  q=orientation[[3, 0, 1, 2]])
                local_pose = pyims.Pose(p=np.array(col_data[5]),
                                        q=np.array([col_data[6][3], col_data[6][0], col_data[6][1], col_data[6][2]]))
                tot_pose = pose * local_pose
                self.add_box(body_name + str(i), np.clip(np.array(size), 0, 40), pose=tot_pose)
            elif col_data[2] == p.GEOM_MESH:
                vis_data = p.getVisualShapeData(i, -1, sim)[0]
                mesh_path = vis_data[4]
                scale = vis_data[3]
                position_orientation = p.getBasePositionAndOrientation(i)
                orientation = np.array(position_orientation[1])
                pose = pyims.Pose(p=np.array(position_orientation[0]),
                                  q=orientation[[3, 0, 1, 2]])
                local_pose = pyims.Pose(p=np.array(col_data[5]),
                                        q=np.array([col_data[6][3], col_data[6][0], col_data[6][1], col_data[6][2]]))
                tot_pose = pose * local_pose
                print(f"Adding mesh {body_name + str(i)} in pose {tot_pose}")
                self.add_mesh(body_name + str(i), mesh_path=mesh_path, scale=scale, pose=pose)
            elif col_data[2] == p.GEOM_CYLINDER:
                height = col_data[3][0]
                radius = col_data[3][1]
                position_orientation = p.getBasePositionAndOrientation(i)
                orientation = np.array(position_orientation[1])
                pose = pyims.Pose(p=np.array(position_orientation[0]),
                                  q=orientation[[3, 0, 1, 2]])
                local_pose = pyims.Pose(p=np.array(col_data[5]),
                                        q=np.array([col_data[6][3], col_data[6][0], col_data[6][1], col_data[6][2]]))
                tot_pose = pose * local_pose
                self.add_cylinder(body_name + str(i), radius, height, pose=tot_pose)
            elif col_data[2] == p.GEOM_SPHERE:
                radius = col_data[3][0]
                position_orientation = p.getBasePositionAndOrientation(i)
                orientation = np.array(position_orientation[1])
                pose = pyims.Pose(p=np.array(position_orientation[0]),
                                  q=orientation[[3, 0, 1, 2]])
                local_pose = pyims.Pose(p=np.array(col_data[5]),
                                        q=np.array([col_data[6][3], col_data[6][0], col_data[6][1], col_data[6][2]]))
                tot_pose = pose * local_pose
                self.add_sphere(body_name + str(i), radius, pose=tot_pose)
            else:
                raise ValueError(f"Collision shape type {col_data[2]} is not supported")


    def _read_mujoco(self, sim: Any, articulations):
        sim_state = sim.get_state()

        for i in range(sim.ngeom):
            geom_type = sim.geom_type[i]
            match geom_type:
                case mj.mjtGeom.mjGEOM_PLANE:
                    pose = pyims.Pose(p=np.array(sim.geom_pos[i]) ,
                                      q=np.array(sim.geom_quat[i]))
                    self.add_box("plane", [10, 10, 0.001], pose)
                case mj.mjtGeom.mjGEOM_HFIELD:
                    raise ValueError(f"Entity type {self.mujoco_geom_type_map[mj.mjtGeom.mjGEOM_HFIELD]} is not supported")
                case mj.mjtGeom.mjGEOM_SPHERE:
                    pose = pyims.Pose(p=np.array(entity.base_link.pos), q=np.array(entity.base_link.quat))
                    self.add_sphere("sphere", entity.morph.radius, pose)
                case mj.mjtGeom.mjGEOM_CAPSULE:
                    raise ValueError(f"Entity type {self.mujoco_geom_type_map[mj.mjtGeom.mjGEOM_CAPSULE]} is not supported")
                case mj.mjtGeom.mjGEOM_ELLIPSOID:
                    raise ValueError(f"Entity type {self.mujoco_geom_type_map[mj.mjtGeom.mjGEOM_ELLIPSOID]} is not supported")
                case mj.mjtGeom.mjGEOM_CYLINDER:
                    pose = pyims.Pose(p=np.array(entity.base_link.pos), q=np.array(entity.base_link.quat))
                    self.add_cylinder("cylinder", entity.morph.radius, entity.morph.height, pose)
                case mj.mjtGeom.mjGEOM_BOX:
                    pose = pyims.Pose(p=np.array(entity.base_link.pos), q=np.array(entity.base_link.quat))
                    self.add_box("box", np.array(entity.morph.size), pose)
                case mj.mjtGeom.mjGEOM_MESH:
                    pose = pyims.Pose(p=np.array(entity.base_link.pos), q=np.array(entity.base_link.quat))
                    self.add_mesh("mesh", mesh_path=entity.morph.file, scale=entity.morph.scale, pose=pose)
                case mj.mjtGeom.mjGEOM_ARROW:
                    raise ValueError(f"Entity type {self.mujoco_geom_type_map[mj.mjtGeom.mjGEOM_ARROW]} is not supported")
                case mj.mjtGeom.mjGEOM_GRID:
                    raise ValueError(f"Entity type {self.mujoco_geom_type_map[mj.mjtGeom.mjGEOM_GRID]} is not supported")
                case mj.mjtGeom.mjGEOM_NONE:
                    continue

            for entity in sim_state.scene.entities:
                if isinstance(entity.morph, gs.morphs.Plane):
                    pose = pyims.Pose(p=np.array(entity.base_link.pos) - np.array([0, 0, -0.002]),
                                      q=np.array(entity.base_link.quat))
                    self.add_box("plane", [10, 10, 0.001], pose)
                elif isinstance(entity.morph, gs.morphs.Box):
                    pose = pyims.Pose(p=np.array(entity.base_link.pos), q=np.array(entity.base_link.quat))
                    self.add_box("box", np.array(entity.morph.size), pose)
                elif isinstance(entity.morph, gs.morphs.Mesh):
                    pose = pyims.Pose(p=np.array(entity.base_link.pos), q=np.array(entity.base_link.quat))
                    self.add_mesh("mesh", mesh_path=entity.morph.file, scale=entity.morph.scale, pose=pose)
                elif isinstance(entity.morph, gs.morphs.Cylinder):
                    pose = pyims.Pose(p=np.array(entity.base_link.pos), q=np.array(entity.base_link.quat))
                    self.add_cylinder("cylinder", entity.morph.radius, entity.morph.height, pose)
                elif isinstance(entity.morph, gs.morphs.Sphere):
                    pose = pyims.Pose(p=np.array(entity.base_link.pos), q=np.array(entity.base_link.quat))
                    self.add_sphere("sphere", entity.morph.radius, pose)
                elif isinstance(entity.morph, gs.morphs.MJCF):
                    continue  # TODO FIX THIS
                elif isinstance(entity.morph, gs.morphs.URDF):
                    continue  # TODO FIX THIS
                else:
                    raise ValueError(f"Entity type {entity.morph} is not supported")

    def print_available_planners(self):
        # print in yellow color
        print("\033[93mAvailable planners:")
        print("  Single-agent planners:")
        for keys, values in self.planner_list_single_agent.items():
            print(f"\033[93m    '{keys}': {values}")
        print("  Multi-agent planners:")
        for keys, values in self.planner_list_multi_agent.items():
            print(f"\033[93m    '{keys}': {values}")
        print("\033[0m")
