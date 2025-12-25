"""
Fixed-width record layouts for RRC Well Bore data.
"""

# Mapping segment keys to human-readable names
SEGMENT_MAP = {
    '01': 'WBROOT',
    '02': 'WBCOMPL',
    '03': 'WBDATE',
    '04': 'WBRMKS',
    '05': 'WBTUBE',
    '06': 'WBCASE',
    '07': 'WBPERF',
    '08': 'WBLINE',
    '09': 'WBFORM',
    '10': 'WBSQEZE',
    '11': 'WBFRESH',
    '12': 'WBOLDLOC',
    '13': 'WBNEWLOC',
    '14': 'WBPLUG',
    '15': 'WBPLRMKS',
    '16': 'WBPLREC',
    '17': 'WBPLCASE',
    '18': 'WBPLPERF',
    '19': 'WBPLNAME',
    '20': 'WBDRILL',
    '21': 'WBWELLID',
    '22': 'WB14B2',
    '23': 'WBH15',
    '24': 'WBH15RMK',
    '25': 'WBSB126',
    '26': 'WBDASTAT',
    '27': 'WBW3C',
    '28': 'WB14B2RM',
}

# Layout definitions: { 'segment_key': [ (start_1_based, length, type, field_name), ... ] }
LAYOUTS = {
    '01': [
        (3, 3, 'int', 'api_county_code'),
        (6, 5, 'int', 'api_unique_number'),
        (11, 2, 'int', 'next_avail_suffix'),
        (13, 2, 'int', 'next_avail_hole_chge_nbr'),
        (15, 2, 'int', 'field_district'),
        (17, 3, 'int', 'res_cnty_code'),
        (20, 1, 'str', 'orig_compl_cc_flag'),
        (21, 2, 'int', 'orig_compl_cent'),
        (23, 2, 'int', 'orig_compl_yy'),
        (25, 2, 'int', 'orig_compl_mm'),
        (27, 2, 'int', 'orig_compl_dd'),
        (29, 5, 'int', 'total_depth'),
        (34, 5, 'int', 'valid_fluid_level'),
        (39, 2, 'int', 'cert_revoked_cc'),
        (41, 2, 'int', 'cert_revoked_yy'),
        (43, 2, 'int', 'cert_revoked_mm'),
        (45, 2, 'int', 'cert_revoked_dd'),
        (47, 2, 'int', 'cert_denial_cc'),
        (49, 2, 'int', 'cert_denial_yy'),
        (51, 2, 'int', 'cert_denial_mm'),
        (53, 2, 'int', 'cert_denial_dd'),
        (55, 1, 'str', 'denial_reason_flag'),
        (56, 1, 'str', 'error_api_assign_code'),
        (57, 8, 'int', 'refer_correct_api_nbr'),
        (65, 8, 'int', 'dummy_api_number'),
        (73, 8, 'int', 'date_dummy_replaced'),
        (81, 6, 'int', 'newest_drl_pmt_nbr'),
        (87, 1, 'str', 'cancel_expire_code'),
        (89, 1, 'str', 'except_13a_flag'),
        (90, 1, 'str', 'fresh_water_flag'),
        (91, 1, 'str', 'plug_flag'),
        (92, 8, 'int', 'previous_api_nbr'),
        (100, 1, 'str', 'completion_data_ind'),
        (101, 1, 'int', 'hist_date_source_flag'),
        (103, 2, 'int', 'ex14b2_count'),
        (105, 1, 'str', 'designation_hb_1975_flag'),
        (106, 2, 'int', 'designation_effec_cc'),
        (108, 2, 'int', 'designation_effec_yy'),
        (110, 2, 'int', 'designation_effec_mm'),
        (112, 2, 'int', 'designation_revised_cc'),
        (114, 2, 'int', 'designation_revised_yy'),
        (116, 2, 'int', 'designation_revised_mm'),
        (118, 2, 'int', 'designation_letter_cc'),
        (120, 2, 'int', 'designation_letter_yy'),
        (122, 2, 'int', 'designation_letter_mm'),
        (124, 2, 'int', 'designation_letter_dd'),
        (126, 2, 'int', 'certification_effec_cc'),
        (128, 2, 'int', 'certification_effec_yy'),
        (130, 2, 'int', 'certification_effec_mm'),
        (132, 1, 'str', 'water_land_code'),
        (133, 6, 'int', 'total_bonded_depth'),
        (139, 7, 'int', 'override_est_plug_cost'),
        (146, 6, 'int', 'shut_in_date'),
        (152, 6, 'int', 'override_bonded_depth'),
        (158, 1, 'str', 'subj_to_14b2_flag'),
        (159, 1, 'str', 'pend_removal_14b2_flag'),
        (160, 1, 'str', 'orphan_well_hold_flag'),
    ],
    '02': [
        # Oil Key Fields
        (3, 1, 'str', 'wb_oil_code'),
        (4, 2, 'int', 'wb_oil_dist'),
        (6, 5, 'int', 'wb_oil_lse_nbr'),
        (11, 6, 'str', 'wb_oil_well_nbr'),
        # Gas Key Fields (Redefines)
        (3, 1, 'str', 'wb_gas_code'),
        (4, 6, 'int', 'wb_gas_rrc_id'),
        # Gas Filler at 10, 7 skipped
        (17, 2, 'int', 'wb_gas_dist'),
        (19, 6, 'str', 'wb_gas_well_no'),
        (25, 1, 'str', 'wb_multi_well_rec_nbr'),
        (26, 2, 'int', 'wb_api_suffix'),
        (46, 1, 'str', 'wb_active_inactive_code'),
        (87, 1, 'str', 'wb_dwn_hole_commingle_code'),
        (122, 1, 'str', 'wb_created_from_pi_flag'),
        (123, 7, 'int', 'wb_rule_37_nbr'),
        (156, 1, 'str', 'wb_p_15_flag'),
        (157, 1, 'str', 'wb_p_12_flag'),
        (158, 8, 'int', 'wb_plug_date_pointer'),
    ],
    '03': [
        (3, 8, 'int', 'wb_file_key'),
        (11, 8, 'int', 'wb_file_date'),
        (27, 1, 'str', 'wb_except_rule_11_flag'),
        (28, 1, 'str', 'wb_cement_affidavit_flag'),
        (29, 1, 'str', 'wb_g_5_flag'),
        (30, 1, 'str', 'wb_w_12_flag'),
        (31, 1, 'str', 'wb_dir_survey_flag'),
        (32, 8, 'int', 'wb_w2_g1_date'),
        (40, 2, 'int', 'wb_compl_century'),
        (42, 2, 'int', 'wb_compl_year'),
        (44, 2, 'int', 'wb_compl_month'),
        (46, 2, 'int', 'wb_compl_day'),
        (48, 8, 'int', 'wb_drl_compl_date'),
        (56, 5, 'int', 'wb_plugb_depth1'),
        (61, 5, 'int', 'wb_plugb_depth2'),
        (66, 6, 'str', 'wb_water_injection_nbr'),
        (72, 5, 'int', 'wb_salt_wtr_nbr'),
        (85, 1, 'str', 'wb_remarks_ind'),
        (86, 4, 'int', 'wb_elevation'),
        (90, 2, 'str', 'wb_elevation_code'),
        (92, 8, 'int', 'wb_log_file_rba'),
        (100, 10, 'str', 'wb_docket_nbr'),
        (110, 1, 'str', 'wb_psa_well_flag'),
        (111, 1, 'str', 'wb_allocation_well_flag'),
    ],
    '04': [
        (3, 3, 'int', 'wb_rmk_lne_cnt'),
        (6, 1, 'str', 'wb_rmk_type_code'),
        (7, 70, 'str', 'wb_remarks'),
    ],
    '05': [
        (3, 3, 'int', 'wb_segment_counter'),
        (6, 2, 'int', 'wb_tubing_inches'),
        (8, 2, 'int', 'wb_fr_numerator'),
        (10, 2, 'int', 'wb_fr_denominator'),
        (12, 5, 'int', 'wb_depth_set'),
        (17, 5, 'int', 'wb_packer_set'),
    ],
    '06': [
        (3, 3, 'int', 'wb_casing_count'),
        (6, 2, 'int', 'wb_cas_inch'),
        (8, 2, 'int', 'wb_cas_frac_num'),
        (10, 2, 'int', 'wb_cas_frac_denom'),
        # Weight table redefines, storing both occurrences flat
        (12, 3, 'int', 'wb_wgt_whole_1'),
        (15, 1, 'int', 'wb_wgt_tenths_1'),
        (16, 3, 'int', 'wb_wgt_whole_2'),
        (19, 1, 'int', 'wb_wgt_tenths_2'),
        (20, 5, 'int', 'wb_casing_depth_set'),
        (25, 5, 'int', 'wb_mlti_stg_tool_dpth'),
        (30, 5, 'int', 'wb_amount_of_cement'),
        (35, 1, 'str', 'wb_cement_measurement'),
        (36, 2, 'int', 'wb_hole_inch'),
        (38, 2, 'int', 'wb_hole_frac_num'),
        (40, 2, 'int', 'wb_hole_frac_denom'),
        (43, 7, 'str', 'wb_top_of_cement_casing'),
        (50, 5, 'int', 'wb_amount_casing_left'),
    ],
    '07': [
        (3, 3, 'int', 'wb_perf_count'),
        (6, 5, 'int', 'wb_from_perf'),
        (11, 5, 'int', 'wb_to_perf'),
        (16, 2, 'str', 'wb_open_hole_code'),
    ],
    '08': [
        (3, 3, 'int', 'wb_line_count'),
        (6, 2, 'int', 'wb_lin_inch'),
        (8, 2, 'int', 'wb_lin_frac_num'),
        (10, 2, 'int', 'wb_lin_frac_denom'),
        (12, 5, 'int', 'wb_sacks_of_cement'),
        (17, 5, 'int', 'wb_top_of_liner'),
        (22, 5, 'int', 'wb_bottom_of_liner'),
    ],
    '09': [
        (3, 3, 'int', 'wb_formation_cntr'),
        (6, 32, 'str', 'wb_formation_name'),
        (38, 5, 'int', 'wb_formation_depth'),
    ],
    '10': [
        (3, 3, 'int', 'wb_squeeze_cntr'),
        (6, 5, 'int', 'wb_squeeze_upper_depth'),
        (11, 5, 'int', 'wb_squeeze_lower_depth'),
        (16, 50, 'str', 'wb_squeeze_kind_amount'),
    ],
    '11': [
        (3, 3, 'int', 'wb_fresh_water_cntr'),
        (6, 8, 'int', 'wb_twdb_date'),
        (14, 1, 'str', 'wb_surface_casing_deter_code'),
        (15, 4, 'int', 'wb_uqwp_from'),
        (19, 4, 'int', 'wb_uqwp_to'),
    ],
    '12': [
        (3, 32, 'str', 'wb_lease_name'),
        (35, 52, 'str', 'wb_sec_blk_survey_loc'),
        (87, 4, 'int', 'wb_well_loc_miles'),
        (91, 6, 'str', 'wb_well_loc_direction'),
        (97, 13, 'str', 'wb_well_loc_nearest_town'),
        (138, 28, 'str', 'wb_dist_from_survey_lines'),
        (166, 28, 'str', 'wb_dist_direct_near_well'),
    ],
    '13': [
        (3, 3, 'int', 'wb_loc_county'),
        (6, 6, 'str', 'wb_abstract'),
        (12, 55, 'str', 'wb_survey'),
        (67, 10, 'str', 'wb_block_number'),
        (77, 8, 'str', 'wb_section'),
        (85, 4, 'str', 'wb_alt_section'),
        (89, 6, 'str', 'wb_alt_abstract'),
        (95, 6, 'int', 'wb_feet_from_sur_sect_1'),
        (101, 13, 'str', 'wb_direc_from_sur_sect_1'),
        (114, 6, 'int', 'wb_feet_from_sur_sect_2'),
        (120, 13, 'str', 'wb_direc_from_sur_sect_2'),
        (133, 10, 'int', 'wb_wgs84_latitude'),
        (143, 10, 'int', 'wb_wgs84_longitude'),
        (158, 2, 'int', 'wb_plane_zone'),
        (160, 10, 'int', 'wb_plane_coordinate_east'),
        (170, 10, 'int', 'wb_plane_coordinate_north'),
        (178, 1, 'str', 'wb_verification_flag'),
    ],
    '14': [
        (3, 8, 'int', 'wb_date_w3_filed'),
        (11, 8, 'int', 'wb_date_well_bore_plugged'),
        (19, 5, 'int', 'wb_plug_total_depth'),
        (24, 32, 'str', 'wb_plug_cement_comp'),
        (56, 1, 'str', 'wb_plug_mud_filled'),
        (57, 12, 'str', 'wb_plug_mud_applied'),
        (69, 3, 'int', 'wb_plug_mud_weight'),
        (76, 8, 'int', 'wb_plug_dril_perm_date'),
        (84, 6, 'int', 'wb_plug_dril_perm_no'),
        (90, 8, 'int', 'wb_plug_dril_comp_date'),
        (98, 1, 'str', 'wb_plug_log_attached'),
        (99, 32, 'str', 'wb_plug_log_released_to'),
        (131, 1, 'str', 'wb_plug_type_log'),
        (132, 5, 'int', 'wb_plug_fresh_water_depth'),
        # Flattened WB-PLUG-UWQP (4 times)
        (137, 5, 'int', 'wb_plug_from_uwqp_1'),
        (142, 5, 'int', 'wb_plug_to_uwqp_1'),
        (147, 5, 'int', 'wb_plug_from_uwqp_2'),
        (152, 5, 'int', 'wb_plug_to_uwqp_2'),
        (157, 5, 'int', 'wb_plug_from_uwqp_3'),
        (162, 5, 'int', 'wb_plug_to_uwqp_3'),
        (167, 5, 'int', 'wb_plug_from_uwqp_4'),
        (172, 5, 'int', 'wb_plug_to_uwqp_4'),
        (177, 1, 'str', 'wb_plug_material_left'),
        # Oil/Gas Key Redefines (Oil is default view)
        (178, 1, 'str', 'wb_plug_oil_code'),
        (179, 2, 'int', 'wb_plug_oil_dist'),
        (181, 5, 'int', 'wb_plug_oil_lse_nbr'),
        (186, 6, 'str', 'wb_plug_oil_well_nbr'),
        # Gas Key Redefines mapped separately? 
        # Standard practice: map overlaps if needed.
        # Gas key: Code(178,1), RRC_ID(179, 6), Filler(185, 7)
        # We'll stick to Oil mapping + raw fields, user can interpret based on type.
        # But wait, 179 for Gas is 6 bytes (RRC ID). 
        # Let's map gas fields too for completeness, referencing same start bytes.
        (178, 1, 'str', 'wb_plug_gas_code'), 
        (179, 6, 'int', 'wb_plug_gas_rrc_id'),
        
        # Back to common
        (192, 2, 'int', 'wb_plug_gas_dist'),
        (194, 6, 'str', 'wb_plug_gas_well_no'),
        (200, 1, 'str', 'wb_plug_type_well'),
        (201, 1, 'str', 'wb_plug_multi_compl_flag'),
        (202, 1, 'str', 'wb_plug_cem_aff'),
        (203, 1, 'str', 'wb_plug_13a'),
        (204, 8, 'int', 'wb_plug_log_released_date'),
        (212, 8, 'int', 'wb_plug_log_file_rba'),
        (220, 7, 'int', 'wb_state_funded_plug_number'),
    ],
    '15': [
        (3, 3, 'int', 'wb_plug_rmk_lne_cnt'),
        (6, 1, 'str', 'wb_plug_rmk_type_code'),
        (7, 70, 'str', 'wb_plug_remarks'),
    ],
    '16': [
        (3, 3, 'int', 'wb_plug_number'),
        (6, 5, 'int', 'wb_nbr_of_cement_sacks'),
        (11, 5, 'int', 'wb_meas_top_of_plug'),
        (16, 5, 'int', 'wb_bottom_tube_pipe_depth'),
        (21, 5, 'int', 'wb_plug_calc_top'),
        (26, 6, 'str', 'wb_plug_type_cement'),
    ],
    '17': [
        (3, 6, 'int', 'wb_plg_cas_counter'),
        (9, 2, 'int', 'wb_plug_cas_inch'),
        (11, 2, 'int', 'wb_plug_cas_frac_num'),
        (13, 2, 'int', 'wb_plug_cas_frac_denom'),
        (15, 3, 'int', 'wb_plug_wgt_whole'),
        (18, 1, 'int', 'wb_plug_wgt_tenths'),
        (19, 5, 'int', 'wb_plug_amt_put'),
        (24, 5, 'int', 'wb_plug_amt_left'),
        (29, 2, 'int', 'wb_plug_hole_inch'),
        (31, 2, 'int', 'wb_plug_hole_frac_num'),
        (33, 2, 'int', 'wb_plug_hole_frac_denom'),
    ],
    '18': [
        (3, 3, 'int', 'wb_plug_perf_counter'),
        (6, 5, 'int', 'wb_plug_from_perf'),
        (11, 5, 'int', 'wb_plug_to_perf'),
        (16, 1, 'str', 'wb_plug_open_hole_indicator'),
    ],
    '19': [
        (3, 8, 'int', 'wb_plug_field_no'),
        (11, 32, 'str', 'wb_plug_field_name'),
        (43, 6, 'str', 'wb_plug_oper_no'),
        (49, 32, 'str', 'wb_plug_oper_name'),
        (81, 32, 'str', 'wb_plug_lease_name'),
    ],
    '20': [
        (3, 6, 'int', 'wb_permit_number'),
    ],
    '21': [
        # Oil Info
        (3, 1, 'str', 'wb_oil_info_oil'),
        (4, 2, 'int', 'wb_oil_info_district'),
        (6, 5, 'int', 'wb_oil_info_lease_number'),
        (11, 6, 'str', 'wb_oil_info_well_number'),
        # Gas Info redefines
        (3, 1, 'str', 'wb_gas_info_gas'),
        (4, 6, 'int', 'wb_gas_info_rrcid'),
    ],
    '22': [
        # Oil Keys
        (3, 1, 'str', 'wb14b2_oil_code'), # 'O'
        (4, 2, 'int', 'wb14b2_oil_district'),
        (6, 5, 'int', 'wb14b2_oil_lease_number'),
        (11, 6, 'str', 'wb14b2_oil_well_number'),
        # Gas Keys redefines
        (3, 1, 'str', 'wb14b2_gas_code'), # 'G'
        (4, 6, 'int', 'wb14b2_gas_rrc_id'),
        # Data
        (17, 6, 'int', 'wb14b2_application_number'),
        (23, 2, 'int', 'wb14b2_gas_district'), # Distinct from oil district in pos 4? Yes, spec says pos 23.
        (25, 1, 'str', 'wb14b2_ext_status_flag'),
        (26, 1, 'str', 'wb14b2_ext_cancelled_reason'),
        # Dates (CCYYMMDD = 8 chars)
        (27, 8, 'int', 'wb14b2_ext_approved_date'),
        (35, 8, 'int', 'wb14b2_ext_exp_date'),
        (43, 8, 'int', 'wb14b2_ext_denied_date'), # pos 43? spec image: 43 (CENT), 45 (YEAR), etc. Yes 43 start.
        (51, 8, 'int', 'wb14b2_ext_hist_date'),
        # Violations
        (59, 1, 'str', 'wb14b2_mech_integ_viol_flag'),
        (60, 1, 'str', 'wb14b2_plug_order_sf_hold_flag'),
        (61, 1, 'str', 'wb14b2_pollution_viol_flag'),
        (62, 1, 'str', 'wb14b2_field_ops_hold_flag'),
        (63, 1, 'str', 'wb14b2_h15_problem_flag'),
        (64, 1, 'str', 'wb14b2_h15_not_filed_flag'),
        (65, 1, 'str', 'wb14b2_oper_delq_flag'),
        (66, 1, 'str', 'wb14b2_district_hold_sfp_flag'),
        (67, 1, 'str', 'wb14b2_dist_sf_clean_up_flag'),
        (68, 1, 'str', 'wb14b2_dist_state_plug_flag'),
        (69, 1, 'str', 'wb14b2_good_faith_viol_flag'),
        (70, 1, 'str', 'wb14b2_well_other_viol_flag'),
        (71, 1, 'str', 'wb14b2_w3c_surf_eqp_viol_flag'),
        (72, 1, 'str', 'wb14b2_w3x_viol_flag'),
        # HB2259 Options (80-83)
        (80, 1, 'str', 'wb14b2_hb2259_w3x_pub_ent'),
        (81, 1, 'str', 'wb14b2_hb2259_w3x_10pct'),
        (82, 1, 'str', 'wb14b2_hb2259_w3x_bonding'),
        (83, 1, 'str', 'wb14b2_hb2259_w3x_h13_eor'),
        # Rejections
        (84, 1, 'str', 'wb14b2_hb2259_eor_rejected'),
        (85, 1, 'str', 'wb14b2_hb2259_w3x_mit'), # NOTE: Image says 'MIT', 'MIT-REJECTED' R. Pos 85 is W3X-MIT-REJECTED?
        # Image: 
        # 07 WB14B2-HB2259-W3X-MIT VALUE SPACES PIC X(01). 85
        # 88 WB14B2-HB2259-MIT-REJECTED VALUE 'R'.
        # So field is 'W3X-MIT'.
        (86, 1, 'str', 'wb14b2_hb2259_w3x_escrow_rejected'), # Field is W3X-ESCROW (86), 88 REJECTED 'R'
        (87, 8, 'int', 'wb14b2_w3x_filing_key'),
        (95, 8, 'int', 'wb14b2_w3x_aop_received_date'),
        (103, 8, 'int', 'wb14b2_w3x_aop_fee_rcvd_date'),
        (111, 8, 'int', 'wb14b2_w3x_h15_fee_rcvd_date'),
        (119, 7, 'int', 'wb14b2_w3x_escrow_funds'), # 9(05)V99 -> 7 digits implied decimal
        (126, 1, 'str', 'wb14b2_60_day_letter_sent_flag'),
        (127, 1, 'str', 'wb14b2_w1x_36_needs_bond_flag'),
        (128, 1, 'str', 'wb14b2_w1x_36_type_coverage'),
        (129, 9, 'int', 'wb14b2_w1x_36_amt_filed'),
        (138, 5, 'int', 'wb14b2_w1x_36_surety'),
        (143, 8, 'int', 'wb14b2_w1x_36_exp_date'),
        (151, 20, 'str', 'wb14b2_w1x_36_bond_number'),
    ],
    '23': [
        (3, 8, 'int', 'wb_h15_date_key'),
        (11, 1, 'str', 'wb_h15_status'),
        (12, 6, 'str', 'wb_h15_operator'),
        (18, 6, 'int', 'wb_h15_next_test_due_date'), # CCYYMM
        (24, 2, 'int', 'wb_h15_district'),
        (26, 8, 'int', 'wb_h15_field'),
        (34, 1, 'str', 'wb_h15_hist_wellbore_flag'),
        (35, 6, 'int', 'wb_h15_hist_well_ccyymm'), # CCYYMM
        (43, 1, 'str', 'wb_h15_w1x_well'),
        (44, 1, 'str', 'wb_h15_oil_gas_code'),
        (45, 5, 'int', 'wb_h15_lease_nbr'),
        (50, 6, 'str', 'wb_h15_well_nbr'),
        (56, 6, 'int', 'wb_h15_gasid_nbr'),
        (62, 8, 'int', 'wb_h15_test_date'), # CCYYMMDD
        (70, 6, 'int', 'wb_h15_base_usable_water'),
        (76, 1, 'str', 'wb_h15_type_test_flag'),
        (77, 6, 'int', 'wb_h15_top_of_fluid'),
        (83, 1, 'str', 'wb_h15_fluid_test_flag'),
        (84, 1, 'str', 'wb_h15_mech_integ_test_flag'),
        (85, 1, 'str', 'wb_h15_mech_test_reason_flag'),
        (86, 2, 'int', 'wb_h15_alternate_test_period'),
        (88, 20, 'str', 'wb_h15_other_mit_test_type'),
        (108, 8, 'int', 'wb_h15_status_date'), # CCYYMMDD
        (116, 1, 'str', 'wb_h15_no_date_well_flag'),
        (117, 1, 'str', 'wb_h15_record_from_edi_flag'),
        (118, 8, 'int', 'wb_h15_keyed_date'),
        (126, 8, 'int', 'wb_h15_changed_date'),
        (134, 1, 'str', 'wb_h15_previous_status'),
        (135, 1, 'str', 'wb_h15_uic_test_flag'),
        (136, 1, 'str', 'wb_h15_2yrs_approved_flag'),
        (137, 1, 'str', 'wb_h15_mail_hold_flag'),
        (138, 1, 'str', 'wb_h15_10yr_inactive_flag'),
        (139, 1, 'str', 'wb_h15_w3x_well_flag'),
    ],
    '24': [
        (3, 3, 'int', 'wb_h15_remark_key'),
        (6, 70, 'str', 'wb_h15_remark_text'),
    ],
    '25': [
        (3, 1, 'str', 'wb_sb126_designation_flag'),
        (4, 6, 'int', 'wb_sb126_desig_effective_date'), # CCYYMM
        (10, 6, 'int', 'wb_sb126_desig_revised_date'), # CCYYMM
        (16, 8, 'int', 'wb_sb126_desig_letter_date'), # CCYYMMDD
        (24, 6, 'int', 'wb_sb126_cert_effect_date'), # CCYYMM
        (30, 8, 'int', 'wb_sb126_cert_revoked_date'), # CCYYMMDD
        (38, 8, 'int', 'wb_sb126_cert_denial_date'), # CCYYMMDD
        (46, 1, 'str', 'wb_sb126_denial_reason_flag'),
    ],
    '26': [
        (3, 7, 'int', 'wb_dastat_stat_num'),
        (10, 2, 'int', 'wb_dastat_uniq_num'),
        (12, 1, 'str', 'wb_dastat_deleted_flag'),
    ],
    '27': [
        (3, 1, 'str', 'wb_w3c_1yr_flag'),
        (4, 8, 'int', 'wb_w3c_1yr_filed_date'),
        (12, 6, 'int', 'wb_w3c_1yr_filing_oper'),
        (18, 1, 'str', 'wb_w3c_5yr_flag'),
        (19, 8, 'int', 'wb_w3c_5yr_filed_date'),
        (27, 6, 'int', 'wb_w3c_5yr_filing_oper'),
        (33, 1, 'str', 'wb_w3c_10yr_flag'),
        (34, 8, 'int', 'wb_w3c_10yr_filed_date'),
        (42, 6, 'int', 'wb_w3c_10yr_filing_oper'),
        (48, 8, 'int', 'wb_w3c_14b2_removal_date'),
        (56, 1, 'str', 'wb_w3c_extension_flag'),
        (57, 4, 'int', 'wb_w3c_extension_year'), # PIC 9(04) 57
        (61, 2, 'int', 'wb_w3c_extension_month'), # PIC 9(02) 61
        (63, 2, 'int', 'wb_w3c_extension_day'), # PIC 9(02) 63
        # I'll combine these into a date field using custom logic if needed, but for now stick to raw fields or use date type if I can composite them.
        # Actually, previous segments used CCYYMMDD int field. Here it is split YYYY MM DD. 
        # I will map them as separate fields for now as per layout, to be safe. 
        # Wait, usually I map dates as one field if contiguous. Here they are contiguous: 4+2+2 = 8.
        # So I can map (57, 8, 'int', 'wb_w3c_extension_date').
        (65, 1, 'str', 'wb_w3c_5yr_flag_previous'),
        (66, 1, 'str', 'wb_w3c_10yr_flag_previous'),
    ],
    '28': [
        (3, 3, 'int', 'wb_14b2_rmk_lne_cnt'),
        (6, 8, 'int', 'wb_14b2_rmk_date'),
        (14, 8, 'str', 'wb_14b2_rmk_userid'),
        (22, 66, 'str', 'wb_14b2_remarks'),
    ]
}

