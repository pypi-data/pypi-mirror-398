"""
Self-collision detection for robots using Pinocchio.

This module provides SelfCollisionChecker: A lightweight API for self-collision
checking in control loops. It requires a PinocchioModel instance (from pinocchio_model.py).
"""

import logging
import pinocchio as pin
import numpy as np
from typing import List, Tuple, Dict, Optional

from .pinocchio_model import PinocchioModel, load_pinocchio_model_for_nov11
from ..utils.constants import PRINT_LINE_WIDTH

logger = logging.getLogger(__name__)

class SelfCollisionChecker:
    """
    Lightweight self-collision checker for use in control loops.
    
    This class provides collision checking APIs that can be called repeatedly
    with different configurations. It requires a pre-loaded PinocchioModel.
    """
    
    def __init__(
        self, 
        pinocchio_model: PinocchioModel,
        excluded_pairs: Optional[List[Tuple[str, str]]] = None
    ):
        """
        Initialize self-collision checker.
        
        Args:
            pinocchio_model: Pre-loaded PinocchioModel instance
            excluded_pairs: List of (geom1_name, geom2_name) pairs to exclude from checking
        """
        if pinocchio_model.geom_model is None:
            raise ValueError("PinocchioModel must have collision geometry loaded")
        
        self.pinocchio_model = pinocchio_model
        self.model = pinocchio_model.model
        self.data = pinocchio_model.data
        self.geom_model = pinocchio_model.geom_model
        
        # Note: We don't store geom_data here - it gets recreated before each
        # collision check to prevent segfaults (this was critical in the original code)
        
        # Cache last configuration to avoid redundant geometry updates
        self._last_q = None
        
        # Add all collision pairs (automatically excludes adjacent links)
        self.geom_model.addAllCollisionPairs()
        
        # Store excluded pairs for reference
        self.excluded_pairs = []
        
        # Exclude specified pairs
        if excluded_pairs:
            self.exclude_collision_pairs(excluded_pairs)
        
        logger.info(f"✓ Self-collision checker initialized")
        logger.info(f"✓ Number of collision pairs: {len(self.geom_model.collisionPairs)}")
        if self.excluded_pairs:
            logger.info(f"✓ Excluded {len(self.excluded_pairs)} collision pair(s)")
    
    def reset_cache(self):
        """Reset the configuration cache to force update on next call."""
        self._last_q = None
    
    def exclude_collision_pair(self, geom1_name: str, geom2_name: str):
        """
        Exclude a collision pair from checking.
        
        Args:
            geom1_name: Name of first geometry (must include _0 suffix, e.g., "base_link_0")
            geom2_name: Name of second geometry (must include _0 suffix, e.g., "Drive_Bracket_1_0")
        """
        self.exclude_collision_pairs([(geom1_name, geom2_name)])
    
    def exclude_collision_pairs(self, pairs: List[Tuple[str, str]]):
        """
        Exclude multiple collision pairs efficiently (O(E + P) complexity).
        
        Args:
            pairs: List of tuples (geom1_name, geom2_name) to exclude
        """
        if not pairs:
            return
        
        # Build lookup dictionary: (geom_id1, geom_id2) -> CollisionPair
        # O(P) where P is number of collision pairs
        pair_lookup = {}
        for cp in self.geom_model.collisionPairs:
            # Store both orderings since pairs can be in either direction
            key1 = (cp.first, cp.second)
            key2 = (cp.second, cp.first)
            pair_lookup[key1] = cp
            pair_lookup[key2] = cp
        
        # Process each excluded pair: O(E) where E is number of excluded pairs
        excluded_count = 0
        for geom1_name, geom2_name in pairs:
            try:
                geom1_id = self.geom_model.getGeometryId(geom1_name)
                geom2_id = self.geom_model.getGeometryId(geom2_name)
                
                # O(1) lookup
                lookup_key = (geom1_id, geom2_id)
                found_pair = pair_lookup.get(lookup_key)
                
                if found_pair is not None:
                    # Check if pair still exists (may have been removed already)
                    if found_pair in self.geom_model.collisionPairs:
                        self.geom_model.removeCollisionPair(found_pair)
                        self.excluded_pairs.append((geom1_name, geom2_name))
                        excluded_count += 1
                        logger.info(f"✓ Excluded collision pair: {geom1_name} <-> {geom2_name}")
                    else:
                        logger.warning(f"Warning: Pair {geom1_name} <-> {geom2_name} already removed")
                else:
                    logger.warning(f"Warning: Pair {geom1_name} <-> {geom2_name} not found in collision pairs")
            except Exception as e:
                logger.warning(f"Warning: Could not exclude pair {geom1_name} <-> {geom2_name}: {e}")
        
        if excluded_count > 0:
            logger.info(f"✓ Excluded {excluded_count} collision pair(s)")
    
    def _update_geometry_if_needed(self, q: np.ndarray, geom_data):
        """
        Update geometry placements if configuration has changed.
        This avoids redundant forward kinematics updates when checking the same configuration.
        
        Args:
            q: Joint configuration vector
            geom_data: Geometry data to update (will be created fresh for collision checks)
        """
        # Normalize q for comparison
        if q.ndim > 1:
            q = q.flatten()
        q = np.asarray(q, dtype=np.float64)
        
        # Check if we need to update forward kinematics (shared data)
        # Geometry update always happens on fresh geom_data, so we can't skip that
        needs_fk_update = True
        if self._last_q is not None:
            # Quick shape check first
            if q.shape == self._last_q.shape:
                # Use allclose with very small tolerance for floating point comparison
                if np.allclose(q, self._last_q, rtol=0, atol=1e-15):
                    needs_fk_update = False  # Skip FK update, but still update geometry
        
        # Update forward kinematics only if needed (shared data)
        if needs_fk_update:
            pin.forwardKinematics(self.model, self.data, q)
            self._last_q = q.copy()
        
        # Always update geometry placements (using the fresh geom_data)
        # This is necessary even if FK didn't change, because geom_data is fresh
        pin.updateGeometryPlacements(
            self.model, self.data, self.geom_model, geom_data, q
        )
    
    def check_collision(
        self, 
        q: np.ndarray, 
        stop_at_first: bool = True
    ) -> bool:
        """
        Check for self-collisions.
        
        Args:
            q: Joint configuration vector
            stop_at_first: If True, stop checking after first collision found
        
        Returns:
            True if collision detected, False otherwise
        """
        # Recreate geometry data for clean state (prevents segfaults)
        # This pattern was critical in the original working code
        geom_data = self.geom_model.createData()
        self._update_geometry_if_needed(q, geom_data)
        
        if len(self.geom_model.collisionPairs) == 0:
            return False
        
        try:
            result = pin.computeCollisions(
                self.geom_model, 
                geom_data, 
                stop_at_first_collision=stop_at_first
            )
            return result
        except Exception as e:
            raise RuntimeError(f"Collision checking failed: {e}")
    
    def _get_pair_names(self, pair_index: int) -> Tuple[str, str]:
        """Helper to get geometry names for a collision pair."""
        cp = self.geom_model.collisionPairs[pair_index]
        geom1_name = self.geom_model.geometryObjects[cp.first].name
        geom2_name = self.geom_model.geometryObjects[cp.second].name
        return geom1_name, geom2_name
    
    def get_colliding_pairs(self, q: np.ndarray) -> List[Tuple[str, str]]:
        """
        Get list of colliding link pairs.
        
        Args:
            q: Joint configuration vector
        
        Returns:
            List of tuples (link1_name, link2_name) that are colliding
        """
        # Recreate geometry data for clean state (prevents segfaults)
        geom_data = self.geom_model.createData()
        self._update_geometry_if_needed(q, geom_data)
        
        pin.computeCollisions(self.geom_model, geom_data, False)
        
        colliding = []
        for k in range(len(self.geom_model.collisionPairs)):
            if geom_data.collisionResults[k].isCollision():
                colliding.append(self._get_pair_names(k))
        
        return colliding
    
    def compute_distances(self, q: np.ndarray) -> Dict[Tuple[str, str], float]:
        """
        Compute minimum distances between all collision pairs.
        
        Args:
            q: Joint configuration vector
        
        Returns:
            Dictionary mapping (link1_name, link2_name) -> minimum_distance
            Negative distances indicate collision.
        """
        # Recreate geometry data for clean state (prevents segfaults)
        # This pattern was critical in the original working code
        geom_data = self.geom_model.createData()
        self._update_geometry_if_needed(q, geom_data)
        
        pin.computeDistances(self.geom_model, geom_data)
        
        distances = {}
        for k in range(len(self.geom_model.collisionPairs)):
            min_dist = geom_data.distanceResults[k].min_distance
            distances[self._get_pair_names(k)] = min_dist
        
        return distances
    
    def get_closest_pairs(
        self, 
        q: np.ndarray, 
        n: int = 10
    ) -> List[Tuple[Tuple[str, str], float]]:
        """
        Get the n closest collision pairs (sorted by distance).
        
        Args:
            q: Joint configuration vector
            n: Number of pairs to return
        
        Returns:
            List of tuples ((link1_name, link2_name), distance) sorted by distance
        """
        distances = self.compute_distances(q)
        sorted_pairs = sorted(distances.items(), key=lambda x: x[1])
        return sorted_pairs[:n]
    
    def check_collision_safe(
        self, 
        q: np.ndarray, 
        safety_margin: float = 0.0
    ) -> Tuple[bool, List[Tuple[str, str]]]:
        """
        Safer collision check using only distance computation (no computeCollisions).
        This avoids potential segfaults from hpp-fcl.
        
        Args:
            q: Joint configuration vector
            safety_margin: Safety margin in meters (default 0.0, negative = collision)
        
        Returns:
            Tuple of (is_colliding, list of colliding pairs)
        """
        if len(self.geom_model.collisionPairs) == 0:
            return False, []
        
        distances = self.compute_distances(q)
        
        colliding_pairs = [
            pair for pair, dist in distances.items() 
            if dist < safety_margin
        ]
        
        return len(colliding_pairs) > 0, colliding_pairs
    
    def check_collision_with_margin(
        self, 
        q: np.ndarray, 
        safety_margin: float = 0.01,
        stop_at_first: bool = True
    ) -> Tuple[bool, List[Tuple[str, str]]]:
        """
        Check for collisions with a safety margin.
        
        Args:
            q: Joint configuration vector
            safety_margin: Safety margin in meters (default 1cm)
            stop_at_first: If True, stop after first collision
        
        Returns:
            Tuple of (is_colliding, list of colliding pairs within margin)
        """
        distances = self.compute_distances(q)
        
        colliding_pairs = [
            pair for pair, dist in distances.items() 
            if dist < safety_margin
        ]
        
        is_colliding = len(colliding_pairs) > 0
        
        if stop_at_first and is_colliding:
            return True, [colliding_pairs[0]]
        
        return is_colliding, colliding_pairs


