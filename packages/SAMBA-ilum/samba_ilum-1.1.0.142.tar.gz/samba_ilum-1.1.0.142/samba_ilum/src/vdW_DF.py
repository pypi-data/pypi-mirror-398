# SAMBA_ilum Copyright (C) 2025
# GNU GPL-3.0 license


if (vdWDF != 'none'):
   #==================
   if (vdWDF == 'DF'):
      replace_vdW_DF = "GGA       = RE \nAGGAC     = 0.0 \nLUSE_VDW  = .TRUE. \nLASPH     = .TRUE."
   #-------------------
   if (vdWDF == 'DF2'):
      replace_vdW_DF = "GGA       = ML \nAGGAC     = 0.0 \nLUSE_VDW  = .TRUE. \nZAB_VDW   = -1.8867 # the default is -0.8491 \nLASPH     = .TRUE."
   #-------------------
   if (vdWDF == 'optPBE'):
      replace_vdW_DF = "GGA       = OR \nAGGAC     = 0.0 \nLUSE_VDW  = .TRUE. \nLASPH     = .TRUE."
   #-------------------
   if (vdWDF == 'optB88'):
      replace_vdW_DF = "GGA       = BO \nPARAM1    = 0.1833333333 \nPARAM2    = 0.22 \nAGGAC     = 0.0 \nLUSE_VDW  = .TRUE. \nLASPH     = .TRUE."
   #-------------------
   if (vdWDF == 'optB86b'):
      replace_vdW_DF = "GGA       = MK \nPARAM1    = 0.1234 \nPARAM2    = 1.0 \nAGGAC     = 0.0 \nLUSE_VDW  = .TRUE. \nLASPH     = .TRUE."
   #-------------------
   if (vdWDF == 'rev-DF2'):
      replace_vdW_DF = "GGA       = MK \nPARAM1    = 0.1234568 # =10/81 \nPARAM2    = 0.7114 \nAGGAC     = 0.0 \nLUSE_VDW  = .TRUE. \nZAB_VDW   = -1.8867 # the default is -0.8491 \nLASPH     = .TRUE."
   #-------------------
   if (vdWDF == 'DF-cx'):
      replace_vdW_DF = "GGA       = CX \nAGGAC     = 0.0 \nLUSE_VDW  = .TRUE. \nLASPH     = .TRUE."
   #-------------------
   if (vdWDF == 'DF3-opt1'):
      replace_vdW_DF = "GGA       = BO \nPARAM1    = 0.1122334456 \nPARAM2    = 0.1234568 # =10/81 \nAGGAC     = 0.0 \nLUSE_VDW  = .TRUE. \nIVDW_NL   = 3 \nALPHA_VDW = 0.94950 # default for IVDW_NL=3 but can be overwritten by this tag \nGAMMA_VDW = 1.12    # default for IVDW_NL=3 but can be overwritten by this tag \nLASPH     = .TRUE."
   #-------------------
   if (vdWDF == 'DF3-opt2'):
      replace_vdW_DF = "GGA       = MK \nPARAM1    = 0.1234568 # =10/81 \nPARAM2    = 0.58 \nAGGAC     = 0.0 \nLUSE_VDW  = .TRUE. \nIVDW_NL   = 4 \nZAB_VDW   = -1.8867 # the default is -0.8491 \nALPHA_VDW = 0.28248 # default for IVDW_NL=4 but can be overwritten by this tag \nGAMMA_VDW = 1.29    # default for IVDW_NL=4 but can be overwritten by this tag \nLASPH     = .TRUE."


#===============================================================
if (vdW == 0 and vdWDF != 'none'): replace_type_vdW = str(vdWDF)
#===============================================================
