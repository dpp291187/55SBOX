`timescale 1ns/1ps
`default_nettype none

module proposed_sbox_factorized (
    input  wire [4:0] din,
    output wire [4:0] dout
);
    wire x0 = din[4];
    wire x1 = din[3];
    wire x2 = din[2];
    wire x3 = din[1];
    wire x4 = din[0];

    wire u0 = x0 ^ x2;
    wire u1 = x2 ^ x3;
    wire u2 = x3 ^ x4;

    wire f0 = (x0 & x3) ^ (x1 & ~x4) ^ (~x1 & x2);
    wire f1 = (x0 & u2) ^ (x1 & ~x3) ^ (~u1 & x4);
    wire f2 = (x0 & ~u1) ^ (x1 & u0) ^ (u1 & u2);
    wire f3 = (x0 & x2) ^ (~x1 & x4) ^ (~x2 & u2);
    wire f4 = (x0 & ~x1) ^ (~u0 & ~x4) ^ (~u1 & u2);

    assign dout = {f4,f3,f2,f1,f0};
endmodule

`default_nettype wire
