function [t1] = calc_rx_power (departure_angle, arrival_angle, p_gain, antenna_number)
%% departure angle/arrival angle will be a matrix as size of (L, 2), where L is the number of paths
%% the first column will be the elevation angle, and the second column is the azimuth angle correspondingly.
%% p_gain will be a matrix size of (L, 1)
%% This .m file uses a m*m SQUARE UPA, so the antenna number at TX, RX will be antenna_number^2.
%%parameters for use%
bandwidth = 8*1e8;
frequency = 6*1e10;
%% we assume we use DFT codebook in this case
c = 3 * 1e8;
lambda = c/frequency;
k = 2*pi/lambda;
d = lambda/2;
nt = antenna_number^2; %%assume SQUARE UPA
m = size(departure_angle, 1); 
nr = nt;
wt = dft_codebook(nt); %%generate DFT codebook for precoders
wr = dft_codebook(nr); %%generate DFT codebook for combiners
H = zeros(nt, nr);
for i = 1 : m
    gain_dB = p_gain(i);
    path_gain = 10^(gain_dB/10);
    omegay = k*d*sin(departure_angle(i,2)) * sin(departure_angle(i,1)); 
    omegax = k*d*sin(departure_angle(i,2)) * cos(departure_angle(i,1));
    vecy = exp(1j * omegay * (0: antenna_number - 1));
    vecx = exp(1j * omegax * (0: antenna_number - 1));
    departure_vec = kron(vecy, vecx); %%departing steering vectors as in Eq. 2 of inverse fingerprinting 
    omegay = k*d*sin(arrival_angle(i,2)) * sin(arrival_angle(i,1));
    omegax = k*d*sin(arrival_angle(i,2)) * cos(arrival_angle(i,1));
    vecy = exp(1j * omegay * (0: antenna_number - 1)); 
    vecx = exp(1j * omegax * (0: antenna_number - 1));
    arrival_vec= kron(vecy, vecx); %%arrival steering vectors as in Eq. 2 of Inverse fingerprinting
    H = H + path_gain * departure_vec' * arrival_vec; %%Generate channel based on geometric channel model. 
end
t1 = wt' * H * wr;
%%t1 will be a matrix of size (nt, nr), each
%%element of index (i,j) will be the received
%%power with the i-th precoder and the j-th
%%combiner in the departing and arrival codebooks
%%respectively
end 