def create_checker_for_nov11(
    base_path: Optional[str] = None,
    urdf_filename: str = "Nov11_convex.urdf"
) -> SelfCollisionChecker:
    """
    Convenience function to create a SelfCollisionChecker for the Nov11 robot.
    
    This function maintains backward compatibility with the old API.
    For better performance in control loops, consider:
    1. Load PinocchioModel once: model = load_pinocchio_model_for_nov11()
    2. Create checker: checker = SelfCollisionChecker(model, excluded_pairs)
    3. Reuse both in your control loop
    
    Args:
        base_path: Base path to featheros directory. If None, tries to infer.
        urdf_filename: Name of URDF file (default: "Nov11_convex.urdf")
    
    Returns:
        Configured SelfCollisionChecker instance
    """
    # Define collision pairs to exclude (links that are always in contact)
    EXCLUDED_COLLISION_PAIRS = [
        # ("base_link_0", "Drive_Bracket_1_0"),
        # ("base_link_0", "Drive_Bracket_2_0"),
        # ("base_link_0", "Drive_Bracket_3_0"),
        # ("base_link_0", "Drive_Wheel_1_0"),
        # ("base_link_0", "Drive_Wheel_2_0"),
        # ("base_link_0", "Drive_Wheel_3_0"),
        # ("base_link_0", "Torso_1_0"),
        # ("Drive_Bracket_1_0", "Drive_Wheel_1_0"),
        # ("Drive_Bracket_2_0", "Drive_Wheel_2_0"),
        # ("Drive_Bracket_3_0", "Drive_Wheel_3_0"),
        # ("Torso_1_0", "link_SpL_SrL_1_0"),
        # ("Torso_1_0", "link_SpR_SrR_1_0"),
        # ("Torso_1_0", "Neck_rotation_1_0"),
        # ("Neck_rotation_1_0", "Camera_1_0"),
        # ("link_SpL_SrL_1_0", "link_SrL_SwL_1_0"),
        # ("link_SrL_SwL_1_0", "link_SwL_EpL_1_0"),
        # ("link_SwL_EpL_1_0", "link_EpL_WwL_1_0"),
        # ("link_EpL_WwL_1_0", "link_WwL_WpL_1_0"),
        # ("link_WwL_WpL_1_0", "link_WpL_WrL_1_0"),
        # ("link_WpL_WrL_1_0", "end_effectorL_1_0"),
        # ("link_SpR_SrR_1_0", "link_SrR_SwR_1_0"),
        # ("link_SrR_SwR_1_0", "link_SwR_EpR_1_0"),
        # ("link_SwR_EpR_1_0", "link_EpR_WwR_1_0"),
        # ("link_EpR_WwR_1_0", "link_WwR_WpR_1_0"),
        # ("link_WwR_WpR_1_0", "link_WpR_WrR_1_0"),
        # ("link_WpR_WrR_1_0", "end_effectorR_1_0"),
    ]
    
    # Load model
    model = load_pinocchio_model_for_nov11(base_path=base_path, urdf_filename=urdf_filename)
    
    # Create checker with excluded pairs
    checker = SelfCollisionChecker(model, excluded_pairs=EXCLUDED_COLLISION_PAIRS)
    
    return checker


