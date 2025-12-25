#!/usr/bin/env python3
"""
URDF Convex Hull Generator

This script processes a URDF file and generates convex hull meshes for all collision
geometries that use mesh files. This is useful for preprocessing URDFs from design tools
so they can be efficiently used with Pinocchio for self-collision checks.

The script:
1. Parses the input URDF file
2. Finds all collision links that use mesh geometry
3. Loads the mesh files (STL, OBJ, etc.)
4. Generates convex hulls from the meshes
5. Saves the convex hull meshes to a specified output directory
6. Generates a new URDF file with updated mesh paths pointing to the convex hulls

Usage:
    python urdf_convex_hull.py input.urdf --output-dir output/ --output-urdf output.urdf
"""

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Tuple
import os
import sys

try:
    import trimesh
except ImportError:
    print("Error: trimesh is required. Install it with: pip install trimesh")
    sys.exit(1)

from .constants import PRINT_LINE_WIDTH


def resolve_mesh_path(mesh_filename: str, urdf_path: Path, package_dir: Optional[Path] = None) -> Path:
    """
    Resolve a mesh file path from URDF.
    
    Handles:
    - Absolute paths
    - Relative paths (relative to URDF directory)
    - package:// paths (e.g., package://robot_description/meshes/file.stl)
    
    Args:
        mesh_filename: The filename attribute from the URDF mesh element
        urdf_path: Path to the URDF file
        package_dir: Base directory for package:// paths (defaults to URDF parent)
    
    Returns:
        Resolved absolute path to the mesh file
    """
    mesh_filename = mesh_filename.strip()
    
    # Handle package:// paths
    if mesh_filename.startswith("package://"):
        # Extract package://package_name/path/to/file
        package_path = mesh_filename[10:]  # Remove "package://"
        parts = package_path.split("/", 1)
        if len(parts) == 2:
            package_name, rel_path = parts
        else:
            # Just package name, no path
            package_name = parts[0]
            rel_path = ""
        
        if package_dir is None:
            # Try to auto-detect: look for package.xml or assume parent of URDF
            current = urdf_path.parent
            while current != current.parent:
                if (current / "package.xml").exists() or (current.parent / package_name / "package.xml").exists():
                    if (current.parent / package_name).exists():
                        package_dir = current.parent
                    else:
                        package_dir = current
                    break
                current = current.parent
            else:
                # Fallback: assume package is in parent directory
                package_dir = urdf_path.parent.parent
        
        # Construct path: package_dir/package_name/rel_path
        if rel_path:
            mesh_path = Path(package_dir) / package_name / rel_path
        else:
            mesh_path = Path(package_dir) / package_name
    elif os.path.isabs(mesh_filename):
        # Absolute path
        mesh_path = Path(mesh_filename)
    else:
        # Relative path - relative to URDF directory
        mesh_path = urdf_path.parent / mesh_filename
    
    return mesh_path.resolve()


