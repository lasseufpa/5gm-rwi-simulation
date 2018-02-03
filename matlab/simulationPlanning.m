%%AK Script to estimate number of results based on simulation time
%%collected by Pedro using our fastest computer.

rtDegreeRes=[1 0.25]; %InSite ray tracing (rt) resolution in degrees
diffusionScattering=1; %enabled or not
if diffusionScattering==1
    TstartSim=[66 198]; %time estimated by Pedro for 1 Rx (seconds)
    TperRxSim=[5 10]; %time estimated by Pedro for adding an extra Rx (seconds)
else %Pedro, should I divide by 2?????
    TstartSim=[66 198]/3; %time estimated by Pedro for 1 Rx (seconds)
    TperRxSim=[5 10]/3; %time estimated by Pedro for adding an extra Rx (seconds)
end
chosenDegreeRes=1; %choose a resolution

%% Define Ts and Te
vel=15 %m/s
streetWidth=20 %meters
d=tan(rtDegreeRes(chosenDegreeRes)*pi/180)*streetWidth; %distance, ortogonal to DSU
Ts=d/vel %to given an idea
Ts=100e-3; %assumed Ts
Te=5;
numScenesPerEpisode=floor(Te/Ts) %num of scene per episode

%% Evaluate processing time
Nrx=1:25; %num of Rxs
%time for a snapshot, one InSite simulation
TinsiteSim=TstartSim(chosenDegreeRes)+Nrx*TperRxSim(chosenDegreeRes)   % seconds
TrxResult=TinsiteSim./Nrx; %time for obtaining one Rx result
plot(Nrx,TrxResult)

Nrx=10; %good tradeoff between less time and diversity (see curves)
%reset values for final choice
TinsiteSim=TstartSim(chosenDegreeRes)+Nrx*TperRxSim(chosenDegreeRes)   % seconds
TrxResult=TinsiteSim./Nrx; %time for obtaining one Rx result
TepisodeResult=TrxResult*numScenesPerEpisode;

Ttotal=48*60*60; % available time for simulation: 2 days

numEpi=floor(Ttotal/TepisodeResult) %final number of episodes
numScenes=numEpi*numScenesPerEpisode %final number of classification problems (scenes)