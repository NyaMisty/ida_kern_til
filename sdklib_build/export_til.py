from idaapi import *
import idc

# turn on coagulation of data in the final pass of analysis
set_inf_attr(INF_AF, get_inf_attr(INF_AF) | AF_DODATA | AF_FINAL);
# .. and plan the entire address space for the final pass
auto_mark_range(0, BADADDR, AU_FINAL);

msg("Waiting for the end of the auto analysis...\n");
auto_wait();

msg("Analysis finished, dumping til..\n");

set_database_flag(DBFL_KILL)

try:
    TILPATH = idc.ARGV[1]
    
    import os
    TILPATH = os.path.abspath(TILPATH)
    
    store_til(cvar.idati, None, TILPATH)
    #set_database_flag(DBFL_TEMP)
    qexit(0)
except:
    import traceback; traceback.print_exc()
    qexit(1)