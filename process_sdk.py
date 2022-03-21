import os
import shutil
from pathlib import Path
import subprocess
from zipfile import ZipFile
import tempfile
import shlex

import requests
from alive_progress import alive_bar

import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s %(levelname)s %(message)s',
                    datefmt='%a %d %b %Y %H:%M:%S')


ROOT_DIR = Path(__file__).absolute().parent

SDK_PATH = None
IDA_PATH = None
OUT_DIR = ROOT_DIR / 'output_tils'

def prepare_ida(sdkver):
    d = ROOT_DIR / 'idatools'
    d.mkdir(exist_ok=True)

    def downfile(url, fn=None):
        logging.info('Downloading: %s', url)
        if not fn:
            fn = url.split('/')[-1]
        if isinstance(fn, Path):
            p = fn
        else:
            p = d / fn
        r = requests.get(url, stream=True)
        l = int(r.headers['Content-Length'])
        
        with open(p, 'wb') as f:
            with alive_bar((l-1)//1024 + 1, force_tty=True) as bar:
                for i in r.iter_content(chunk_size=1024):
                    f.write(i)
                    bar()
    
    global SDK_PATH, IDA_PATH
    SDK_PATH = d / f'idasdk{sdkver}'
    IDA_PATH = d / 'ida77'
    if not SDK_PATH.exists():
        logging.info('Preparing IDA SDK...')
        downfile('https://github.com/NyaMisty/idasdk-collection/raw/master/' + f'idasdk{sdkver}.zip')
        shutil.unpack_archive(d / f'idasdk{sdkver}.zip', d)
        SDK_PATH = d / f'idasdk{sdkver}'
        
        hx_file = 'hexrays%s.hpp' % sdkver
        downfile('https://github.com/NyaMisty/idasdk-collection/raw/master/' + hx_file, SDK_PATH / 'include' / 'hexrays.hpp')
    
    if not IDA_PATH.exists():
        logging.info('Preparing IDA Tools...')
        downfile('https://onepoint.misty.workers.dev/gd-pub-temp/ida-leak-wine/IDA-7.7.220118-fullpatch-wine.zip', 'ida77.zip')   
        IDA_PATH.mkdir()
        shutil.unpack_archive(d / 'ida77.zip', IDA_PATH)
        
        downfile('https://github.com/NyaMisty/idasdk-collection/raw/master/idaclang77.zip')
        with ZipFile(d / 'idaclang77.zip', 'r') as z:
            with open(IDA_PATH / 'idaclang.exe', 'wb') as f:
                f.write(z.read('idaclang77/win/idaclang.exe'))
        shutil.unpack_archive(d / 'idaclang77.zip', d)
        downfile('https://github.com/NyaMisty/idasdk-collection/raw/master/tilib77.zip')
        with ZipFile(d / 'tilib77.zip', 'r') as z:
            with open(IDA_PATH / 'tilib.exe', 'wb') as f:
                f.write(z.read('tilib77/win/tilib.exe'))
            with open(IDA_PATH / 'tilib64.exe', 'wb') as f:
                f.write(z.read('tilib77/win/tilib64.exe'))


def get_til_prefix(platform, version):
    return 'ida%s%s' % (platform, version)

def call_process(*args, **kwargs):
    logging.info("Running: \n    [%s]" % 
        shlex.join(list(map(str, args[0])))
    )
    return subprocess.call(*args, **kwargs)

def do_idaclang_build(platform, version):
    build_dir = ROOT_DIR / 'sdkhdr_build' / f'idasdk_{platform}'
    ida_path = Path(os.path.relpath(IDA_PATH, build_dir))
    sdk_path = Path(os.path.relpath(SDK_PATH, build_dir))
    out_dir = Path(os.path.relpath(OUT_DIR, build_dir))
    toLinuxPath = lambda x: str(x).replace('\\', '/')
    command = [
        'make',
        '-f', '%s' % (f'idasdk_{platform}.mak'),
        'TIL_NAME=%s' % get_til_prefix(platform, version), 
        'IDASDK_DESC=%s' % (f"IDA{version} {platform}"), 
        'IDASDK=%s' % toLinuxPath(sdk_path),
        'IDACLANG=%s' % toLinuxPath(ida_path / 'idaclang.exe'),
        'TILIB64=%s' % toLinuxPath(ida_path / 'tilib64.exe'),
        'TIL_OUT_DIR=%s' % toLinuxPath(out_dir)
        ]
    
    call_process(command, cwd=build_dir)

def do_idatil_extract(libtype, platform, version):
    build_dir = ROOT_DIR / 'sdklib_build'
    libpath = SDK_PATH / 'lib' / libtype
    objs = libpath / 'objs'
    objs.mkdir(exist_ok=True)
    call_process(['7z', 'e', '-aoa', libpath / 'pro.lib'], cwd=objs)
    call_process(['7z', 'e', '-aoa', libpath / 'network.lib'], cwd=objs)
    call_process(['7z', 'e', '-aoa', libpath / 'compress.lib'], cwd=objs)
    call_process(['7z', 'e', '-aoa', libpath / 'unicode.lib'], cwd=objs)
    with tempfile.TemporaryDirectory() as tmpdir:
        idaenv = dict(os.environ)
        idaenv['TVHEADLESS'] = "1"
        logfile = Path(tmpdir) / 'til_extract.log'
        idaenv['IDALOG'] = str(logfile)
        def readlog():
            with open(logfile, 'r') as f:
                logcontent = f.read()
                logging.info('ida log: %s', logcontent)
            logfile.unlink()
        for c in objs.glob('*'):
            if c.suffix in ('.txt', '.til', '.id0', '.id1', '.nam'):
                continue
            logging.info("exporting til for %s", c.name)
            outputtil = c.with_suffix('.til')
            if outputtil.exists():
                continue
            call_process([IDA_PATH / 'idat64.exe', '-c', '-A', '-S%s %s' % (build_dir / 'export_til.py', outputtil), c], env=idaenv, cwd=objs)
            readlog()
    
        for c in objs.glob('*.til'):
            logging.info("disabling ordinal types for %s", c.name)
            call_process([IDA_PATH / 'tilib64.exe', '-#-', c], cwd=objs)
        
        tilname = f'{get_til_prefix(platform, version)}_libtypes'
        outputtil = OUT_DIR / (tilname + '.til')
        call_process([IDA_PATH / 'idat64.exe', '-c', '-A', '-S"%s" "%s" "%s" "%s" "%s"' % 
            (build_dir / 'merge_til.py', outputtil, tilname, f"SDK static lib types for IDA{version} {platform}", objs), 
            '-t'], env=idaenv, cwd=objs)
        readlog()

        call_process([IDA_PATH / 'tilib64.exe', '-#-', outputtil], cwd=objs)

def do_export_til_headers():
    for c in OUT_DIR.glob('*.til'):
        h = c.with_suffix('.h')
        with tempfile.TemporaryDirectory() as tmpdir:
            tmptil = Path(shutil.copy(c, tmpdir))
            with open(h, 'wb') as f:
                subprocess.run([IDA_PATH / 'tilib64.exe', '-lc', tmptil], cwd=OUT_DIR, stdout=f)
        py = c.with_suffix('.py')
        call_process(['python3', ROOT_DIR / 'tils2py' / 'gen_interop_til.py', h, py], cwd=OUT_DIR)

def main(args):
    sdk_ver = args[0]
    prepare_ida(sdk_ver)
    OUT_DIR.mkdir(exist_ok=True)
    do_idaclang_build('win', sdk_ver)
    do_idatil_extract('x64_win_vc_64_s', 'win', sdk_ver)
    do_export_til_headers()

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])