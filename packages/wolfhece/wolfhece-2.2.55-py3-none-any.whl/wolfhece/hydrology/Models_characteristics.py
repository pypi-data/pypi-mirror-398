from . import constant as cst
from . import cst_exchanges as cste
from . import Internal_variables as iv

VHM_VAR = iv.Group_to_Activate(
    name="VHM",
    all_params=[
        iv.Param_to_Activate(
            key="x", group="Internal variables to save", file="soil", 
            all_variables=[
                iv.Internal_Variable(name=f"%xu", file="xu", type_of_var=iv.FRAC_VAR, linked_param=None, id=cste.iv_VHM_xu),
                iv.Internal_Variable(name=f"%xof", file="xof", type_of_var=iv.FRAC_VAR, linked_param=None, id=cste.iv_VHM_xof),
                iv.Internal_Variable(name=f"%xif", file="xif", type_of_var=iv.FRAC_VAR, linked_param=None, id=cste.iv_VHM_xif),
                iv.Internal_Variable(name=f"%xbf", file="xbf", type_of_var=iv.FRAC_VAR, linked_param=None, id=cste.iv_VHM_xbf),
            ]),
        iv.Param_to_Activate(
            key="U", group="Internal variables to save", file="soil",
            all_variables=[
                iv.Internal_Variable(name="U", file="U", type_of_var=iv.IV_VAR, 
                                     linked_param=cste.exchange_parameters_VHM_Umax, id=cste.iv_VHM_U)
            ]),
        iv.Param_to_Activate(
            key=None, group=None, file="",
            all_variables=[
                iv.Internal_Variable(name="q_of", file="of", type_of_var=iv.DEFAULT_VAR, linked_param=None, id=cste.iv_VHM_qof),
                iv.Internal_Variable(name="q_if", file="if", type_of_var=iv.DEFAULT_VAR, linked_param=None, id=cste.iv_VHM_qif),
                iv.Internal_Variable(name="q_bf", file="bf", type_of_var=iv.DEFAULT_VAR, linked_param=None, id=cste.iv_VHM_qbf),
            ])
    ])


UHDIST_LINBF_VAR = iv.Group_to_Activate(
    name="2 layers",
    all_params=[
        iv.Param_to_Activate(
            key="x", group="Internal variables to save", file="soil",
            all_variables=[
                iv.Internal_Variable(name=f"% xif", file="x", type_of_var=iv.FRAC_VAR, linked_param=None, id=cste.iv_2layers_linBF_xif),
            ]),
        iv.Param_to_Activate(
            key="U", group="Internal variables to save", file="soil",
            all_variables=[
                iv.Internal_Variable(name=f"%U", file="U", type_of_var=iv.IV_VAR, 
                                     linked_param=cste.exchange_parameters_Dist_Soil_Umax, id=cste.iv_2layers_linBF_U)
            ]),
        iv.Param_to_Activate(
            key="Reservoir", group="Internal variables to save", file="soil",
            all_variables=[
                iv.Internal_Variable(name=f"% xp", file="xp", type_of_var=iv.FRAC_VAR, linked_param=None, id=cste.iv_2layers_linBF_xp),
                iv.Internal_Variable(name=f"S", file="S", type_of_var=iv.IV_VAR, 
                                     linked_param=cste.exchange_parameters_Dist_RS_Hs, id=cste.iv_2layers_linBF_S),
            ]),
        iv.Param_to_Activate(
            key=None, group=None, file="",
            all_variables=[
                iv.Internal_Variable(name="q_of", file="of", type_of_var=iv.DEFAULT_VAR, linked_param=None, id=cste.iv_2layers_linBF_qof),
                iv.Internal_Variable(name="q_if", file="if", type_of_var=iv.DEFAULT_VAR, linked_param=None, id=cste.iv_2layers_linBF_qif),
            ])
    ]
)


