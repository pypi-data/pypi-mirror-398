# Path: usekit.classes.data.base.init.wrap.txt.dbi_simple_txt.py
# -----------------------------------------------------------------------------------------------
#  Simple Txt IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.1: Optimized to call wrap functions directly (removed duplicate wrapper layer)
# -----------------------------------------------------------------------------------------------
#    act: r / w / u / d / e : read / write / update / delete / exists
#    obj: t : txt
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format, _wrap_write_format
)
from usekit.classes.data.base.init.wrap.txt.dbi_wrap_txt import (
    # READ
    read_txt_base, read_txt_sub, read_txt_dir, read_txt_now, 
    read_txt_tmp, read_txt_pre, read_txt_cache,
    # WRITE
    write_txt_base, write_txt_sub, write_txt_dir, write_txt_now,
    write_txt_tmp, write_txt_pre, write_txt_cache,
    # UPDATE
    update_txt_base, update_txt_sub, update_txt_dir, update_txt_now,
    update_txt_tmp, update_txt_pre, update_txt_cache,
    # DELETE
    delete_txt_base, delete_txt_sub, delete_txt_dir, delete_txt_now,
    delete_txt_tmp, delete_txt_pre, delete_txt_cache,
    # EXISTS
    exists_txt_base, exists_txt_sub, exists_txt_dir, exists_txt_now,
    exists_txt_tmp, exists_txt_pre, exists_txt_cache,
)

# ===============================================================================
# TxtSimple class - Ultra-short interface with alias support
# ===============================================================================

class TxtSimple:
    """
    Ultra-short txt wrapper with full alias support
    
    Features:
    - 3-letter function names (act.obj.loc)
    - Positional arguments support
    - Full parameter names (name, data, dir_path, keydata)
    - Alias parameters (nm, dt, dp, kd)
    - Mix and match any style
    
    Examples:
        # Positional (shortest)
        TxtSP.rtb("config")
        TxtSP.wtb({"x": 1}, "config")
        
        # Original parameters
        TxtSP.rtb(name="config", keydata="user")
        TxtSP.wtb(data={"x": 1}, name="config")
        
        # Alias parameters (recommended)
        TxtSP.rtb(nm="config", kd="user")
        TxtSP.wtb(dt={"x": 1}, nm="config")
        
        # Mixed (natural)
        TxtSP.rtb("config", kd="user/email")
        TxtSP.wtb({"x": 1}, nm="config", dp="session")
    """

    # ─────────────────────────────────────
    # READ (rc*)
    # ─────────────────────────────────────
    @staticmethod
    def rtb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read txt base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_txt_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rts(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read txt sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_txt_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rtd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read txt dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_txt_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rtn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read txt now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_txt_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rtt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read txt tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_txt_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rtp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read txt pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_txt_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rtc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read txt cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_txt_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # WRITE (wc*)
    # ─────────────────────────────────────
    @staticmethod
    def wtb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write txt base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_txt_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wts(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write txt sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_txt_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wtd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write txt dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_txt_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wtn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write txt now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_txt_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wtt(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write txt tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_txt_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wtp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write txt pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_txt_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wtc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write txt cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_txt_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # UPDATE (uc*)
    # ─────────────────────────────────────
    @staticmethod
    def utb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update txt base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_txt_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def uts(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update txt sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_txt_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def utd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update txt dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_txt_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def utn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update txt now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_txt_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def utt(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update txt tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_txt_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def utp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update txt pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_txt_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def utc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update txt cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_txt_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # DELETE (dc*)
    # ─────────────────────────────────────
    @staticmethod
    def dtb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete txt base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_txt_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dts(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete txt sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_txt_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dtd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete txt dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_txt_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dtn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete txt now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_txt_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dtt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete txt tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_txt_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dtp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete txt pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_txt_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dtc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete txt cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_txt_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # EXISTS (ec*)
    # ─────────────────────────────────────
    @staticmethod
    def etb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """exists txt base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(exists_txt_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ets(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """exists txt sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(exists_txt_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def etd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """exists txt dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(exists_txt_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def etn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """exists txt now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(exists_txt_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ett(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """exists txt tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(exists_txt_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def etp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """exists txt pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(exists_txt_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def etc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """exists txt cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(exists_txt_cache)(name, dir_path, keydata, cus, **kwargs)

# Singleton-style export
TxtSP = TxtSimple()

__all__ = [
    "TxtSimple",
    "TxtSP",
]
