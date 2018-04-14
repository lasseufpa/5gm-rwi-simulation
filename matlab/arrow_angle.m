i=3 %index of best beam for Tx
j=5 %index of best beam for Rx
Ni=64; %number of Tx beams
Nj=64; %number of Rx beams
mag=5 %magnitude of vector
deltaI=(2*pi)/Ni %angle for each beam in Tx
deltaJ=(2*pi)/Nj %angle for each beam in Rx

for i=1:Ni
   for j=1:Nj
       angleI=i*deltaI-(deltaI/2);
       angleJ=j*deltaJ-(deltaJ/2);
       vectorI=mag*exp(1j*angleI);
       vectorJ=mag*exp(1j*angleJ);
       %plot two vectors keeping the aspect ratio to denote a circle.
       %Use different colors
       clf
       plot([0 real(vectorI)], [0 imag(vectorI)], '-xb')
       hold on
       plot([0 real(vectorJ)], [0 imag(vectorJ)], '-or')
       title([num2str(i) ' and ' num2str(j)])
       axis(mag*[-1.2 1.2 -1.2 1.2])
       pause
   end
end