HBV_VAR = iv.Group_to_Activate(
    name="HBV",
    all_params=[
        iv.Param_to_Activate(
            key="U", group="Internal variables to save", file="soil",
            all_variables=[
                iv.Internal_Variable(name="U", file="U", type_of_var=iv.IV_VAR, 
                                     linked_param=cste.exchange_parameters_HBV_FC, id=cste.iv_HBV_U),
            ]),
        iv.Param_to_Activate(
            key="Q out", group="Internal variables to save", file="soil",
            all_variables=[
                iv.Internal_Variable(name="q recharge", file="qrech", type_of_var=iv.OUT_VAR, linked_param=None, id=cste.iv_HBV_qrech),
                iv.Internal_Variable(name="q capillary", file="qcap", type_of_var=iv.OUT_VAR, linked_param=None, id=cste.iv_HBV_soil_qcap),
                iv.Internal_Variable(name="Evapotranspiration", file="etr", type_of_var=iv.OUT_VAR, linked_param=None, id=cste.iv_HBV_etr),
            ]),
        iv.Param_to_Activate(
            key="Su", group="Internal variables to save", file="UZ",
            all_variables=[
                iv.Internal_Variable(name="Su", file="Su", type_of_var=iv.IV_VAR, 
                                     linked_param=cste.exchange_parameters_HBV_SUmax, id=cste.iv_HBV_Su),
            ]),
        iv.Param_to_Activate(
            key="Q out", group="Internal variables to save", file="UZ",
            all_variables=[
                iv.Internal_Variable(name="q_of", file="qr", type_of_var=iv.FINAL_OUT_VAR, linked_param=None, id=cste.iv_HBV_qr),
                iv.Internal_Variable(name="q_if", file="qif", type_of_var=iv.FINAL_OUT_VAR, linked_param=None, id=cste.iv_HBV_qif),
                iv.Internal_Variable(name="q percolation", file="qperc", type_of_var=iv.OUT_VAR, linked_param=None, id=cste.iv_HBV_qperc),
                iv.Internal_Variable(name="q cap UZ", file="qcap", type_of_var=iv.OUT_VAR, linked_param=None, id=cste.iv_HBV_UZ_qcap),
            ]),
        iv.Param_to_Activate(
            key=None, group=None, file="",
            all_variables=[
                iv.Internal_Variable(name="q_bf", file="bf", type_of_var=iv.DEFAULT_VAR, linked_param=None, id=cste.iv_HBV_qbf),
            ])
    ]
)

