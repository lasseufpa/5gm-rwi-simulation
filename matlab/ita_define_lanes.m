%Define lanes to fit InSite scenario. AK. Jan 30, 2018.
function ita_define_lanes
%original bounds obtained by browsing InSite
pur=[766.31 657]
pdr=[778.03 448.19]
pul=[745.94 657]
pdl=[751.54 457.36]
%original bounds rounded for integers by myself
pur=[766 657]
pdr=[778 457]
pul=[746 657]
pdl=[752 457]

pur-pul
pdr-pdl
%in terms of x, upper has 20 m of space while down has 26 m. Use upper
middleXUpper = (pur(1)-pul(1))/2 + pul(1); %756
middleXLower = pdl(1)+10;
middleUpper=[middleXUpper 657]
middleLower=[middleXLower 457]
clf
plot([pur(1) pdr(1)], [pur(2) pdr(2)],'k')
hold on
plot([pul(1) pdl(1)], [pul(2) pdl(2)],'k')
title('Black: boundaries and blue: center of lanes. X indicates where lane starts');
lineCenter.start = [middleLower(1) middleLower(2)];
lineCenter.end = [middleUpper(1) middleUpper(2)];

%middleYUpper = (pur(1)-pul(1))/2 + pul(1);
%make things with respect to B
leftBorder.end=pul; %node3
leftBorder.start=pdl; %node4
[m1,b1]=getLineParameters(leftBorder)
[m2,b2]=getLineParameters(lineCenter)

m1-m2 %have same angle
N=4; %num of lanes
laneCenterA.start=[lineCenter.start(1)-5 lineCenter.start(2)]
laneCenterA.end=[lineCenter.end(1)-5 lineCenter.end(2)]
hold on
plotLane(laneCenterA,'b')
laneCenterB.start=[lineCenter.start(1)-2 lineCenter.start(2)]
laneCenterB.end=[lineCenter.end(1)-2 lineCenter.end(2)]
plotLane(laneCenterB,'b')
%invert direction of C and D
laneCenterC.start=[lineCenter.end(1)+2 lineCenter.end(2)]
laneCenterC.end=[lineCenter.start(1)+2 lineCenter.start(2)]
plotLane(laneCenterC,'b')
laneCenterD.start=[lineCenter.end(1)+5 lineCenter.end(2)]
laneCenterD.end=[lineCenter.start(1)+5 lineCenter.start(2)]
plotLane(laneCenterD,'b')

%mark where the cars start
plot(laneCenterA.start(1),laneCenterA.start(2),'xr','MarkerSize',20)
plot(laneCenterB.start(1),laneCenterB.start(2),'xr','MarkerSize',20)
plot(laneCenterC.start(1),laneCenterC.start(2),'xr','MarkerSize',20)
plot(laneCenterD.start(1),laneCenterD.start(2),'xr','MarkerSize',20)
disp('Result:')
laneCenterA, laneCenterB, laneCenterC, laneCenterD

%This was the final result:
% laneA.start = [757 457]; %node2
% laneA.end = [751 657]; %node1
% laneB.start = [760 457]; %node4
% laneB.end = [754 657]; %node3
% laneC.start = [758 657]; %node5
% laneC.end = [764 457]; %node6
% laneD.start = [761 657]; %node7
% laneD.end = [767 457]; %node8
% directly as XML:
% <nodes>
%    <node id="1" x="751" y="657" />
%    <node id="2" x="757" y="457" />
%    <node id="3" x="754" y="657" />
%    <node id="4" x="760" y="457" />
%    <node id="5" x="758" y="657" />
%    <node id="6" x="764" y="457" />
%    <node id="7" x="761" y="657" />
%    <node id="8" x="767" y="457" />
% </nodes>
end

function [m,b]=getLineParameters(lane)
anglerad=atan2(lane.end(2)-lane.start(2),lane.end(1)-lane.start(1));
m=(lane.end(2)-lane.start(2))/(lane.end(1)-lane.start(1));
angle=anglerad*180/pi;
b=lane.end(2)-m*lane.end(1);
end

