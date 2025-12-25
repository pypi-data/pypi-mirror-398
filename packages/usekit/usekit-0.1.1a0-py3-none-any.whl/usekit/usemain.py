# MIT License. See project root LICENSE file.
# Path: usekit.usemain.py
# ----------------------------------------------------------------------------------------------- 
#  a creation by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# ----------------------------------------------------------------------------------------------- 

# [USEKIT TICKER LOG : True/False]
import sys
from usekit.classes.common.utils.helper_timer import _tick, _clear
_clear()
_tick("USEKIT ON")

# [DEBUG MODE LOG : True/False]
from usekit.classes.common.errors.helper_setupdebug import print_loader_debug
print_loader_debug()
_tick("USEKIT import setupdebug")

# [MAIN INTERFACES]
from usekit.classes.wrap.base.use_base import use, u
_tick("USEKIT use loaded")

# [SAFE LOAD LOG: True/False]
from usekit.classes.wrap.safe.use_safe import safe, s
_tick("USEKIT safe loaded")

# [OPTIONAL: PRELOAD SAFE IN BACKGROUND]
# Uncomment to start loading safe immediately (adds ~0s to startup, eliminates 8s first-use delay)
safe.preload()
_tick("USEKIT safe preload started")

# [REFIXING EXTENSIONS]
# Rebinding and reloading optional extension modules for dynamic usekit augmentation
# from usekit.classes.class_ext import ext 
# from usekit.classes.classrefs.refs_use_ext  import utt, uww, uai, udd, u, w, t
# from usekit.classes.classrefs.refs_aliases import uf, e, ef
# from usekit.classes.classrefs.refs_usesafe import usf, stt, sai
# from usekit.classes.classrefs.refs_extsafe import esf

# [EXPORT DEFINITIONS]
__all__ = [    
    "use", "u", "safe", "s"
    # "utt", "uww", "udd", "uai", "ext",
    # "usf", "esf", "u", "uf", "e", "ef", "w", "t"
]

# [LOADER STATUS]
_tick("USEKIT LOAD")
print("[Memory is emotion]")

# ----------------------------------------------------------------------------------------------- 
#  [ withropnfop@gmail.com ]  
# ----------------------------------------------------------------------------------------------- 