SACSMA_VAR = iv.Group_to_Activate(
    name="SAC-SMA",
    all_params=[
        iv.Param_to_Activate(
            key="IV", group="Internal variables to save", file="UZ",
            all_variables=[
                iv.Internal_Variable(name="C_UZ_TW", file="Ctw", type_of_var=iv.IV_VAR, 
                                     linked_param=cste.exchange_parameters_SAC_M_UZ_TW, id=cste.iv_SACSMA_CUZTW),
                iv.Internal_Variable(name="C_UZ_FW", file="Cfw", type_of_var=iv.IV_VAR,
                                     linked_param=cste.exchange_parameters_SAC_M_UZ_FW, id=cste.iv_SACSMA_CUZFW),
                iv.Internal_Variable(name="C_Adimp", file="Cadimp", type_of_var=iv.IV_VAR, 
                                     linked_param=None, id=cste.iv_SACSMA_CADIMP),
            ]),
        iv.Param_to_Activate(
            key="Q out", group="Internal variables to save", file="UZ",
            all_variables=[
                iv.Internal_Variable(name="E1", file="e1", type_of_var=iv.OUT_VAR, linked_param=None, id=cste.iv_SACSMA_e1),
                iv.Internal_Variable(name="E2", file="e2", type_of_var=iv.OUT_VAR, linked_param=None, id=cste.iv_SACSMA_e2),
                iv.Internal_Variable(name="E5", file="e5", type_of_var=iv.OUT_VAR, linked_param=None, id=cste.iv_SACSMA_e5),
                iv.Internal_Variable(name="q_ft", file="qft", type_of_var=iv.OUT_VAR, linked_param=None, id=None),
                iv.Internal_Variable(name="q_tf", file="qtf", type_of_var=iv.OUT_VAR, linked_param=None, id=None),
                iv.Internal_Variable(name="q_if", file="qif", type_of_var=iv.OUT_VAR, linked_param=None, id=cste.iv_SACSMA_qqif),
                iv.Internal_Variable(name="q_perc", file="qperc", type_of_var=iv.OUT_VAR, linked_param=None, id=None),
                iv.Internal_Variable(name="q_sr", file="qsr", type_of_var=iv.OUT_VAR, linked_param=None, id=cste.iv_SACSMA_qqsr),
                iv.Internal_Variable(name="q_in Adimp", file="qinadimp", type_of_var=iv.OUT_VAR, linked_param=None, id=None),
                iv.Internal_Variable(name="q_dr Adimp", file="qdr", type_of_var=iv.OUT_VAR, linked_param=None, id=cste.iv_SACSMA_qqdr),
            ]),
        iv.Param_to_Activate(
            key="IV", group="Internal variables to save", file="LZ",
            all_variables=[
                iv.Internal_Variable(name="C_LZ_TW", file="Ctw", type_of_var=iv.IV_VAR, 
                                     linked_param=cste.exchange_parameters_SAC_M_LZ_TW, id=cste.iv_SACSMA_CLZTW),
                iv.Internal_Variable(name="C_LZ_FP", file="Cfp", type_of_var=iv.IV_VAR, 
                                     linked_param=cste.exchange_parameters_SAC_M_LZ_FP, id=cste.iv_SACSMA_CLZFP),
                iv.Internal_Variable(name="C_LZ_FS", file="Cfs", type_of_var=iv.IV_VAR,
                                     linked_param=cste.exchange_parameters_SAC_M_LZ_FS, id=cste.iv_SACSMA_CLZFS),
            ]),
        iv.Param_to_Activate(
            key="Q out", group="Internal variables to save", file="LZ",
            all_variables=[
                iv.Internal_Variable(name="E3", file="e3", type_of_var=iv.OUT_VAR, linked_param=None, id=cste.iv_SACSMA_e3),
                iv.Internal_Variable(name="q_fp", file="qfp", type_of_var=iv.OUT_VAR, linked_param=None, id=None),
                iv.Internal_Variable(name="q_fs", file="qfs", type_of_var=iv.OUT_VAR, linked_param=None, id=None),
                iv.Internal_Variable(name="q_in tw", file="qintw", type_of_var=iv.OUT_VAR, linked_param=None, id=None),
                iv.Internal_Variable(name="q_in fp", file="qinfp", type_of_var=iv.OUT_VAR, linked_param=None, id=None),
                iv.Internal_Variable(name="q_in fs", file="qinfs", type_of_var=iv.OUT_VAR, linked_param=None, id=None),
                iv.Internal_Variable(name="q_out tw", file="qouttw", type_of_var=iv.OUT_VAR, linked_param=None, id=None),
                iv.Internal_Variable(name="q_out fp", file="qoutfp", type_of_var=iv.OUT_VAR, linked_param=None, id=None),
                iv.Internal_Variable(name="q_out fs", file="qoutfs", type_of_var=iv.OUT_VAR, linked_param=None, id=None),
            ]),
        iv.Param_to_Activate(
            key=None, group=None, file="out",
            all_variables=[
                iv.Internal_Variable(name="E_tot", file="Etot", type_of_var=iv.DEFAULT_VAR, linked_param=None, id=cste.iv_SACSMA_etot),
                iv.Internal_Variable(name="Q_of", file="Qof", type_of_var=iv.DEFAULT_VAR, linked_param=None, id=cste.iv_SACSMA_qof),
                iv.Internal_Variable(name="Q_if", file="Qif", type_of_var=iv.DEFAULT_VAR, linked_param=None, id=cste.iv_SACSMA_qif),
                iv.Internal_Variable(name="Q_bf", file="Qbf", type_of_var=iv.DEFAULT_VAR, linked_param=None, id=cste.iv_SACSMA_qbf),
                iv.Internal_Variable(name="Q_subbf", file="Qsubbf", type_of_var=iv.DEFAULT_VAR, linked_param=None, id=cste.iv_SACSMA_qsubbf),
                iv.Internal_Variable(name="Q_surf", file="Qsurf", type_of_var=iv.DEFAULT_VAR, linked_param=None, id=cste.iv_SACSMA_qsurf),
                iv.Internal_Variable(name="Q_base", file="Qbase", type_of_var=iv.DEFAULT_VAR, linked_param=None, id=cste.iv_SACSMA_qbase),
            ])
    ]
)

