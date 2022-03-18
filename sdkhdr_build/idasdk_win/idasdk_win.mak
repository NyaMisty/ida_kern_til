TIL_NAME = idasdk_win
IDASDK_DESC = "IDA SDK headers for x64 Windows"
CLANG_ARGV = -target x86_64-pc-win32       \
             -x c++                        \
             -I$(IDASDK)/include          \
             -D__NT__                      \
             -D__EA64__                    \
             -Wno-nullability-completeness -nostdlib 

include ../idaclang_idasdk_base.mak
