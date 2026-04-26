// 简单标准单元库定义
module AND2(A, B, Y);
  input A, B;
  output Y;
  assign Y = A & B;
endmodule

module OR2(A, B, Y);
  input A, B;
  output Y;
  assign Y = A | B;
endmodule

module XOR2(A, B, Y);
  input A, B;
  output Y;
  assign Y = A ^ B;
endmodule

module NAND2(A, B, Y);
  input A, B;
  output Y;
  assign Y = ~(A & B);
endmodule

module NOR2(A, B, Y);
  input A, B;
  output Y;
  assign Y = ~(A | B);
endmodule

module INV(A, Y);
  input A;
  output Y;
  assign Y = ~A;
endmodule

module BUF(A, Y);
  input A;
  output Y;
  assign Y = A;
endmodule

module MX2(A, B, S0, Y);
  input A, B, S0;
  output Y;
  assign Y = S0 ? B : A;
endmodule

module FA(A, B, CI, S, CO);
  input A, B, CI;
  output S, CO;
  assign S = A ^ B ^ CI;
  assign CO = (A & B) | (B & CI) | (A & CI);
endmodule

module HA(A, B, S, CO);
  input A, B;
  output S, CO;
  assign S = A ^ B;
  assign CO = A & B;
endmodule
