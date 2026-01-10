module mux_8to1 (
    input [2:0] sel,
    output reg [7:0] res
);

always @(*) begin
    case (sel)
        3'b000: res = 8'b11111110;
        3'b001: res = 8'b11111101;
        3'b010: res = 8'b11111011;
        3'b011: res = 8'b11110111;
        3'b100: res = 8'b11101111;
        3'b101: res = 8'b11011111;
        3'b110: res = 8'b10111111;
        3'b111: res = 8'b01111111;
        default: res = 8'b11111111;
    endcase
end

endmodule