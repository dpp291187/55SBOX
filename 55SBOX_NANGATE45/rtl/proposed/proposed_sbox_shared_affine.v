`timescale 1ns/1ps
`default_nettype none

// Shared-affine realization of the proposed 5x5 S-box.
// This is the R6_OLD_SHARED_AFFINE candidate from the ASIC-aware search.
// Bit convention matches proposed_sbox_factorized.v:
//   x0=din[4], x1=din[3], x2=din[2], x3=din[1], x4=din[0].
module proposed_sbox_shared_affine (
    input  wire [4:0] din,
    output wire [4:0] dout
);
    wire x0 = din[4];
    wire x1 = din[3];
    wire x2 = din[2];
    wire x3 = din[1];
    wire x4 = din[0];

    // Shared affine forms.
    wire a = x3 ^ x2;
    wire b = x4 ^ x3 ^ x0;

    // Complements shared by the nonlinear products.
    wire n_x4 = ~x4;
    wire n_x3 = ~x3;
    wire n_a  = ~a;
    wire n_x1 = ~x1;
    wire n_b  = ~b;

    // Thirteen unique nonlinear products.
    wire p00 = x2   & n_x1;
    wire p01 = n_x1 & x0;
    wire p02 = n_x3 & n_a;
    wire p03 = n_x4 & b;
    wire p04 = a    & b;
    wire p05 = n_x3 & x1;
    wire p06 = x3   & n_b;
    wire p07 = n_x4 & x1;
    wire p08 = x0   & n_b;
    wire p09 = x4   & n_a;
    wire p10 = x4   & x1;
    wire p11 = x3   & x0;
    wire p12 = x2   & x1;

    assign dout[0] = p07 ^ p11 ^ p00;
    assign dout[1] = p09 ^ p05 ^ p08;
    assign dout[2] = p12 ^ p04 ^ p01;
    assign dout[3] = p10 ^ p06 ^ p04;
    assign dout[4] = p03 ^ p02 ^ p01;
endmodule

`default_nettype wire
