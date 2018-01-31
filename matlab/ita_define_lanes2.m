%Define lanes to fit InSite scenario. AK. Jan 30, 2018.
%Generates output that can be used for the Sumo nodes XML file and also the rwi Python code
clear all
streetCenter.start=[764 460];
streetCenter.end=[750 660];
N=4;
laneWidth=3; %3 meters
laneCenter{N}=[];
laneCenterDist=[-5.5 -2.5 2.5 5.5]; %separate pair of lanes by 1 m
clf
plotLane(streetCenter,'k')
hold on
for i=1:N
    laneCenter{i}.start=[streetCenter.start(1)+laneCenterDist(i) streetCenter.start(2)];
    laneCenter{i}.end=[streetCenter.end(1)+laneCenterDist(i) streetCenter.end(2)];
    plotLane(laneCenter{i},'r')
    %lane{i}.start=[laneCenter.start(1)-0.5*laneWidth laneCenter.start(2)];
    %lane{i}.end=[laneCenter.end(1)+0.5*laneWidth laneCenter.end(2)];
    %plotLane(lane{i},'b')
end

%generate directly as XML:
%    <node id="7" x="761" y="657" />
%    <node id="8" x="767" y="457" />
id=1;
disp('####### For file ita.nod.xml')
disp('<nodes>')
for i=1:N
    x=laneCenter{i}.start(1);
    y=laneCenter{i}.start(2);
    disp(['    <node id="' num2str(id) '" x="' num2str(x) '" y="' num2str(y) '" />'])
    id = id+1;
    x=laneCenter{i}.end(1);
    y=laneCenter{i}.end(2);
    disp(['    <node id="' num2str(id) '" x="' num2str(x) '" y="' num2str(y) '" />'])
    id = id+1;
end
disp('</nodes>')

disp('####### For file config.py')
% lane_boundary_dict = {"laneA_0": [[757, 457], [751, 657]],
%                     "laneB_0": [[760, 457], [754, 657]],
%                     "laneC_0": [[758, 657], [764, 457]],
%                     "laneD_0": [[761, 657], [767, 457]]}
%The Python notation is to put first the start of the lane and then the end
%so need to invert the order to mimic what Sumo does in the edge XML file.
myLetters='ABCDEFGHI'; %in case there are more lanes
fprintf('%s','lane_boundary_dict = {"')
invertedDirectionLanes=[0 0 1 1]; %last two inverted
for i=1:N
    if i ~= 1
        fprintf('    ');
    end
    fprintf('%s',['lane' myLetters(i) '_0": [['])
    if invertedDirectionLanes(i) == 1
        fprintf('%s',[num2str(laneCenter{i}.end(1)) ',' ...
            num2str(laneCenter{i}.end(2)) '], [' ...
            num2str(laneCenter{i}.start(1)) ',' ...
            num2str(laneCenter{i}.start(2)) ']]'])
        %fprintf('\n')
    else
        fprintf('%s',[num2str(laneCenter{i}.start(1)) ',' ...
            num2str(laneCenter{i}.start(2)) '], [' ...
            num2str(laneCenter{i}.end(1)) ',' ...
            num2str(laneCenter{i}.end(2)) ']]'])
        %fprintf('\n')
    end
    fprintf('\n')
end