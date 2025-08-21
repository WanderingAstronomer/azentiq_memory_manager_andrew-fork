"""
Diagnostic script to examine Google ADK package structure and import paths.
"""
import sys
import pkgutil
import importlib
import os

def inspect_module(module_name):
    try:
        module = importlib.import_module(module_name)
        print(f"Successfully imported {module_name}")
        print(f"Module file: {getattr(module, '__file__', 'Not available')}")
        print(f"Package path: {getattr(module, '__path__', 'Not a package')}")
        
        # List submodules if it's a package
        if hasattr(module, '__path__'):
            print(f"Submodules of {module_name}:")
            for _, name, is_pkg in pkgutil.iter_modules(module.__path__, module.__name__ + '.'):
                print(f"  - {name} {'[package]' if is_pkg else '[module]'}")
        
        print(f"Attributes/members of {module_name}:")
        for name in dir(module):
            if not name.startswith('_'):  # Skip private/internal attributes
                print(f"  - {name}")
    except ImportError as e:
        print(f"Failed to import {module_name}: {str(e)}")

# Try various potential import paths for Google ADK
print("\n=== Testing Google ADK Import Paths ===")
for module_name in [
    'google_adk',
    'google.adk',
    'adk',
    'google_agent_development_kit',
    'google_agent',
    'google.agent',
]:
    print(f"\nTrying import: {module_name}")
    inspect_module(module_name)

print("\n=== Installed Packages ===")
import site
for site_path in site.getsitepackages():
    print(f"Site-packages path: {site_path}")
    try:
        adk_packages = [p for p in os.listdir(site_path) if 'adk' in p.lower()]
        print(f"ADK-related packages in {site_path}: {adk_packages}")
        
        # If we found ADK packages, look deeper
        for pkg in adk_packages:
            pkg_path = os.path.join(site_path, pkg)
            if os.path.isdir(pkg_path) and not pkg.endswith('.dist-info'):
                print(f"Contents of {pkg}:")
                try:
                    for item in os.listdir(pkg_path):
                        print(f"  - {item}")
                except Exception as e:
                    print(f"  Error listing contents: {str(e)}")
    except Exception as e:
        print(f"Error examining {site_path}: {str(e)}")

print("\n=== sys.modules with ADK ===")
adk_modules = [m for m in sys.modules if 'adk' in m.lower()]
print(f"ADK-related modules already imported: {adk_modules}")

print("\n=== sys.path ===")
for path in sys.path:
    print(path)

print("\n=== pip list output ===")
try:
    import subprocess
    result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                           capture_output=True, text=True)
    print(result.stdout)
except Exception as e:
    print(f"Error running pip list: {str(e)}")

if 'google_adk-1.11.0.dist-info' in adk_packages:
    print("\n=== Checking google_adk distribution metadata ===")
    try:
        import importlib.metadata
        dist = importlib.metadata.distribution('google-adk')
        print(f"Entry points: {list(dist.entry_points)}")
        print(f"Files: {list(dist.files)}")
    except Exception as e:
        print(f"Error accessing metadata: {str(e)}")
