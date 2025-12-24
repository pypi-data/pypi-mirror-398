import sys
import platform
import importlib.util
from pathlib import Path

# Supported CPU architecture types
ARCH_TYPES = {
    "avx512_amx": "AVX512 with AMX",
    "avx512": "AVX512",
    "avx2": "AVX2"
}

# Detect if current CPU supports specific instruction sets 
def _detect_cpu_features():
    if platform.system() != "Linux":
        # Only Linux is supported
        print("Warning: Only Linux is supported for dynamic CPU feature detection.")
        return "avx2"  # Default to the lowest version
    
    try:
        # Use /proc/cpuinfo for more universal compatibility
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read().lower()
        
        # Check for AMX instruction set support
        if 'amx_bf16' in cpuinfo or 'amx_tile' in cpuinfo or 'amx_int8' in cpuinfo:
            print("Detected CPU with AMX support")
            return "avx512_amx"
        
        # Check for AVX512 instruction set support
        if 'avx512f' in cpuinfo:
            print("Detected CPU with AVX512 support")
            return "avx512"
        
        # Check for AVX2 instruction set support
        if 'avx2' in cpuinfo:
            print("Detected CPU with AVX2 support")
            return "avx2"
        
        # No advanced instruction sets supported, use basic version
        print("Detected CPU with basic instruction set support")
        return "avx2"  # Default to avx2 as minimum requirement
    except Exception as e:
        print(f"Error detecting CPU features: {e}")
        return "avx2"  # Default to lowest version on error

# Dynamically load the appropriate SO file
def _load_library():
    # Get current module directory
    module_dir = Path(__file__).parent
    
    # Detect CPU features
    arch_type = _detect_cpu_features()
    
    so_filename = f"_lk_moe_C_{arch_type}.so"
    so_path = module_dir / so_filename
    
    # Fallback logic if the specific architecture version is not found
    if not so_path.exists():
        for fallback_arch in ["avx512", "avx2"]:
            fallback_so_path = module_dir / f"_lk_moe_C_{fallback_arch}.so"
            if fallback_so_path.exists():
                print(f"Requested {arch_type} version not found, falling back to {fallback_arch}")
                so_path = fallback_so_path
                arch_type = fallback_arch
                break
        else: 
            generic_so_files = list(module_dir.glob("_lk_moe_C.cpython-*.so"))
            if generic_so_files:
                so_path = generic_so_files[0]
                print(f"No architecture-specific files found, using generic file {so_path.name}")
            else:
                raise ImportError(f"No compatible _lk_moe_C library found in {module_dir}")
    
    print(f"Loading {so_path.name}")
     
    try: 
        spec = importlib.util.spec_from_file_location("_lk_moe_C", str(so_path))
        if spec is None:
            raise ImportError(f"Could not create spec for {so_path}")
         
        module = importlib.util.module_from_spec(spec)
         
        spec.loader.exec_module(module)
         
        if hasattr(module, 'MOE') and hasattr(module, 'MOEConfig') and hasattr(module, 'MOE_FP8') and hasattr(module, 'MOE_FP8Config') and hasattr(module, 'MOE_WNA16') and hasattr(module, 'MOE_WNA16Config'):
            print("Successfully loaded MOE, MOEConfig, MOE_FP8, MOE_FP8Config, MOE_WNA16, and MOE_WNA16Config") 
            return module.MOE, module.MOEConfig, module.MOE_FP8, module.MOE_FP8Config, module.MOE_WNA16, module.MOE_WNA16Config
        else:
            raise AttributeError("MOE, MOEConfig, MOE_FP8, MOE_FP8Config, MOE_WNA16, or MOE_WNA16Config not found in the module")
    except Exception as e:
        print(f"Error loading library: {e}")
        raise ImportError(f"Failed to load {so_path}")