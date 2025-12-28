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
obj2egg = lambda: _exec_tool(u'obj2egg')
apply_patch = lambda: _exec_tool(u'apply_patch')
check_adler = lambda: _exec_tool(u'check_adler')
egg_optchar = lambda: _exec_tool(u'egg-optchar')
egg_texture_cards = lambda: _exec_tool(u'egg-texture-cards')
deploy_stub = lambda: _exec_tool(u'deploy-stub')
egg2c = lambda: _exec_tool(u'egg2c')
check_crc = lambda: _exec_tool(u'check_crc')
text_stats = lambda: _exec_tool(u'text-stats')
pstats = lambda: _exec_tool(u'pstats')
dae2egg = lambda: _exec_tool(u'dae2egg')
interrogate = lambda: _exec_tool(u'interrogate')
check_md5 = lambda: _exec_tool(u'check_md5')
fltcopy = lambda: _exec_tool(u'fltcopy')
egg_qtess = lambda: _exec_tool(u'egg-qtess')
egg_palettize = lambda: _exec_tool(u'egg-palettize')
pfm_bba = lambda: _exec_tool(u'pfm-bba')
interrogate_module = lambda: _exec_tool(u'interrogate_module')
dxf_points = lambda: _exec_tool(u'dxf-points')
punzip = lambda: _exec_tool(u'punzip')
egg_crop = lambda: _exec_tool(u'egg-crop')
lwo2egg = lambda: _exec_tool(u'lwo2egg')
multify = lambda: _exec_tool(u'multify')
egg2dxf = lambda: _exec_tool(u'egg2dxf')
pfm_trans = lambda: _exec_tool(u'pfm-trans')
pview = lambda: _exec_tool(u'pview')
egg2flt = lambda: _exec_tool(u'egg2flt')
build_patch = lambda: _exec_tool(u'build_patch')
flt_info = lambda: _exec_tool(u'flt-info')
egg_topstrip = lambda: _exec_tool(u'egg-topstrip')
egg_rename = lambda: _exec_tool(u'egg-rename')
egg2bam = lambda: _exec_tool(u'egg2bam')
parse_file = lambda: _exec_tool(u'parse_file')
test_interrogate = lambda: _exec_tool(u'test_interrogate')
x_trans = lambda: _exec_tool(u'x-trans')
x2egg = lambda: _exec_tool(u'x2egg')
egg_retarget_anim = lambda: _exec_tool(u'egg-retarget-anim')
image_info = lambda: _exec_tool(u'image-info')
egg_mkfont = lambda: _exec_tool(u'egg-mkfont')
bam2egg = lambda: _exec_tool(u'bam2egg')
pzip = lambda: _exec_tool(u'pzip')
vrml_trans = lambda: _exec_tool(u'vrml-trans')
egg_list_textures = lambda: _exec_tool(u'egg-list-textures')
pencrypt = lambda: _exec_tool(u'pencrypt')
flt2egg = lambda: _exec_tool(u'flt2egg')
vrml2egg = lambda: _exec_tool(u'vrml2egg')
egg_make_tube = lambda: _exec_tool(u'egg-make-tube')
dxf2egg = lambda: _exec_tool(u'dxf2egg')
pdecrypt = lambda: _exec_tool(u'pdecrypt')
egg2obj = lambda: _exec_tool(u'egg2obj')
egg_trans = lambda: _exec_tool(u'egg-trans')
show_ddb = lambda: _exec_tool(u'show_ddb')
p3dcparse = lambda: _exec_tool(u'p3dcparse')
make_prc_key = lambda: _exec_tool(u'make-prc-key')
lwo_scan = lambda: _exec_tool(u'lwo-scan')
bam_info = lambda: _exec_tool(u'bam-info')
egg2x = lambda: _exec_tool(u'egg2x')
flt_trans = lambda: _exec_tool(u'flt-trans')
image_resize = lambda: _exec_tool(u'image-resize')
image_trans = lambda: _exec_tool(u'image-trans')