def generate_convex_hull(mesh_path: Path, output_path: Path, scale: Optional[Tuple[float, float, float]] = None) -> bool:
    """
    Generate a convex hull from a mesh file and save it.
    
    Args:
        mesh_path: Path to input mesh file
        output_path: Path where convex hull should be saved
        scale: Optional scale factor (x, y, z) to apply to mesh before generating convex hull
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load the mesh
        if not mesh_path.exists():
            print(f"  ⚠ Warning: Mesh file not found: {mesh_path}")
            return False
        
        mesh = trimesh.load(str(mesh_path))
        
        # Handle scene objects (multiple meshes)
        if isinstance(mesh, trimesh.Scene):
            # Combine all meshes in the scene
            mesh = trimesh.util.concatenate([m for m in mesh.geometry.values() if isinstance(m, trimesh.Trimesh)])
        
        # Ensure we have a Trimesh object
        if not isinstance(mesh, trimesh.Trimesh):
            print(f"  ⚠ Warning: Could not convert to Trimesh: {mesh_path}")
            return False
        
        # Apply scale if provided
        if scale is not None:
            import numpy as np
            scale_matrix = np.diag([scale[0], scale[1], scale[2], 1.0])
            mesh.apply_transform(scale_matrix)
        
        # Generate convex hull
        convex_hull = mesh.convex_hull
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the convex hull
        # Try to preserve the original file format, default to STL
        ext = output_path.suffix.lower()
        if ext in ['.stl', '.STL']:
            convex_hull.export(str(output_path))
        elif ext in ['.obj', '.OBJ']:
            convex_hull.export(str(output_path))
        else:
            # Default to STL
            output_path = output_path.with_suffix('.stl')
            convex_hull.export(str(output_path))
        
        # Print statistics
        print(f"  ✓ Generated convex hull: {len(convex_hull.vertices)} vertices, "
              f"{len(convex_hull.faces)} faces (original: {len(mesh.vertices)} vertices, "
              f"{len(mesh.faces)} faces)")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error generating convex hull: {e}")
        import traceback
        traceback.print_exc()
        return False


def process_urdf(
    input_urdf: Path,
    output_urdf: Path,
    output_mesh_dir: Path,
    package_dir: Optional[Path] = None,
    mesh_path_prefix: str = ""
) -> int:
    """
    Process URDF file to replace collision meshes with convex hulls.
    
    Args:
        input_urdf: Path to input URDF file
        output_urdf: Path to output URDF file
        output_mesh_dir: Directory to save convex hull meshes
        package_dir: Base directory for package:// paths
        mesh_path_prefix: Prefix to add to mesh paths in output URDF (e.g., "package://robot/meshes/")
    
    Returns:
        Number of meshes processed
    """
    print(f"Processing URDF: {input_urdf}")
    print(f"Output URDF: {output_urdf}")
    print(f"Output mesh directory: {output_mesh_dir}")
    
    # Parse URDF
    tree = ET.parse(input_urdf)
    root = tree.getroot()
    
    # Create output mesh directory
    output_mesh_dir.mkdir(parents=True, exist_ok=True)
    
    processed_count = 0
    skipped_count = 0
    
    # Find all links
    for link in root.findall('link'):
        link_name = link.get('name', 'unknown')
        
        # Find collision elements
        for collision in link.findall('collision'):
            geometry = collision.find('geometry')
            if geometry is None:
                continue
            
            # Check if it's a mesh
            mesh_elem = geometry.find('mesh')
            if mesh_elem is None:
                continue
            
            mesh_filename = mesh_elem.get('filename')
            if not mesh_filename:
                continue
            
            print(f"\nProcessing collision mesh for link '{link_name}':")
            print(f"  Original mesh: {mesh_filename}")
            
            # Resolve mesh path
            try:
                original_mesh_path = resolve_mesh_path(mesh_filename, input_urdf, package_dir)
                print(f"  Resolved path: {original_mesh_path}")
            except Exception as e:
                print(f"  ✗ Error resolving mesh path: {e}")
                skipped_count += 1
                continue
            
            # Parse scale from URDF
            scale_str = mesh_elem.get('scale', '1.0 1.0 1.0')
            try:
                scale_values = [float(s) for s in scale_str.split()]
                if len(scale_values) == 3:
                    scale_tuple = tuple(scale_values)
                else:
                    scale_tuple = (1.0, 1.0, 1.0)
            except (ValueError, AttributeError):
                scale_tuple = (1.0, 1.0, 1.0)
            
            # Generate output mesh path
            # Use link name + original filename for uniqueness
            original_name = original_mesh_path.stem
            original_ext = original_mesh_path.suffix or '.stl'
            output_mesh_name = f"{link_name}_{original_name}_convex_hull{original_ext}"
            output_mesh_path = output_mesh_dir / output_mesh_name
            
            # Generate convex hull (scale is applied to mesh before generating hull)
            if generate_convex_hull(original_mesh_path, output_mesh_path, scale=scale_tuple):
                # Update URDF to point to new mesh
                # Determine the path to use in URDF
                if mesh_path_prefix:
                    # Use provided prefix
                    new_mesh_filename = f"{mesh_path_prefix}{output_mesh_name}"
                else:
                    # Use relative path from output URDF to output mesh
                    try:
                        rel_path = os.path.relpath(output_mesh_path, output_urdf.parent)
                        new_mesh_filename = rel_path
                    except ValueError:
                        # If relative path fails (different drives on Windows), use absolute
                        new_mesh_filename = str(output_mesh_path)
                
                # Update mesh filename
                mesh_elem.set('filename', new_mesh_filename)
                
                # Remove scale from URDF since it's now baked into the convex hull mesh
                # (or set to 1.0 1.0 1.0 if we want to keep the attribute)
                mesh_elem.set('scale', '1.0 1.0 1.0')
                
                print(f"  Updated URDF mesh path: {new_mesh_filename}")
                processed_count += 1
            else:
                skipped_count += 1
    
    # Save modified URDF
    print(f"\nSaving modified URDF to: {output_urdf}")
    output_urdf.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_urdf, encoding='utf-8', xml_declaration=True)
    
    print(f"\n✓ Processing complete!")
    print(f"  Processed: {processed_count} meshes")
    print(f"  Skipped: {skipped_count} meshes")
    
    return processed_count


def visualize_convex_hulls(
    output_mesh_dir: Path,
    original_mesh_dir: Optional[Path] = None,
    input_urdf: Optional[Path] = None,
    package_dir: Optional[Path] = None
):
    """
    Visualize generated convex hulls, optionally comparing with originals.
    
    Args:
        output_mesh_dir: Directory containing convex hull meshes
        original_mesh_dir: Optional directory with original meshes for comparison
        input_urdf: Optional URDF file to extract original mesh paths from
        package_dir: Base directory for resolving package:// paths from URDF
    """
    print("\n" + "="*PRINT_LINE_WIDTH)
    print("Visualizing convex hulls...")
    print("="*PRINT_LINE_WIDTH)
    
    try:
        # Try to use trimesh viewer
        try:
            from trimesh.viewer import SceneViewer
            viewer_available = True
        except ImportError:
            viewer_available = False
            print("⚠ trimesh.viewer not available, using scene.show() instead")
    except Exception:
        viewer_available = False
    
    convex_hulls = []
    originals = []
    
    # Load all convex hull meshes
    convex_files = sorted(output_mesh_dir.glob("*_convex_hull.*"))
    if not convex_files:
        print("⚠ No convex hull meshes found in output directory")
        return
    
    print(f"Found {len(convex_files)} convex hull mesh(es)")
    
    for convex_file in convex_files:
        try:
            hull = trimesh.load(str(convex_file))
            if isinstance(hull, trimesh.Trimesh):
                convex_hulls.append(hull)
                print(f"  ✓ Loaded: {convex_file.name}")
        except Exception as e:
            print(f"  ✗ Failed to load {convex_file.name}: {e}")
    
    # Optionally load original meshes for comparison
    if original_mesh_dir and original_mesh_dir.exists():
        print(f"\nLoading original meshes from: {original_mesh_dir}")
        # Try to match convex hulls with originals by extracting base name
        for convex_file in convex_files:
            # Extract base name: "link_name_originalname_convex_hull.stl" -> "originalname"
            base_name = convex_file.stem.replace('_convex_hull', '')
            # Try to find original by removing link name prefix
            parts = base_name.split('_', 1)
            if len(parts) > 1:
                original_name = parts[1]  # Get part after link name
            else:
                original_name = base_name
            
            # Try different extensions
            for ext in ['.stl', '.STL', '.obj', '.OBJ', '.ply', '.PLY']:
                original_file = original_mesh_dir / f"{original_name}{ext}"
                if original_file.exists():
                    try:
                        orig = trimesh.load(str(original_file))
                        if isinstance(orig, trimesh.Trimesh):
                            originals.append(orig)
                            print(f"  ✓ Loaded original: {original_file.name}")
                            break
                    except Exception as e:
                        print(f"  ✗ Failed to load {original_file.name}: {e}")
    
    # Also try to load originals from URDF if provided
    if input_urdf and input_urdf.exists() and not original_mesh_dir:
        print(f"\nExtracting original mesh paths from URDF: {input_urdf}")
        try:
            tree = ET.parse(input_urdf)
            root = tree.getroot()
            
            for link in root.findall('link'):
                for collision in link.findall('collision'):
                    geometry = collision.find('geometry')
                    if geometry is None:
                        continue
                    
                    mesh_elem = geometry.find('mesh')
                    if mesh_elem is None:
                        continue
                    
                    mesh_filename = mesh_elem.get('filename')
                    if not mesh_filename:
                        continue
                    
                    try:
                        original_mesh_path = resolve_mesh_path(mesh_filename, input_urdf, package_dir)
                        if original_mesh_path.exists():
                            orig = trimesh.load(str(original_mesh_path))
                            if isinstance(orig, trimesh.Trimesh):
                                originals.append(orig)
                                print(f"  ✓ Loaded original from URDF: {original_mesh_path.name}")
                    except Exception as e:
                        pass  # Skip if can't resolve
        except Exception as e:
            print(f"  ⚠ Could not extract meshes from URDF: {e}")
    
    if not convex_hulls:
        print("⚠ No convex hulls loaded for visualization")
        return
    
    # Create scene with all meshes
    import numpy as np
    import trimesh.transformations as tf
    
    # Ensure all meshes have proper visual materials and colors
    all_meshes = []
    for mesh in convex_hulls + originals:
        # Make a copy to avoid modifying originals
        mesh_copy = mesh.copy()
        
        # Ensure visual is properly initialized
        if not hasattr(mesh_copy, 'visual') or mesh_copy.visual is None:
            mesh_copy.visual = trimesh.visual.ColorVisuals()
        elif not isinstance(mesh_copy.visual, trimesh.visual.ColorVisuals):
            # Convert to ColorVisuals if it's a different type
            mesh_copy.visual = trimesh.visual.ColorVisuals(mesh=mesh_copy)
        
        # Set colors - use face colors for solid rendering
        # Colors must be set per-face, so create array matching number of faces
        if mesh in convex_hulls:
            # Red for convex hulls (semi-transparent)
            color = np.array([255, 0, 0, 200], dtype=np.uint8)
        else:
            # Gray for originals (more transparent)
            color = np.array([200, 200, 200, 100], dtype=np.uint8)
        
        # Set face colors - need array of shape (n_faces, 4) for RGBA
        n_faces = len(mesh_copy.faces)
        mesh_copy.visual.face_colors = np.tile(color, (n_faces, 1))
        
        # Rotate mesh to show front view instead of top view
        # Rotate -90 degrees around X axis to go from top view (Z up) to front view (Y up)
        rotation_matrix = tf.rotation_matrix(-np.pi / 2, [1, 0, 0])
        mesh_copy.apply_transform(rotation_matrix)
        
        all_meshes.append(mesh_copy)
    
    scene = trimesh.Scene(all_meshes)
    
    print(f"\n✓ Scene created with {len(convex_hulls)} convex hull(s) and {len(originals)} original(s)")
    print("  - Red meshes: Convex hulls")
    print("  - Gray meshes: Original meshes (if available)")
    print("\nOpening viewer...")
    print("  (Close the viewer window when done)")
    print("  (Use mouse to rotate: left-click drag, scroll to zoom)")
    
    # Show the scene
    try:
        if viewer_available:
            SceneViewer(scene=scene, caption="Convex Hulls (Red) vs Originals (Gray)")
        else:
            # For scene.show(), we can't directly set camera, but user can rotate
            scene.show()
    except Exception as e:
        print(f"⚠ Error opening viewer: {e}")
        print("  You can manually view the meshes using:")
        print(f"  import trimesh")
        print(f"  scene = trimesh.load('{output_mesh_dir}')")
        print(f"  scene.show()")


def main():
    parser = argparse.ArgumentParser(
        description="Generate convex hull meshes for URDF collision geometries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python urdf_convex_hull.py robot.urdf -o output/ -u robot_convex.urdf
  
  # With package:// path resolution
  python urdf_convex_hull.py robot.urdf -o output/ -u robot_convex.urdf --package-dir /path/to/packages
  
  # With custom mesh path prefix for output URDF
  python urdf_convex_hull.py robot.urdf -o output/ -u robot_convex.urdf --mesh-path-prefix "package://robot/meshes/"
  
  # With visualization
  python urdf_convex_hull.py robot.urdf -o output/ -u robot_convex.urdf --visualize
  
  # With visualization and original meshes for comparison
  python urdf_convex_hull.py robot.urdf -o output/ -u robot_convex.urdf --visualize --original-mesh-dir meshes/
  
  # Auto-detects existing outputs and skips reprocessing, then visualizes
  python urdf_convex_hull.py robot.urdf -o output/ -u robot_convex.urdf --visualize
  
  # Force reprocessing even if outputs exist
  python urdf_convex_hull.py robot.urdf -o output/ -u robot_convex.urdf --force-reprocess
        """
    )
    
    parser.add_argument(
        'input_urdf',
        type=Path,
        nargs='?',
        default=None,
        help='Path to input URDF file (required for processing, optional for visualization-only)'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        type=Path,
        required=True,
        help='Directory containing convex hull mesh files (or where to save them)'
    )
    
    parser.add_argument(
        '-u', '--output-urdf',
        type=Path,
        required=True,
        help='Path to output URDF file with updated mesh references'
    )
    
    parser.add_argument(
        '--package-dir',
        type=Path,
        default=None,
        help='Base directory for resolving package:// paths (auto-detected if not specified)'
    )
    
    parser.add_argument(
        '--mesh-path-prefix',
        type=str,
        default='',
        help='Prefix to add to mesh paths in output URDF (e.g., "package://robot/meshes/")'
    )
    
    parser.add_argument(
        '--visualize',
        action='store_true',
        help='Open interactive 3D viewer to visualize convex hulls after processing'
    )
    
    parser.add_argument(
        '--original-mesh-dir',
        type=Path,
        default=None,
        help='Directory containing original meshes for comparison visualization (optional)'
    )
    
    parser.add_argument(
        '--force-reprocess',
        action='store_true',
        help='Force reprocessing even if output files already exist'
    )
    
    args = parser.parse_args()
    
    # Validate output paths (always required to know where to check/save)
    if not args.output_dir:
        print("Error: --output-dir is required")
        sys.exit(1)
    
    if not args.output_urdf:
        print("Error: --output-urdf is required")
        sys.exit(1)
    
    # Check if outputs already exist
    output_exists = args.output_urdf.exists()
    mesh_dir_exists = args.output_dir.exists()
    convex_hulls_exist = False
    
    if mesh_dir_exists:
        convex_hull_files = list(args.output_dir.glob("*_convex_hull.*"))
        convex_hulls_exist = len(convex_hull_files) > 0
    
    # Auto-detect and skip reprocessing if outputs exist
    if output_exists and convex_hulls_exist and not args.force_reprocess:
        print("="*PRINT_LINE_WIDTH)
        print("Existing outputs detected - skipping reprocessing")
        print("="*PRINT_LINE_WIDTH)
        print(f"✓ Found output URDF: {args.output_urdf}")
        print(f"✓ Found {len(list(args.output_dir.glob('*_convex_hull.*')))} convex hull mesh(es) in: {args.output_dir}")
        print("\nTo force reprocessing, use --force-reprocess flag")
        
        # Go straight to visualization if requested
        if args.visualize:
            print("\n" + "="*PRINT_LINE_WIDTH)
            print("Opening visualization...")
            print("="*PRINT_LINE_WIDTH)
            try:
                visualize_convex_hulls(
                    args.output_dir,
                    args.original_mesh_dir,
                    args.input_urdf,  # Optional - only used to extract original mesh paths
                    args.package_dir
                )
            except Exception as e:
                print(f"\n✗ Error during visualization: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
        else:
            print("\n💡 Tip: Use --visualize flag to view the convex hulls")
        
        return
    
    # Process URDF (either first time or forced reprocessing)
    # For processing, input_urdf is required
    if not args.input_urdf:
        print("Error: input_urdf is required for processing")
        print("  (If outputs already exist, they will be auto-detected and processing skipped)")
        sys.exit(1)
    
    # Validate input URDF exists
    if not args.input_urdf.exists():
        print(f"Error: Input URDF file not found: {args.input_urdf}")
        sys.exit(1)
    
    if args.force_reprocess and (output_exists or convex_hulls_exist):
        print("="*PRINT_LINE_WIDTH)
        print("Force reprocessing requested - regenerating outputs")
        print("="*PRINT_LINE_WIDTH)
    
    try:
        processed = process_urdf(
            args.input_urdf,
            args.output_urdf,
            args.output_dir,
            args.package_dir,
            args.mesh_path_prefix
        )
        
        if processed == 0:
            print("\n⚠ Warning: No meshes were processed. Check that:")
            print("  1. The URDF contains collision elements with mesh geometry")
            print("  2. Mesh file paths are correct")
            print("  3. Mesh files exist and are readable")
            sys.exit(1)
        
        # Visualize if requested
        if args.visualize:
            visualize_convex_hulls(
                args.output_dir,
                args.original_mesh_dir,
                args.input_urdf,
                args.package_dir
            )
        
    except Exception as e:
        print(f"\n✗ Error processing URDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

