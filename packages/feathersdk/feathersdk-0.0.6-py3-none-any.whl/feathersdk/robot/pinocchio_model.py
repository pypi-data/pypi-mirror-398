"""
Pinocchio model loader for robots.

This module provides PinocchioModel class for loading and managing Pinocchio models
and collision geometry, making them available for multiple tasks (kinematics, dynamics,
collision checking, visualization, etc.).
"""

import logging
import pinocchio as pin
import numpy as np
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class PinocchioModel:
    """
    Reusable Pinocchio model and geometry loader.
    
    This class loads and manages the Pinocchio model and collision geometry,
    making them available for multiple tasks (kinematics, dynamics, collision checking, etc.).
    """
    
    def __init__(
        self, 
        urdf_path: str, 
        package_dir: Optional[str] = None,
        load_collision: bool = True
    ):
        """
        Initialize Pinocchio model from URDF.
        
        Args:
            urdf_path: Path to the URDF file
            package_dir: Directory containing mesh files (for package:// paths)
            load_collision: If True, load collision geometry model
        """
        self.urdf_path = Path(urdf_path)
        
        # Determine package directory
        if package_dir is None:
            # Try to auto-detect: look for package.xml to find the package root
            current = self.urdf_path.parent
            while current != current.parent:  # Stop at filesystem root
                if (current / "package.xml").exists():
                    # Found package root (Nov11_description/)
                    # package_dir should be parent of this
                    self.package_dir = current.parent
                    logger.info(f"Auto-detected package_dir: {self.package_dir}")
                    break
                current = current.parent
            else:
                # Fallback: assume package is 2 levels up from URDF
                self.package_dir = self.urdf_path.parent.parent.parent
                logger.info(f"Using inferred package_dir: {self.package_dir}")
        else:
            self.package_dir = Path(package_dir)
        
        # Load the kinematic model
        self.model = pin.buildModelFromUrdf(str(self.urdf_path))
        self.data = self.model.createData()
        
        # Load collision geometry if requested
        self.geom_model = None
        self.geom_data = None
        if load_collision:
            self._load_collision_geometry()
        
        logger.info(f"✓ Model loaded: {self.model.name}")
        n_frames = getattr(self.model, 'nframes', len(self.model.names))
        logger.info(f"✓ Number of frames: {n_frames}")
        logger.info(f"✓ Number of joints: {self.model.njoints}")
        if self.geom_model:
            logger.info(f"✓ Number of collision geometries: {len(self.geom_model.geometryObjects)}")
    
    def _load_collision_geometry(self):
        """Load collision geometry from URDF."""
        logger.info(f"Loading collision geometry with package_dirs: [{self.package_dir}]")
        
        try:
            self.geom_model = pin.buildGeomFromUrdf(
                self.model,
                str(self.urdf_path),
                pin.GeometryType.COLLISION,
                None,  # geometry_model=None
                [str(self.package_dir)]  # package_dirs as list
            )
            self.geom_data = self.geom_model.createData()
            logger.info(f"✓ Successfully loaded collision geometry")
        except Exception as e:
            # Fallback: try without package_dirs
            logger.warning(f"⚠ Loading with package_dirs failed, trying without...")
            try:
                self.geom_model = pin.buildGeomFromUrdf(
                    self.model,
                    str(self.urdf_path),
                    pin.GeometryType.COLLISION
                )
                self.geom_data = self.geom_model.createData()
                logger.info(f"✓ Successfully loaded collision geometry (without package_dirs)")
            except Exception as e2:
                logger.error(f"\n❌ Failed to load collision geometry")
                logger.error(f"   package_dirs tried: [{self.package_dir}]")
                logger.error(f"   Errors: {e}, {e2}")
                raise RuntimeError(
                    f"Failed to load collision geometry. "
                    f"package_dirs: [{self.package_dir}]. "
                    f"Last error: {e2}"
                )
        
        # Initialize geometry data with neutral configuration
        try:
            q_neutral = pin.neutral(self.model)
            pin.forwardKinematics(self.model, self.data, q_neutral)
            pin.updateGeometryPlacements(
                self.model, self.data, self.geom_model, self.geom_data, q_neutral
            )
            logger.info("✓ Geometry data initialized successfully")
        except Exception as e:
            logger.warning(f"⚠ Warning: Could not initialize geometry data: {e}")
    
    def update_kinematics(self, q: np.ndarray):
        """
        Update forward kinematics for the given configuration.
        
        Args:
            q: Joint configuration vector (nq x 1)
        """
        if q.ndim > 1:
            q = q.flatten()
        q = np.asarray(q, dtype=np.float64)
        
        if len(q) != self.model.nq:
            raise ValueError(
                f"Configuration size mismatch: got {len(q)}, expected {self.model.nq}"
            )
        
        pin.forwardKinematics(self.model, self.data, q)
    
    def update_geometry(self, q: np.ndarray):
        """
        Update geometry placements based on joint configuration.
        
        Args:
            q: Joint configuration vector (nq x 1)
        """
        if self.geom_model is None:
            raise RuntimeError("Collision geometry not loaded. Set load_collision=True in __init__")
        
        self.update_kinematics(q)
        pin.updateGeometryPlacements(
            self.model, self.data, self.geom_model, self.geom_data, q
        )
    
    def get_link_names(self) -> List[str]:
        """Get list of all link names in the model."""
        n_frames = getattr(self.model, 'nframes', len(self.model.names))
        return [self.model.names[i] for i in range(n_frames)]
    
    def get_geometry_names(self) -> List[str]:
        """Get list of all collision geometry names."""
        if self.geom_model is None:
            return []
        return [geom.name for geom in self.geom_model.geometryObjects]


def load_pinocchio_model_for_nov11(
    base_path: Optional[str] = None,
    urdf_filename: str = "Nov11_convex.urdf"
) -> PinocchioModel:
    """
    Convenience function to load PinocchioModel for the Nov11 robot.
    
    Args:
        base_path: Base path to featheros directory. If None, tries to infer.
        urdf_filename: Name of URDF file (default: "Nov11_convex.urdf")
    
    Returns:
        PinocchioModel instance
    """
    if base_path is None:
        # Try to find featheros directory
        current = Path.cwd()
        if 'featheros' in str(current):
            base_path = str(current)[:str(current).find('featheros') + len('featheros')]
        else:
            base_path = str(current)
    
    urdf_path = Path(base_path) / "assets" / "feather_one" / "2025_11_11" / \
                "Nov11_description" / "urdf" / urdf_filename
    
    if not urdf_path.exists():
        raise FileNotFoundError(f"URDF not found at: {urdf_path}")
    
    # Package directory for meshes
    package_dir = urdf_path.parent.parent.parent  # Points to 2025_11_11/
    
    return PinocchioModel(str(urdf_path), package_dir=str(package_dir), load_collision=True)

