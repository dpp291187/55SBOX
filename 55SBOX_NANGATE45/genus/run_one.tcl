foreach V {PROJECT_ROOT LIB_FILE CONFIGURATION TOP RTL} {
    if {![info exists ::env($V)]} { error "$V missing" }
}

set ROOT $::env(PROJECT_ROOT)
set LIB  $::env(LIB_FILE)
set ID   $::env(CONFIGURATION)
set TOP  $::env(TOP)
set RTL  $::env(RTL)

set REPORT_BASE "reports"
set NETLIST_BASE "netlist"

if {[info exists ::env(REPORT_BASE)]} {
    set REPORT_BASE $::env(REPORT_BASE)
}
if {[info exists ::env(NETLIST_BASE)]} {
    set NETLIST_BASE $::env(NETLIST_BASE)
}

set RPT "${ROOT}/${REPORT_BASE}/${ID}"
set NET "${ROOT}/${NETLIST_BASE}/${ID}"

file mkdir $RPT
file mkdir $NET

set_db library $LIB

read_hdl $RTL
elaborate $TOP

check_design -unresolved > "${RPT}/01_check_design.rpt"

create_clock -name VCLK -period 10.000
set_input_delay 0.0 -clock VCLK [all_inputs]
set_output_delay 0.0 -clock VCLK [all_outputs]

syn_generic
report_area > "${RPT}/02_area_generic.rpt"

syn_map
report_area > "${RPT}/03_area_mapped.rpt"
report_timing -from [all_inputs] -to [all_outputs] -max_paths 10 \
    > "${RPT}/04_timing_mapped.rpt"

syn_opt
report_area > "${RPT}/05_area_final.rpt"
report_timing -from [all_inputs] -to [all_outputs] -max_paths 20 \
    > "${RPT}/06_timing_final.rpt"
report_qor > "${RPT}/07_qor_final.rpt"
report_power > "${RPT}/08_power_preliminary.rpt"
report_gates > "${RPT}/09_gates_final.rpt"

write_hdl > "${NET}/${ID}_mapped.v"
write_sdc > "${NET}/${ID}.sdc"

puts "GENUS_DONE: $ID"
exit
