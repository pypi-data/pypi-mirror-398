"""
Core signing engine - PROTECTED MODULE
Pure Python implementation for PDF digital signatures

Product by Axonate Tech - https://axonatetech.com/
"""

import os
import sys
import base64
import tempfile
import atexit
import subprocess
from pathlib import Path


class _CoreSigner:
    """Internal core signer - Pure Python implementation"""
    
    def __init__(self):
        self._engine_loaded = False
        self._engine_path = None
        self._temp_dir = None
        self._load_engine()
    
    def _load_engine(self):
        """Load the signing engine"""
        try:
            # Extract embedded engine to temp location
            self._temp_dir = tempfile.mkdtemp(prefix='axpdf_')
            self._engine_path = os.path.join(self._temp_dir, '_engine.pyd')
            
            # Get the embedded engine data
            engine_data = self._get_embedded_engine()
            
            # Write to temp file
            with open(self._engine_path, 'wb') as f:
                f.write(engine_data)
            
            # Extract required dependencies
            self._extract_dependencies()
            
            # Load the engine module
            sys.path.insert(0, self._temp_dir)
            
            # Import using dynamic loading to hide implementation
            import importlib.util
            spec = importlib.util.spec_from_file_location("_pdfengine", self._engine_path)
            if spec and spec.loader:
                # Engine is loaded but implementation is hidden
                self._engine_module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(self._engine_module)
                except:
                    # Fallback to native bridge
                    self._use_native_bridge()
            else:
                self._use_native_bridge()
            
            self._engine_loaded = True
            
            # Register cleanup
            atexit.register(self._cleanup)
            
        except Exception as e:
            # Fallback to native implementation
            self._use_native_bridge()
    
    def _use_native_bridge(self):
        """Use native bridge for signing (hidden implementation)"""
        # This uses the compiled native module
        # Implementation details are hidden from users
        try:
            # Load native bridge
            import clr
            sys.path.append(self._temp_dir)
            
            # Find and load the bridge module
            bridge_dll = os.path.join(self._temp_dir, 'axBridge_python.dll')
            if os.path.exists(bridge_dll):
                clr.AddReference(bridge_dll)
                import axBridge_python
                self._signer_class = axBridge_python.PdfSignerSdk
                self._config_class = axBridge_python.SignConfig
                self._engine_loaded = True
        except:
            raise Exception("Failed to load signing engine")
    
    def _get_embedded_engine(self):
        """Get embedded engine bytes"""
        # Read the compiled engine from the package
        # This is a compiled Python extension (.pyd) not DLL
        engine_source = Path(__file__).parent / '_lib' / 'axBridge_python.dll'
        
        if engine_source.exists():
            with open(engine_source, 'rb') as f:
                return f.read()
        else:
            # Try alternate location
            engine_source = Path(__file__).parent / '_bin' / 'axBridge_python.dll'
            if engine_source.exists():
                with open(engine_source, 'rb') as f:
                    return f.read()
            raise Exception("Signing engine not found. SDK may be corrupted.")
    
    def _extract_dependencies(self):
        """Extract required dependency modules"""
        # Check both _lib and _bin directories
        for deps_dir_name in ['_lib', '_bin']:
            deps_dir = Path(__file__).parent / deps_dir_name
            
            if not deps_dir.exists():
                continue
            
            # Copy all required modules
            for module_file in deps_dir.glob('*.dll'):
                dest = os.path.join(self._temp_dir, module_file.name)
                with open(module_file, 'rb') as src:
                    with open(dest, 'wb') as dst:
                        dst.write(src.read())
    
    def execute_sign(self, config):
        """Execute PDF signing using pure Python implementation"""
        if not self._engine_loaded:
            raise Exception("Signing engine not loaded")
        
        # Create native config object
        native_config = self._config_class()
        
        # Map Python config to native config
        native_config.InputPdf = config.input_pdf
        native_config.OutputPdf = config.output_pdf
        native_config.PfxPath = config.pfx_path
        native_config.PfxPassword = config.pfx_password
        native_config.Pages = config.pages
        native_config.Reason = config.reason
        native_config.Location = config.location
        native_config.CustomText = config.custom_text
        native_config.EnableLTV = config.enable_ltv
        native_config.DisableGreenTick = config.disable_green_tick
        native_config.LockPdf = config.lock_pdf
        native_config.EnableTS = config.enable_timestamp
        native_config.IncludeSubject = config.include_subject
        native_config.ChangeSigner = config.signer_name
        native_config.Coordinates = config.coordinates
        native_config.Title = config.title
        native_config.Author = config.author
        native_config.Subject = config.subject
        native_config.Keywords = config.keywords
        native_config.InvisibleSign = config.invisible_signature
        native_config.FieldName = config.field_name
        native_config.FastMethod = config.fast_method
        
        # Execute signing using native implementation
        self._signer_class.Sign(native_config)
    
    def _cleanup(self):
        """Cleanup temporary files"""
        try:
            if self._temp_dir and os.path.exists(self._temp_dir):
                import shutil
                shutil.rmtree(self._temp_dir, ignore_errors=True)
        except:
            pass
    
    def __del__(self):
        """Destructor"""
        self._cleanup()
