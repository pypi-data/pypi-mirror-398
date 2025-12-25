"""
Debug Network Visualization - Step by Step

This script adds network elements one by one to identify where the issue occurs.
"""

import pyvista as pv
import numpy as np
import random
from pathlib import Path

def create_debug_network(n_nodes=43):
    """Create a network step by step for debugging."""
    print(f"Creating debug network with {n_nodes} nodes...")
    
    # Generate random node positions
    np.random.seed(42)
    node_positions = np.random.uniform(-5, 5, (n_nodes, 3))
    print(f"Generated {len(node_positions)} node positions")
    
    # Create basic PolyData
    points = pv.PolyData(node_positions)
    print(f"Created PolyData with {len(points.points)} points")
    
    return points

def test_basic_points():
    """Test 1: Just points, no colors, no lines"""
    print("\n=== TEST 1: Basic Points Only ===")
    
    network = create_debug_network(n_nodes=10)  # Smaller for testing
    
    plotter = pv.Plotter(off_screen=True, window_size=[400, 300])
    print("Created plotter")
    
    try:
        plotter.add_mesh(network, color='lightblue', point_size=8)
        print("✓ Added basic points successfully")
    except Exception as e:
        print(f"✗ Error adding basic points: {e}")
        return False
    
    try:
        plotter.screenshot("test1_basic_points.png")
        print("✓ Screenshot saved successfully")
    except Exception as e:
        print(f"✗ Error taking screenshot: {e}")
        return False
    
    plotter.close()
    return True

def test_colored_points():
    """Test 2: Points with colors"""
    print("\n=== TEST 2: Colored Points ===")
    
    network = create_debug_network(n_nodes=10)
    
    # Add colors
    colors = []
    for i in range(len(network.points)):
        hue = i / len(network.points)
        r = int(255 * (0.5 + 0.5 * np.sin(hue * 2 * np.pi)))
        g = int(255 * (0.5 + 0.5 * np.sin(hue * 2 * np.pi + 2 * np.pi / 3)))
        b = int(255 * (0.5 + 0.5 * np.sin(hue * 2 * np.pi + 4 * np.pi / 3)))
        colors.append([r, g, b])
    
    network['colors'] = colors
    print(f"Added colors: {len(colors)} color values")
    
    plotter = pv.Plotter(off_screen=True, window_size=[400, 300])
    
    try:
        plotter.add_mesh(network, scalars='colors', rgb=True, point_size=8)
        print("✓ Added colored points successfully")
    except Exception as e:
        print(f"✗ Error adding colored points: {e}")
        return False
    
    try:
        plotter.screenshot("test2_colored_points.png")
        print("✓ Screenshot saved successfully")
    except Exception as e:
        print(f"✗ Error taking screenshot: {e}")
        return False
    
    plotter.close()
    return True

def test_with_lines():
    """Test 3: Points with lines"""
    print("\n=== TEST 3: Points with Lines ===")
    
    network = create_debug_network(n_nodes=10)
    
    # Add some simple lines
    edges = []
    for i in range(0, len(network.points), 2):
        if i + 1 < len(network.points):
            edges.extend([i, i + 1])
    
    if edges:
        lines = np.array(edges).reshape(-1, 2)
        network.lines = lines
        print(f"Added {len(lines)} lines")
    
    plotter = pv.Plotter(off_screen=True, window_size=[400, 300])
    
    try:
        # Add points
        plotter.add_mesh(network, color='lightblue', point_size=8)
        print("✓ Added points successfully")
        
        # Add lines separately
        if hasattr(network, 'lines') and len(network.lines) > 0:
            line_mesh = pv.PolyData()
            line_mesh.points = network.points
            line_mesh.lines = network.lines
            
            plotter.add_mesh(line_mesh, color='white', line_width=2, style='wireframe')
            print("✓ Added lines successfully")
        
    except Exception as e:
        print(f"✗ Error adding points/lines: {e}")
        return False
    
    try:
        plotter.screenshot("test3_with_lines.png")
        print("✓ Screenshot saved successfully")
    except Exception as e:
        print(f"✗ Error taking screenshot: {e}")
        return False
    
    plotter.close()
    return True

def test_full_network():
    """Test 4: Full network with colors and lines"""
    print("\n=== TEST 4: Full Network (Colors + Lines) ===")
    
    network = create_debug_network(n_nodes=10)
    
    # Add colors
    colors = []
    for i in range(len(network.points)):
        hue = i / len(network.points)
        r = int(255 * (0.5 + 0.5 * np.sin(hue * 2 * np.pi)))
        g = int(255 * (0.5 + 0.5 * np.sin(hue * 2 * np.pi + 2 * np.pi / 3)))
        b = int(255 * (0.5 + 0.5 * np.sin(hue * 2 * np.pi + 4 * np.pi / 3)))
        colors.append([r, g, b])
    
    network['colors'] = colors
    print(f"Added colors: {len(colors)} color values")
    
    # Add lines
    edges = []
    for i in range(0, len(network.points), 2):
        if i + 1 < len(network.points):
            edges.extend([i, i + 1])
    
    if edges:
        lines = np.array(edges).reshape(-1, 2)
        network.lines = lines
        print(f"Added {len(lines)} lines")
    
    plotter = pv.Plotter(off_screen=True, window_size=[400, 300])
    
    try:
        # Add colored points
        plotter.add_mesh(network, scalars='colors', rgb=True, point_size=8)
        print("✓ Added colored points successfully")
        
        # Add lines
        if hasattr(network, 'lines') and len(network.lines) > 0:
            line_mesh = pv.PolyData()
            line_mesh.points = network.points
            line_mesh.lines = network.lines
            
            plotter.add_mesh(line_mesh, color='white', line_width=2, style='wireframe')
            print("✓ Added lines successfully")
        
    except Exception as e:
        print(f"✗ Error in full network: {e}")
        return False
    
    try:
        plotter.screenshot("test4_full_network.png")
        print("✓ Screenshot saved successfully")
    except Exception as e:
        print(f"✗ Error taking screenshot: {e}")
        return False
    
    plotter.close()
    return True

if __name__ == "__main__":
    print("PyVista Network Debugging")
    print("=" * 40)
    
    # Run tests one by one
    test1_ok = test_basic_points()
    test2_ok = test_colored_points()
    test3_ok = test_with_lines()
    test4_ok = test_full_network()
    
    print("\n" + "=" * 40)
    print("DEBUG RESULTS:")
    print(f"Test 1 (Basic Points): {'✓ PASS' if test1_ok else '✗ FAIL'}")
    print(f"Test 2 (Colored Points): {'✓ PASS' if test2_ok else '✗ FAIL'}")
    print(f"Test 3 (Points + Lines): {'✓ PASS' if test3_ok else '✗ FAIL'}")
    print(f"Test 4 (Full Network): {'✓ PASS' if test4_ok else '✗ FAIL'}")
    
    if test4_ok:
        print("\n🎉 All tests passed! The issue might be with the large network size.")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