if __name__ == "__main__":
    # Example usage
    import sys

    # Configure root logger to show INFO and above
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        print("=" * PRINT_LINE_WIDTH)
        print("Option 1: Using convenience function")
        print("=" * PRINT_LINE_WIDTH)
        checker = create_checker_for_nov11()
        
        # Get neutral configuration
        q = pin.neutral(checker.model)
        logger.info(f"\n✓ Neutral configuration: {q.flatten()}")
        
        # Check for collisions using safer distance-based method
        logger.info("\n--- Checking collisions in neutral pose (using safe distance method) ---")
        is_colliding, colliding_pairs = checker.check_collision_safe(q, safety_margin=0.0)
        logger.info(f"\n✓ Collision check completed!")
        logger.info(f"Collision detected: {is_colliding}")
        
        if is_colliding:
            logger.info(f"Colliding pairs ({len(colliding_pairs)}):")
            for pair in colliding_pairs:
                logger.info(f"  - {pair[0]} <-> {pair[1]}")
        else:
            logger.info("No collisions detected")
        
        # Compute distances
        logger.info("\n--- Computing distances ---")
        distances = checker.compute_distances(q)
        closest = checker.get_closest_pairs(q, n=max(10, 1+len(colliding_pairs)))
        logger.info("Closest pairs:")
        for (link1, link2), dist in closest:
            status = "COLLIDING" if dist < 0 else "OK"
            logger.info(f"  {link1} <-> {link2}: {dist:.4f} m [{status}]")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
