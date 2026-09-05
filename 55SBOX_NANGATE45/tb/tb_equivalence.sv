`timescale 1ns/1ps

module tb_equivalence;
    reg [4:0] din;
    wire [4:0] proposed_lut_out;
    wire [4:0] fides_lut_out;
    wire [4:0] proposed_factorized_out;
    wire [4:0] proposed_shared_affine_out;
    integer i;
    integer errors;

    proposed_sbox_lut        dut0 (.din(din), .dout(proposed_lut_out));
    fides_sbox_lut           dut1 (.din(din), .dout(fides_lut_out));
    proposed_sbox_factorized  dut2 (.din(din), .dout(proposed_factorized_out));
    proposed_sbox_shared_affine dut3 (.din(din), .dout(proposed_shared_affine_out));

function automatic [4:0] proposed_ref;
    input [4:0] x;
    begin
        case (x)
            5'd 0: proposed_ref = 5'd16;
            5'd 1: proposed_ref = 5'd18;
            5'd 2: proposed_ref = 5'd28;
            5'd 3: proposed_ref = 5'd 8;
            5'd 4: proposed_ref = 5'd 1;
            5'd 5: proposed_ref = 5'd13;
            5'd 6: proposed_ref = 5'd17;
            5'd 7: proposed_ref = 5'd11;
            5'd 8: proposed_ref = 5'd19;
            5'd 9: proposed_ref = 5'd24;
            5'd10: proposed_ref = 5'd29;
            5'd11: proposed_ref = 5'd 0;
            5'd12: proposed_ref = 5'd 7;
            5'd13: proposed_ref = 5'd 2;
            5'd14: proposed_ref = 5'd21;
            5'd15: proposed_ref = 5'd 6;
            5'd16: proposed_ref = 5'd20;
            5'd17: proposed_ref = 5'd 4;
            5'd18: proposed_ref = 5'd31;
            5'd19: proposed_ref = 5'd25;
            5'd20: proposed_ref = 5'd 9;
            5'd21: proposed_ref = 5'd23;
            5'd22: proposed_ref = 5'd30;
            5'd23: proposed_ref = 5'd22;
            5'd24: proposed_ref = 5'd 3;
            5'd25: proposed_ref = 5'd26;
            5'd26: proposed_ref = 5'd10;
            5'd27: proposed_ref = 5'd 5;
            5'd28: proposed_ref = 5'd27;
            5'd29: proposed_ref = 5'd12;
            5'd30: proposed_ref = 5'd14;
            5'd31: proposed_ref = 5'd15;
            default: proposed_ref = 5'd0;
        endcase
    end
endfunction

function automatic [4:0] fides_ref;
    input [4:0] x;
    begin
        case (x)
            5'd 0: fides_ref = 5'd 1;
            5'd 1: fides_ref = 5'd 0;
            5'd 2: fides_ref = 5'd25;
            5'd 3: fides_ref = 5'd26;
            5'd 4: fides_ref = 5'd17;
            5'd 5: fides_ref = 5'd29;
            5'd 6: fides_ref = 5'd21;
            5'd 7: fides_ref = 5'd27;
            5'd 8: fides_ref = 5'd20;
            5'd 9: fides_ref = 5'd 5;
            5'd10: fides_ref = 5'd 4;
            5'd11: fides_ref = 5'd23;
            5'd12: fides_ref = 5'd14;
            5'd13: fides_ref = 5'd18;
            5'd14: fides_ref = 5'd 2;
            5'd15: fides_ref = 5'd28;
            5'd16: fides_ref = 5'd15;
            5'd17: fides_ref = 5'd 8;
            5'd18: fides_ref = 5'd 6;
            5'd19: fides_ref = 5'd 3;
            5'd20: fides_ref = 5'd13;
            5'd21: fides_ref = 5'd 7;
            5'd22: fides_ref = 5'd24;
            5'd23: fides_ref = 5'd16;
            5'd24: fides_ref = 5'd30;
            5'd25: fides_ref = 5'd 9;
            5'd26: fides_ref = 5'd31;
            5'd27: fides_ref = 5'd10;
            5'd28: fides_ref = 5'd22;
            5'd29: fides_ref = 5'd12;
            5'd30: fides_ref = 5'd11;
            5'd31: fides_ref = 5'd19;
            default: fides_ref = 5'd0;
        endcase
    end
endfunction

    initial begin
        errors = 0;
        for (i = 0; i < 32; i = i + 1) begin
            din = i[4:0];
            #1;
            if (proposed_lut_out        !== proposed_ref(din)) errors = errors + 1;
            if (proposed_factorized_out    !== proposed_ref(din)) errors = errors + 1;
            if (proposed_shared_affine_out !== proposed_ref(din)) errors = errors + 1;
            if (fides_lut_out           !== fides_ref(din))    errors = errors + 1;
        end

        if (errors == 0) begin
            $display("PREFLIGHT_PASS");
            $finish;
        end

        $display("PREFLIGHT_FAIL errors=%0d", errors);
        $fatal(1);
    end
endmodule