NAM_VAR = iv.Group_to_Activate(
    name="NAM",
    all_params=[
        iv.Param_to_Activate(
            key="U", group="Internal variables to save", file="SS",
            all_variables=[
                iv.Internal_Variable(name="U", file="U", type_of_var=iv.IV_VAR, 
                                     linked_param=cste.exchange_parameters_NAM_UMAX, id=cste.iv_NAM_U),
            ]),
        iv.Param_to_Activate(
            key="Q out", group="Internal variables to save", file="SS",
            all_variables=[
                iv.Internal_Variable(name="qqof", file="qof", type_of_var=iv.OUT_VAR, linked_param=None, id=None),
                iv.Internal_Variable(name="qqif", file="qif", type_of_var=iv.OUT_VAR, linked_param=None, id=None),
                # iv.Internal_Variable(name="q_infil", file="qinfil", type_of_var=iv.OUT_VAR),
                iv.Internal_Variable(name="Ea", file="ea", type_of_var=iv.OUT_VAR, linked_param=None, id=cste.iv_NAM_ea),
            ]),
        iv.Param_to_Activate(
            key="IV", group="Internal variables to save", file="RZ",
            all_variables=[
                iv.Internal_Variable(name="L", file="L", type_of_var=iv.IV_VAR,
                                     linked_param=cste.exchange_parameters_NAM_LMAX, id=cste.iv_NAM_L),
            ]),
        iv.Param_to_Activate(
            key="Q out", group="Internal variables to save", file="RZ",
            all_variables=[
                iv.Internal_Variable(name="E_rz", file="erz", type_of_var=iv.OUT_VAR, linked_param=None, id=cste.iv_NAM_erz),
                iv.Internal_Variable(name="q_g", file="qg", type_of_var=iv.OUT_VAR, linked_param=None, id=cste.iv_NAM_qg),
            ]),
        iv.Param_to_Activate(
            key=None, group=None, file="",
            all_variables=[
                iv.Internal_Variable(name="q_of", file="OF", type_of_var=iv.DEFAULT_VAR, linked_param=None, id=cste.iv_NAM_qof),
                iv.Internal_Variable(name="q_if", file="IF", type_of_var=iv.DEFAULT_VAR, linked_param=None, id=cste.iv_NAM_qif),
                iv.Internal_Variable(name="q_bf", file="BF", type_of_var=iv.DEFAULT_VAR, linked_param=None, id=cste.iv_NAM_qbf),
            ])
    ]
)


MODELS_VAR:dict[int, iv.Group_to_Activate] = {
    cst.tom_VHM: VHM_VAR,
    cst.tom_2layers_linIF: UHDIST_LINBF_VAR,
    cst.tom_HBV: HBV_VAR,
    cst.tom_SAC_SMA: SACSMA_VAR,
    cst.tom_NAM: NAM_VAR,
    cst.tom_SAC_SMA_LROF: SACSMA_VAR
}

if __name__ == "__main__":
    print(f"VHM keys: {VHM_VAR.get_keys()}")
    print(f"UHDIST_LINBF keys: {UHDIST_LINBF_VAR.get_keys()}")
    print(f"HBV keys: {HBV_VAR.get_keys()}")
    print(f"SACSMA keys: {SACSMA_VAR.get_keys()}")
    print(f"NAM keys: {NAM_VAR.get_keys()}")
    
    print(f"VHM files: {VHM_VAR.get_files_per_keys()}")
    print(f"UHDIST_LINBF files: {UHDIST_LINBF_VAR.get_files_per_keys()}")
    print(f"HBV files: {HBV_VAR.get_files_per_keys()}")
    print(f"SACSMA files: {SACSMA_VAR.get_files_per_keys()}")
    print(f"NAM files: {NAM_VAR.get_files_per_keys()}")
