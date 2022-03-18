from idaapi import *
import idc

try:
    if not idc.ARGV:
        TILPATH = r'D:\Workspaces\UtilWorkspace\Reverse\IDAPlugins\ida_kern_til\idatools\idasdk77\lib\x64_win_vc_64_s\final.til'
        TILNAME = 'test'
        TILDESC = 'test'
        TILDIR = r'D:\Workspaces\UtilWorkspace\Reverse\IDAPlugins\ida_kern_til\idatools\idasdk77\lib\x64_win_vc_64_s\objs'
    else:
        TILPATH = idc.ARGV[1]
        TILNAME = idc.ARGV[2]
        TILDESC = idc.ARGV[3]
        TILDIR = idc.ARGV[4]
    
    import os
    TILPATH = os.path.abspath(TILPATH)
    
    
    finaltil = new_til(TILNAME, TILDESC)
    import ctypes
    ctypes.CDLL('ida64.dll').enable_numbered_types(ctypes.c_void_p(int(finaltil.this)), 1)
    assert type(finaltil) == til_t
    
    
    from pathlib import Path
    # note: cannot handle duplicated type names!
    for smalltil in Path(TILDIR).glob('*.til'):
        print('merging til %s' % smalltil)
        til = load_til(str(smalltil), None)
        assert type(til) == til_t
        
        COPY_BY_ORD = False
        if COPY_BY_ORD:
            qty = get_ordinal_qty(til)
            print('total %d types' % qty)
            for typeord in range(1, qty):
                name = get_numbered_type_name(til, typeord)
                if name:
                    succ = copy_named_type(finaltil, til, name) != 0
                    print('Copying type: %s, %s' % (name, 'succ' if succ else 'fail'))
                else:
                    print('noname: %d' % typeord)
                    pass
        else:
            name = first_named_type(til, NTF_TYPE)
            while name:
                succ = copy_named_type(finaltil, til, name) != 0
                print('Copying type: %s, %s' % (name, 'succ' if succ else 'fail'))
                name = next_named_type(til, name, NTF_TYPE)
    
    name = first_named_type(finaltil, NTF_TYPE)
    while name:
        print('Final types: %s' % name)
        name = next_named_type(finaltil, name, NTF_TYPE)
    
    print('Writing final til to %s' % TILPATH)
    assert store_til(finaltil, None, TILPATH)
    if True:
        set_database_flag(DBFL_KILL)
        #set_database_flag(DBFL_TEMP)
        qexit(0);
except:
    import traceback; traceback.print_exc()
    qexit(1)