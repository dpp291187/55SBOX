`timescale 1ns/1ps
`default_nettype none

module proposed_sbox_lut (
    input  wire [4:0] din,
    output reg  [4:0] dout
);
always @(*) begin
    case (din)
        5'd 0: dout = 5'd16;
        5'd 1: dout = 5'd18;
        5'd 2: dout = 5'd28;
        5'd 3: dout = 5'd 8;
        5'd 4: dout = 5'd 1;
        5'd 5: dout = 5'd13;
        5'd 6: dout = 5'd17;
        5'd 7: dout = 5'd11;
        5'd 8: dout = 5'd19;
        5'd 9: dout = 5'd24;
        5'd10: dout = 5'd29;
        5'd11: dout = 5'd 0;
        5'd12: dout = 5'd 7;
        5'd13: dout = 5'd 2;
        5'd14: dout = 5'd21;
        5'd15: dout = 5'd 6;
        5'd16: dout = 5'd20;
        5'd17: dout = 5'd 4;
        5'd18: dout = 5'd31;
        5'd19: dout = 5'd25;
        5'd20: dout = 5'd 9;
        5'd21: dout = 5'd23;
        5'd22: dout = 5'd30;
        5'd23: dout = 5'd22;
        5'd24: dout = 5'd 3;
        5'd25: dout = 5'd26;
        5'd26: dout = 5'd10;
        5'd27: dout = 5'd 5;
        5'd28: dout = 5'd27;
        5'd29: dout = 5'd12;
        5'd30: dout = 5'd14;
        5'd31: dout = 5'd15;
        default: dout = 5'd0;
    endcase
end
endmodule

`default_nettype wire
