# ####################################################################

#  Created by Genus(TM) Synthesis Solution 23.14-s090_1 on Fri Aug 28 07:05:38 +07 2026

# ####################################################################

set sdc_version 2.0

set_units -capacitance 1fF
set_units -time 1000ps

# Set the current design
current_design proposed_sbox_shared_affine

create_clock -name "VCLK" -period 10.0 -waveform {0.0 5.0} 
set_clock_gating_check -setup 0.0 
set_input_delay -clock [get_clocks VCLK] -add_delay 0.0 [get_ports {din[4]}]
set_input_delay -clock [get_clocks VCLK] -add_delay 0.0 [get_ports {din[3]}]
set_input_delay -clock [get_clocks VCLK] -add_delay 0.0 [get_ports {din[2]}]
set_input_delay -clock [get_clocks VCLK] -add_delay 0.0 [get_ports {din[1]}]
set_input_delay -clock [get_clocks VCLK] -add_delay 0.0 [get_ports {din[0]}]
set_output_delay -clock [get_clocks VCLK] -add_delay 0.0 [get_ports {dout[4]}]
set_output_delay -clock [get_clocks VCLK] -add_delay 0.0 [get_ports {dout[3]}]
set_output_delay -clock [get_clocks VCLK] -add_delay 0.0 [get_ports {dout[2]}]
set_output_delay -clock [get_clocks VCLK] -add_delay 0.0 [get_ports {dout[1]}]
set_output_delay -clock [get_clocks VCLK] -add_delay 0.0 [get_ports {dout[0]}]
set_wire_load_mode "enclosed"
