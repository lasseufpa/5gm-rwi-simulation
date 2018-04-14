function [w] = dft_codebook(dim)
%UNTITLED4 Summary of this function goes here
%   Detailed explanation goes here
seq = 0: dim-1;
mat = seq' * seq;
w = exp(-1j*2*pi*mat/dim);
end

