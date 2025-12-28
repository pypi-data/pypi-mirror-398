import os, sys
import panda3d

dir = os.path.dirname(panda3d.__file__)
del panda3d

if sys.platform in ('win32', 'cygwin'):
    path_var = 'PATH'
    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(dir)
elif sys.platform == 'darwin':
    path_var = 'DYLD_LIBRARY_PATH'
else:
    path_var = 'LD_LIBRARY_PATH'

if not os.environ.get(path_var):
    os.environ[path_var] = dir
else:
    os.environ[path_var] = dir + os.pathsep + os.environ[path_var]

del os, sys, path_var, dir


def _exec_tool(tool):
    import os, sys
    from subprocess import Popen
    tools_dir = os.path.dirname(__file__)
    handle = Popen(sys.argv, executable=os.path.join(tools_dir, tool))
    try:
        try:
            return handle.wait()
        except KeyboardInterrupt:
            # Give the program a chance to handle the signal gracefully.
            return handle.wait()
    except:
        handle.kill()
        handle.wait()
        raise

# Register all the executables in this directory as global functions.
apply_patch = lambda: _exec_tool(u'apply_patch.exe')
bam_info = lambda: _exec_tool(u'bam-info.exe')
bam2egg = lambda: _exec_tool(u'bam2egg.exe')
build_patch = lambda: _exec_tool(u'build_patch.exe')
cginfo = lambda: _exec_tool(u'cginfo.exe')
check_adler = lambda: _exec_tool(u'check_adler.exe')
check_crc = lambda: _exec_tool(u'check_crc.exe')
check_md5 = lambda: _exec_tool(u'check_md5.exe')
dae2egg = lambda: _exec_tool(u'dae2egg.exe')
deploy_stub = lambda: _exec_tool(u'deploy-stub.exe')
deploy_stubw = lambda: _exec_tool(u'deploy-stubw.exe')
dxf_points = lambda: _exec_tool(u'dxf-points.exe')
dxf2egg = lambda: _exec_tool(u'dxf2egg.exe')
egg_crop = lambda: _exec_tool(u'egg-crop.exe')
egg_list_textures = lambda: _exec_tool(u'egg-list-textures.exe')
egg_make_tube = lambda: _exec_tool(u'egg-make-tube.exe')
egg_mkfont = lambda: _exec_tool(u'egg-mkfont.exe')
egg_optchar = lambda: _exec_tool(u'egg-optchar.exe')
egg_palettize = lambda: _exec_tool(u'egg-palettize.exe')
egg_qtess = lambda: _exec_tool(u'egg-qtess.exe')
egg_rename = lambda: _exec_tool(u'egg-rename.exe')
egg_retarget_anim = lambda: _exec_tool(u'egg-retarget-anim.exe')
egg_texture_cards = lambda: _exec_tool(u'egg-texture-cards.exe')
egg_topstrip = lambda: _exec_tool(u'egg-topstrip.exe')
egg_trans = lambda: _exec_tool(u'egg-trans.exe')
egg2bam = lambda: _exec_tool(u'egg2bam.exe')
egg2c = lambda: _exec_tool(u'egg2c.exe')
egg2dxf = lambda: _exec_tool(u'egg2dxf.exe')
egg2flt = lambda: _exec_tool(u'egg2flt.exe')
egg2maya2008 = lambda: _exec_tool(u'egg2maya2008.exe')
egg2maya2009 = lambda: _exec_tool(u'egg2maya2009.exe')
egg2maya2010 = lambda: _exec_tool(u'egg2maya2010.exe')
egg2maya2011 = lambda: _exec_tool(u'egg2maya2011.exe')
egg2maya2012 = lambda: _exec_tool(u'egg2maya2012.exe')
egg2maya2013 = lambda: _exec_tool(u'egg2maya2013.exe')
egg2maya6 = lambda: _exec_tool(u'egg2maya6.exe')
egg2maya65 = lambda: _exec_tool(u'egg2maya65.exe')
egg2maya7 = lambda: _exec_tool(u'egg2maya7.exe')
egg2maya8 = lambda: _exec_tool(u'egg2maya8.exe')
egg2maya85 = lambda: _exec_tool(u'egg2maya85.exe')
egg2obj = lambda: _exec_tool(u'egg2obj.exe')
egg2x = lambda: _exec_tool(u'egg2x.exe')
ffmpeg = lambda: _exec_tool(u'ffmpeg.exe')
ffplay = lambda: _exec_tool(u'ffplay.exe')
ffprobe = lambda: _exec_tool(u'ffprobe.exe')
flt_info = lambda: _exec_tool(u'flt-info.exe')
flt_trans = lambda: _exec_tool(u'flt-trans.exe')
flt2egg = lambda: _exec_tool(u'flt2egg.exe')
fltcopy = lambda: _exec_tool(u'fltcopy.exe')
image_info = lambda: _exec_tool(u'image-info.exe')
image_resize = lambda: _exec_tool(u'image-resize.exe')
image_trans = lambda: _exec_tool(u'image-trans.exe')
interrogate = lambda: _exec_tool(u'interrogate.exe')
interrogate_module = lambda: _exec_tool(u'interrogate_module.exe')
lwo_scan = lambda: _exec_tool(u'lwo-scan.exe')
lwo2egg = lambda: _exec_tool(u'lwo2egg.exe')
make_prc_key = lambda: _exec_tool(u'make-prc-key.exe')
maya2egg2008 = lambda: _exec_tool(u'maya2egg2008.exe')
maya2egg2009 = lambda: _exec_tool(u'maya2egg2009.exe')
maya2egg2010 = lambda: _exec_tool(u'maya2egg2010.exe')
maya2egg2011 = lambda: _exec_tool(u'maya2egg2011.exe')
maya2egg2012 = lambda: _exec_tool(u'maya2egg2012.exe')
maya2egg2013 = lambda: _exec_tool(u'maya2egg2013.exe')
maya2egg6 = lambda: _exec_tool(u'maya2egg6.exe')
maya2egg65 = lambda: _exec_tool(u'maya2egg65.exe')
maya2egg7 = lambda: _exec_tool(u'maya2egg7.exe')
maya2egg8 = lambda: _exec_tool(u'maya2egg8.exe')
maya2egg85 = lambda: _exec_tool(u'maya2egg85.exe')
mayacopy2008 = lambda: _exec_tool(u'mayacopy2008.exe')
mayacopy2009 = lambda: _exec_tool(u'mayacopy2009.exe')
mayacopy2010 = lambda: _exec_tool(u'mayacopy2010.exe')
mayacopy2011 = lambda: _exec_tool(u'mayacopy2011.exe')
mayacopy2012 = lambda: _exec_tool(u'mayacopy2012.exe')
mayacopy2013 = lambda: _exec_tool(u'mayacopy2013.exe')
mayacopy6 = lambda: _exec_tool(u'mayacopy6.exe')
mayacopy65 = lambda: _exec_tool(u'mayacopy65.exe')
mayacopy7 = lambda: _exec_tool(u'mayacopy7.exe')
mayacopy8 = lambda: _exec_tool(u'mayacopy8.exe')
mayacopy85 = lambda: _exec_tool(u'mayacopy85.exe')
multify = lambda: _exec_tool(u'multify.exe')
obj2egg = lambda: _exec_tool(u'obj2egg.exe')
p3dcparse = lambda: _exec_tool(u'p3dcparse.exe')
parse_file = lambda: _exec_tool(u'parse_file.exe')
pdecrypt = lambda: _exec_tool(u'pdecrypt.exe')
pencrypt = lambda: _exec_tool(u'pencrypt.exe')
pfm_bba = lambda: _exec_tool(u'pfm-bba.exe')
pfm_trans = lambda: _exec_tool(u'pfm-trans.exe')
pstats = lambda: _exec_tool(u'pstats.exe')
punzip = lambda: _exec_tool(u'punzip.exe')
pview = lambda: _exec_tool(u'pview.exe')
pzip = lambda: _exec_tool(u'pzip.exe')
show_ddb = lambda: _exec_tool(u'show_ddb.exe')
test_interrogate = lambda: _exec_tool(u'test_interrogate.exe')
text_stats = lambda: _exec_tool(u'text-stats.exe')
vrml_trans = lambda: _exec_tool(u'vrml-trans.exe')
vrml2egg = lambda: _exec_tool(u'vrml2egg.exe')
x_trans = lambda: _exec_tool(u'x-trans.exe')
x2egg = lambda: _exec_tool(u'x2egg.exe')

