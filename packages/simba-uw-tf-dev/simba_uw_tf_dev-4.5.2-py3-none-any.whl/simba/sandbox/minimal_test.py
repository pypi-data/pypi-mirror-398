"""
Minimal PyVista Test - Find the exact issue
"""

import pyvista as pv
import numpy as np
from pathlib import Path

def test_1_basic_sphere():
    """Test 1: Just a basic sphere"""
    print("Test 1: Basic sphere...")
    try:
        sphere = pv.Sphere()
        plotter = pv.Plotter(off_screen=True)
        plotter.add_mesh(sphere)
        plotter.screenshot("test1_sphere.png")
        plotter.close()
        print("✓ Test 1 PASSED")
        return True
    except Exception as e:
        print(f"✗ Test 1 FAILED: {e}")
        return False

def test_2_simple_points():
    """Test 2: Simple points"""
    print("Test 2: Simple points...")
    try:
        points = np.random.uniform(-5, 5, (10, 3))
        poly = pv.PolyData(points)
        plotter = pv.Plotter(off_screen=True)
        plotter.add_mesh(poly, color='blue', point_size=8)
        plotter.screenshot("test2_points.png")
        plotter.close()
        print("✓ Test 2 PASSED")
        return True
    except Exception as e:
        print(f"✗ Test 2 FAILED: {e}")
        return False

def test_3_points_with_lines():
    """Test 3: Points with lines"""
    print("Test 3: Points with lines...")
    try:
        points = np.random.uniform(-5, 5, (5, 3))
        poly = pv.PolyData(points)
        
        # Add simple lines
        lines = np.array([0, 1, 1, 2, 2, 3, 3, 4])
        poly.lines = lines
        
        plotter = pv.Plotter(off_screen=True)
        plotter.add_mesh(poly, color='blue', point_size=8)
        plotter.screenshot("test3_points_lines.png")
        plotter.close()
        print("✓ Test 3 PASSED")
        return True
    except Exception as e:
        print(f"✗ Test 3 FAILED: {e}")
        return False

def test_4_interactive_only():
    """Test 4: Interactive plotter (not off-screen)"""
    print("Test 4: Interactive plotter...")
    try:
        points = np.random.uniform(-5, 5, (10, 3))
        poly = pv.PolyData(points)
        
        plotter = pv.Plotter()  # Interactive, not off-screen
        plotter.add_mesh(poly, color='blue', point_size=8)
        print("✓ Test 4 PASSED - Interactive plotter works")
        print("Close the window to continue...")
        plotter.show()
        return True
    except Exception as e:
        print(f"✗ Test 4 FAILED: {e}")
        return False

def test_5_alternative_rendering():
    """Test 5: Alternative rendering method"""
    print("Test 5: Alternative rendering...")
    try:
        points = np.random.uniform(-5, 5, (10, 3))
        poly = pv.PolyData(points)
        
        # Try different plotter settings
        plotter = pv.Plotter(off_screen=True, window_size=[400, 300])
        plotter.add_mesh(poly, color='blue', point_size=8, render_points_as_spheres=True)
        
        # Try different screenshot method
        img = plotter.screenshot(return_img=True)
        print(f"Screenshot shape: {img.shape}")
        
        plotter.close()
        print("✓ Test 5 PASSED")
        return True
    except Exception as e:
        print(f"✗ Test 5 FAILED: {e}")
        return False

if __name__ == "__main__":
    print("Minimal PyVista Tests")
    print("=" * 30)
    
    # Run tests
    test1 = test_1_basic_sphere()
    test2 = test_2_simple_points()
    test3 = test_3_points_with_lines()
    test4 = test_4_interactive_only()
    test5 = test_5_alternative_rendering()
    
    print("\n" + "=" * 30)
    print("RESULTS:")
    print(f"Test 1 (Basic Sphere): {'✓' if test1 else '✗'}")
    print(f"Test 2 (Simple Points): {'✓' if test2 else '✗'}")
    print(f"Test 3 (Points + Lines): {'✓' if test3 else '✗'}")
    print(f"Test 4 (Interactive): {'✓' if test4 else '✗'}")
    print(f"Test 5 (Alternative): {'✓' if test5 else '✗'}")
    
    if not test1:
        print("\n❌ Basic PyVista functionality is broken!")
    elif not test2:
        print("\n❌ Point rendering is broken!")
    elif not test3:
        print("\n❌ Line rendering is broken!")
    elif not test4:
        print("\n❌ Interactive rendering is broken!")
    else:
        print("\n✅ PyVista is working! The issue might be with off-screen rendering.")
        print("Try using interactive mode instead of off-screen rendering.")
