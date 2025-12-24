import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
DLL_DIR_NAME = 'DLL_DIR'
DLL_DIR_PATH = os.path.join(BASE_DIR, DLL_DIR_NAME) 

if sys.platform == "win32" and os.path.exists(DLL_DIR_PATH):
    try:
        os.add_dll_directory(DLL_DIR_PATH)
    except AttributeError:
        os.environ['PATH'] = DLL_DIR_PATH + os.pathsep + os.environ['PATH']

try:
    from . import _slmtk 
except ImportError as e:
    raise ImportError(f"Cannot load C++ extension module (_slmtk). More information: {e}")

run_rbtn_sdk = _slmtk.run_rbtn_sdk
run_parser_sdk = _slmtk.run_parser_sdk
run_parser2transx_sdk = _slmtk.run_parser2transx_sdk
run_poly_sdk = _slmtk.run_poly_sdk
run_tonesandhi_sdk = _slmtk.run_tonesandhi_sdk
run_FW2CHPOS_sdk = _slmtk.run_FW2CHPOS_sdk
run_engtransx_sdk = _slmtk.run_engtransx_sdk
run_bp_sdk = _slmtk.run_bp_sdk
run_psp_sdk = _slmtk.run_psp_sdk
run_paf_sdk = _slmtk.run_paf_sdk
run_SS_sdk = _slmtk.run_SS_sdk
run_TTS = _slmtk.run_TTS