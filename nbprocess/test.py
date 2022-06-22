# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/14_test.ipynb.

# %% auto 0
__all__ = ['test_nb', 'nbprocess_test']

# %% ../nbs/14_test.ipynb 1
import time,os,sys,traceback,contextlib, inspect
from fastcore.basics import *
from fastcore.imports import *
from fastcore.foundation import *
from fastcore.parallel import *
from fastcore.script import *


from .read import *
from .doclinks import *
from .process import NBProcessor
from logging import warning

from execnb.nbio import *
from execnb.shell import *

# %% ../nbs/14_test.ipynb 3
def test_nb(fn, skip_flags=None, force_flags=None, do_print=False, showerr=True):
    "Execute tests in notebook in `fn` except those with `skip_flags`"
    if not IN_NOTEBOOK: os.environ["IN_TEST"] = '1'
    flags=set(L(skip_flags)) - set(L(force_flags))
    nb = NBProcessor(fn, process=True).nb

    def _no_eval(cell):
        if cell.cell_type != 'code': return True
        direc = getattr(cell, 'directives_', {}) or {}
        if direc.get('eval:', [''])[0].lower() == 'false': return True
        return flags & direc.keys()
    
    start = time.time()
    k = CaptureShell(fn)
    if do_print: print(f'Starting {fn}')
    try:
        k.run_all(nb, exc_stop=True, preproc=_no_eval)
        res = True
    except: 
        if showerr: warning(k.prettytb(fname=fn))
        res=False
    if do_print: print(f'- Completed {fn}')
    return res,time.time()-start

# %% ../nbs/14_test.ipynb 8
def _keep_file(fname:str, # filename for which to check for `indicator_fname`
               ignore_fname:str # filename that will result in siblings being ignored
                ) -> bool:
    "Returns False if `indicator_fname` is a sibling to `fname` else True"
    p = Path(fname)
    if p.exists(): return not bool(p.parent.ls().attrgot('name').filter(lambda x: x == ignore_fname))
    else: True

# %% ../nbs/14_test.ipynb 11
@call_parse
def nbprocess_test(
    fname:str=None,  # A notebook name or glob to test
    flags:str='',  # Space separated list of test flags you want to run that are normally ignored
    n_workers:int=None,  # Number of workers to use
    timing:bool=False,  # Timing each notebook to see the ones are slow
    do_print:str=False, # Print start and end of each NB
    pause:float=0.01,  # Pause time (in secs) between notebooks to avoid race conditions
    ignore_fname:str='.notest' # filename that will result in siblings being ignored
):
    "Test in parallel the notebooks matching `fname`, passing along `flags`"
    skip_flags = config_key('tst_flags', '', path=False).split()
    force_flags = flags.split()
    files = [Path(f).absolute() for f in sorted(nbglob(fname)) if _keep_file(f, ignore_fname)]
    if len(files)==0:
        print('No files were eligible for testing')
        return
    if n_workers is None: n_workers = 0 if len(files)==1 else min(num_cpus(), 8)
    os.chdir(config_key("nbs_path"))
    results = parallel(test_nb, files, skip_flags=skip_flags, force_flags=force_flags, n_workers=n_workers, pause=pause, do_print=do_print)
    passed,times = zip(*results)
    if all(passed): print("Success.")
    else: 
        _fence = '='*50
        failed = '\n\t'.join(f.name for p,f in zip(passed,files) if not p)
        sys.stderr.write(f"\nnbprocess Tests Failed On The Following Notebooks:\n{_fence}\n\t{failed}")
        exit(1)
    if timing:
        for i,t in sorted(enumerate(times), key=lambda o:o[1], reverse=True): print(f"{files[i].name}: {int(t)} secs")
