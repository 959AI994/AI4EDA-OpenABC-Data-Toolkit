module jk_flip_flop (
    input wire clk,
    input wire j,
    input wire k,
    output wire q,
    output wire q_
);

reg state;

initial begin
    state = 1'b0;
end

assign q = state;
assign q_ = ~state;

always @(posedge clk) begin
    case ({j, k})
        2'b00: state <= state;    // No change
        2'b01: state <= 1'b0;     // Reset
        2'b10: state <= 1'b1;     // Set
        2'b11: state <= ~state;   // Toggle
        default: state <= 1'b0;   // Default to reset state
    endcase
end

endmodule