# Placeholder for lookups used when convert_values=True
# Structure: { 'segment_name': { 'field_name': { 'code': 'description' } } }
LOOKUPS = {
    'WBROOT': {
        'orig_compl_cc_flag': {
            '0': 'ZEROS',
            '1': '19TH CENTURY',
            '2': '20TH CENTURY',
            '3': '21ST CENTURY',
        },
        'denial_reason_flag': {
            'A': 'AUTOMATIC',
            'M': 'MANUAL',
            ' ': 'NONE',  # Assuming space means none/not denied
            '0': 'NONE',
        },
        'except_13a_flag': {
            'Y': 'FILED',
            'N': 'NOT FILED',
        },
        'fresh_water_flag': {
            'Y': 'FRESH WATER',
            'N': 'NOT FRESH WATER',
        },
        'plug_flag': {
            'Y': 'PLUGGED',
            'N': 'NOT PLUGGED',
        },
        'completion_data_ind': {
            'Y': 'ON FILE',
            'N': 'NOT ON FILE',
        },
        'hist_date_source_flag': {
            '1': 'P-I TAPE',
            '2': 'OTHER',
            '0': 'UNKNOWN',
        },
        'designation_hb_1975_flag': {
            'A': 'AUTOMATIC',
            'M': 'MANUAL',
            ' ': 'NOT CERTIFIED',
            '0': 'NOT CERTIFIED',
        },
        'water_land_code': {
            'I': 'INLAND WATERWAY',
            'B': 'BAY/ESTUARY',
            'O': 'OFFSHORE',
            'L': 'LAND',
        },
        'subj_to_14b2_flag': {
            'Y': 'SUBJECT TO 14B2',
            'N': 'NOT SUBJECT',
        },
        'pend_removal_14b2_flag': {
            'Y': 'PENDING REMOVAL',
            'N': 'NOT PENDING',
        },
        'orphan_well_hold_flag': {
            'Y': 'ORPHAN HOLD',
            'N': 'NO HOLD',
        }
    },
    'WBCOMPL': {
        'wb_created_from_pi_flag': {'Y': 'CREATED FROM PI', 'N': 'NOT CREATED FROM PI'},
        'wb_p_15_flag': {'Y': 'FILED', 'N': 'NOT FILED'},
        'wb_p_12_flag': {'Y': 'FILED', 'N': 'NOT FILED'},
    },
    'WBDATE': {
        'wb_except_rule_11_flag': {'Y': 'FILED', 'N': 'NOT FILED'},
        'wb_cement_affidavit_flag': {
            'N': 'NOT FILED', 'Y': 'FILED', 'B': 'NOT FOUND', 'A': 'AVAIL', 'R': 'NOT REQ'
        },
        'wb_g_5_flag': {'Y': 'FILED', 'N': 'NOT FILED'},
        'wb_w_12_flag': {'Y': 'FILED', 'N': 'NOT FILED'},
        'wb_dir_survey_flag': {'Y': 'FILED', 'N': 'NOT FILED'},
        'wb_remarks_ind': {'Y': 'ON FILE', 'N': 'NOT ON FILE'},
        'wb_elevation_code': {
            'GL': 'GROUND LEVEL', 'DF': 'DERRICK FLOOR', 'KB': 'KELLY BUSHING',
            'RT': 'ROTARY TABLE', 'GR': 'GROUND'
        },
        'wb_psa_well_flag': {'Y': 'PSA WELL', 'N': 'NOT PSA', ' ': 'NOT PSA'},
        'wb_allocation_well_flag': {'Y': 'ALLOCATION WELL', 'N': 'NOT ALLOCATION', ' ': 'NOT ALLOCATION'},
    },
    'WBCASE': {
        'wb_cement_measurement': {
            'S': 'SACKS',
            'Y': 'CUBIC YARDS',
            'F': 'CUBIC FEET',
        }
    },
    'WBPERF': {
        'wb_open_hole_code': {
            'OH': 'OPEN HOLE',
        }
    },
    'WBFRESH': {
        'wb_surface_casing_deter_code': {
            'Y': 'FIELD RULES IN EFFECT',
            'N': 'NO FIELD RULES',
        }
    },
    'WBNEWLOC': {
        'wb_verification_flag': {
            'N': 'NOT VERIFIED',
            'Y': 'VERIFIED',
            'C': 'VERIFIED - CHANGE',
        }
    },
    'WBPLUG': {
        'wb_plug_mud_filled': {'Y': 'YES', 'N': 'NO'},
        'wb_plug_log_attached': {'Y': 'YES', 'N': 'NO'},
        'wb_plug_type_log': {
            'D': 'DRILLERS',
            'E': 'ELECTRIC',
            'R': 'RADIOACTIVITY',
            'A': 'ACOUSTICAL-SONIC',
            'F': 'DRIL-AND-ELEC',
            'G': 'ELEC-AND-RADIO',
            'H': 'RADIO-AND-ACOUS',
            'I': 'DRIL-AND-RADIO',
            'J': 'ELEC-AND-ACOUS',
            'K': 'DRIL-AND-ACOUS',
            'L': 'DRIL-ELEC-RADIO',
            'M': 'ELEC-RADIO-ACOUS',
            'N': 'DRIL-ELEC-ACOUS',
            'O': 'DRIL-RADIO-ACOUS',
            'P': 'DRIL-ELEC-RADIO-ACOUS',
        },
        'wb_plug_material_left': {'Y': 'YES', 'N': 'NO'},
        'wb_plug_type_well': {
            'O': 'OIL',
            'G': 'GAS',
            'D': 'DRY HOLE',
            'S': 'SERVICE',
        },
        'wb_plug_multi_compl_flag': {'Y': 'YES', 'N': 'NO'},
        'wb_plug_cem_aff': {'Y': 'FILED', 'N': 'NOT FILED'},
        'wb_plug_13a': {'Y': 'FILED', 'N': 'NOT FILED'},
    },
    'WBPLPERF': {
        'wb_plug_open_hole_indicator': {'Y': 'YES', 'N': 'NO'},
    },
    'WB14B2': {
        'wb14b2_ext_status_flag': {
            'A': 'APPROVED',
            'C': 'CANCELLED',
            'D': 'DENIED',
            'E': 'EXPIRED'
        },
        'wb14b2_ext_cancelled_reason': {
            'T': 'INJECTION WELL',
            'P': 'PRODUCING WELL',
            'G': 'PLUGGED WELL',
            'S': 'SERVICE WELL',
            'O': 'OTHER'
        },
        'wb14b2_mech_integ_viol_flag': {'H': 'MECHANICAL INTEGRITY VIOLATION'},
        'wb14b2_plug_order_sf_hold_flag': {'E': 'PLUG ORDER SF HOLD'},
        'wb14b2_pollution_viol_flag': {'P': 'POLLUTION VIOLATION'},
        'wb14b2_field_ops_hold_flag': {'F': 'FIELD OPS HOLD'},
        'wb14b2_h15_problem_flag': {'V': 'H15 PROBLEM'},
        'wb14b2_h15_not_filed_flag': {'X': 'H15 NOT FILED'},
        'wb14b2_oper_delq_flag': {'O': 'OPERATOR DELINQUENT'},
        'wb14b2_district_hold_sfp_flag': {'T': 'DISTRICT HOLD SFP'},
        'wb14b2_dist_sf_clean_up_flag': {'M': 'DISTRICT SF CLEAN UP'},
        'wb14b2_dist_state_plug_flag': {'K': 'DISTRICT STATE PLUG'},
        'wb14b2_good_faith_viol_flag': {'R': 'GOOD FAITH VIOLATION'},
        'wb14b2_well_other_viol_flag': {'Q': 'WELL OTHER VIOLATION'},
        'wb14b2_w3c_surf_eqp_viol_flag': {'S': 'W3C SURF EQUIP VIOLATION'},
        'wb14b2_w3x_viol_flag': {'W': 'W3X VIOLATION'},
        'wb14b2_hb2259_eor_rejected': {'R': 'REJECTED'},
        'wb14b2_hb2259_w3x_mit': {'R': 'REJECTED'}, # Mapped from field name using corrected lookup
        'wb14b2_hb2259_w3x_escrow_rejected': {'R': 'REJECTED'},
        'wb14b2_60_day_letter_sent_flag': {'Y': 'YES'},
        'wb14b2_w1x_36_needs_bond_flag': {'Y': 'YES'},
        'wb14b2_w1x_36_type_coverage': {'B': 'BOND', 'L': 'LETTER OF CREDIT'},
    },
    'WBH15': {
        'wb_h15_status': {
            'A': 'APPROVED',
            'C': 'COMPLIANT',
            'D': 'DELINQUENT',
            'N': 'NOT APPROVED',
            'P': 'APPROVAL PENDING',
            'W': 'W3A EXTENSION',
            'U': 'UIC',
            'E': 'NO TEST PROJ EXT', 
            'X': 'W1X DENIED'
        },
        'wb_h15_hist_wellbore_flag': {'D': 'DRILLING PERMIT', 'C': 'EARLIEST COMPLETION'},
        'wb_h15_oil_gas_code': {'G': 'GAS WELL', 'O': 'OIL WELL'},
        'wb_h15_type_test_flag': {'F': 'FLUID LEVEL TEST', 'M': 'MECHANICAL INTEGRITY TEST'},
        'wb_h15_fluid_test_flag': {'W': 'WIRE LINE', 'S': 'SONIC', 'V': 'VISUAL', 'O': 'OTHER'},
        'wb_h15_mech_integ_test_flag': {'H': 'HYDRAULIC', 'O': 'OTHER'},
        'wb_h15_mech_test_reason_flag': {'A': 'SUBSTITUTE', 'B': 'REQUIRED 14(B)(2)'},
        'wb_h15_no_date_well_flag': {'Y': 'YES'},
        'wb_h15_record_from_edi_flag': {'Y': 'YES'},
        'wb_h15_2yrs_approved_flag': {'Y': 'YES'},
        'wb_h15_mail_hold_flag': {'Y': 'YES'},
    },
    'WBSB126': {
        'wb_sb126_designation_flag': {
            'A': 'AUTOMATICALLY DESIGNATED',
            'M': 'MANUALLY DESIGNATED'
        },
        'wb_sb126_denial_reason_flag': {
            'A': 'AUTOMATICALLY DENIED',
            'M': 'MANUALLY DENIED'
        }
    },
    'WBDASTAT': {
        'wb_dastat_deleted_flag': {'Y': 'DELETED', 'N': 'ACTIVE'}
    },
    'WBW3C': {
        'wb_w3c_1yr_flag': {
            'Y': '1 YEAR REQUIREMENTS MET',
            'F': 'FALSELY CERTIFIED'
        },
        'wb_w3c_5yr_flag': {
            'R': '5 YEAR REQUIREMENTS MET',
            'O': 'OPERATOR OWNS LAND',
            'F': 'FALSELY CERTIFIED'
        },
        'wb_w3c_10yr_flag': {
            'R': '10 YEAR REQUIREMENTS MET',
            'O': 'OPERATOR OWNS LAND',
            'E': 'PART OF EOR PROJECT',
            'J': '10 YEAR REJECTED', # Spec image says 'J' REJ. Wait, 88 REJ VALUE 'J'. Correct.
            'F': 'FALSELY CERTIFIED'
        },
        'wb_w3c_extension_flag': {
            'Y': 'TEMPORARY EXCEPTION GRANTED',
            'F': 'FALSELY FILED EXCEPTION'
        }
    }
}
