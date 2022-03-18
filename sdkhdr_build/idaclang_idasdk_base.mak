IDACLANG ?= idaclang
TILIB64 ?= tilib64

ROOT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
TIL_OUT_DIR := $(ROOT_DIR)/output_hdrs

CLANG_ARGV += -ferror-limit=50 -I$(ROOT_DIR)/include
IDACLANG_ARGS += --idaclang-log-all

SDK_HEADER := $(ROOT_DIR)/idasdk.h
BASE_HEADER := $(ROOT_DIR)/base.h
HEXRAYS_HEADER := $(ROOT_DIR)/hexrays.h

BASE_TIL := $(TIL_OUT_DIR)/$(TIL_NAME)_base.til
SDK_TIL := $(TIL_OUT_DIR)/$(TIL_NAME)_sdk.til
HEXRAYS_TIL := $(TIL_OUT_DIR)/$(TIL_NAME)_hexrays.til

TILS = $(BASE_TIL) $(SDK_TIL) $(HEXRAYS_TIL)

.PHONY: all install clean

all: $(TILS)

$(BASE_TIL): $(BASE_HEADER)
	$(IDACLANG) $(IDACLANG_ARGS) --idaclang-tilname $(basename $@) --idaclang-tildesc "Base types for $(IDASDK_DESC)" $(CLANG_ARGV) $<

$(SDK_TIL): $(SDK_HEADER) $(BASE_TIL)
	$(IDACLANG) $(IDACLANG_ARGS) --idaclang-tilname $(basename $@) --idaclang-tildesc "SDK types for $(IDASDK_DESC)" $(CLANG_ARGV) $<
	$(TILIB64) -b$(BASE_TIL) -u+ $@

$(HEXRAYS_TIL): $(HEXRAYS_HEADER) $(SDK_TIL)
	$(IDACLANG) $(IDACLANG_ARGS) --idaclang-tilname $(basename $@) --idaclang-tildesc "HexRays types for $(IDASDK_DESC)" $(CLANG_ARGV) $<
	$(TILIB64) -b$(SDK_TIL) -u+ $@

#%.h: %.til
#	$(TILIB64) -lc $< > $@


#install_hdr: %.h
#	mkdir -p "$(ROOT_DIR)/output_hdrs"
#	cp $^ "$(ROOT_DIR)/output_hdrs"

clean:
	rm -f *.til *.txt *.log
