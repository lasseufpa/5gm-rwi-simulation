%goal here is to learn how to convert a position x,y provided by
%Sumo into something InSite can properly interpret.
function m1=ita2

laneA.start=[757 645]; %node1
laneA.end=[768 470]; %node2
laneB.end=[741 645]; %node3
laneB.start=[752 470]; %node4
chosenLane = 'B'; %choose A or B
if chosenLane == 'A' %start of laneA
    lane=laneA;
    %pointSumoAfterStep=[14.86 166.82]; %truck of 8 meters
    %pos=8.10; %truck of 8 meters
    %pointSumoAfterStep=[14.36 174.80]; %truck with 0.0001 meters
    %pos=0.10; %truck with 0.0001 meters
    pointSumoAfterStep=[20 84.98]; %truck with 90 meters
    pos=90.10; %truck with 90 meters
else %start of laneB
    lane=laneB;
    %pointSumoAfterStep=[12.14 8.18]; %truck of 8 meters
    %pos=8.10; %truck of 8 meters
    %pointSumoAfterStep=[12.64 0.20]; %truck with 0.0001 meters
    %pos=0.10; %truck with 0.0001 meters
    pointSumoAfterStep=[7 90.02]; %truck with 90 meters
    pos=90.10; %truck with 90 meters
end
pointInSiteTarget=lane.start %target point
%angle depends on the lane direction:
angleRad=atan2(lane.end(2)-lane.start(2),lane.end(1)-lane.start(1));
angleSumo = omnet2traciAngle(angleRad)
deltax=pos*cos(angleRad)
deltay=pos*sin(angleRad)
pointSumo = pointSumoAfterStep - [deltax deltay]

%the margin is below a correction factor. Could not make it
%work properly. It varies depending the lane. The vehicle length
%is not the issue.
if chosenLane == 'A'
    margin=[-1.6523   -0.0975];
else
    margin=[1.6523    0.0975];
end
%margin = [0 0];

[netBoundsMin, netBoundsMax]=getSumoNetBounds(laneA,laneB);

tryInSite = pointSumo+netBoundsMin
pointInSiteTarget - tryInSite

pointInSite2=convertSumoToInSiteCoordinates(pointSumo,netBoundsMin,netBoundsMax,margin)
pointSumo2=convertInSiteToSumoCoordinates(pointInSite2,netBoundsMin,netBoundsMax,margin)

conversionError = pointInSite2 - pointInSiteTarget

if 0 %extra testes
    %point=[15.61 160.83] %laneA
    point=[12.02 8.18] %laneB
    convertSumoToInSiteCoordinates(point,netBoundsMin,netBoundsMax,margin)
    
    %point=[25.35 0.05] %laneA
    point=[1.66 174.95] %laneB
    convertSumoToInSiteCoordinates(point,netBoundsMin,netBoundsMax,margin)
end
end

function [m,b]=getLineParameters(lane)
anglerad=atan2(lane.end(2)-lane.start(2),lane.end(1)-lane.start(1));
m=(lane.end(2)-lane.start(2))/(lane.end(1)-lane.start(1));
angle=anglerad*180/pi;
b=lane.end(2)-m*lane.end(1);
end

function [netBoundsMin, netBoundsMax]=getSumoNetBounds(laneA,laneB)
minX=min([laneA.start(1),laneB.start(1),laneA.end(1),laneB.end(1)]);
minY=min([laneA.start(2),laneB.start(2),laneA.end(2),laneB.end(2)]);
netBoundsMin=[minX minY];

maxX=max([laneA.start(1),laneB.start(1),laneA.end(1),laneB.end(1)]);
maxY=max([laneA.start(2),laneB.start(2),laneA.end(2),laneB.end(2)]);
netBoundsMax=[maxX maxY];
end

%The source code of TraCIConnection.cc in software Veins (http://veins.car2x.org/documentation/faq/) has functions to convert coordinates and angles
%AK: I will assume netbounds1 has the min value and netbound2 the max as in
%https://groups.google.com/forum/#!topic/omnetpp/_-mHbZZmObA
%Coord TraCIConnection::traci2omnet(TraCICoord coord) const {
%    return Coord(coord.x - netbounds1.x + margin, (netbounds2.y - netbounds1.y) - (coord.y - netbounds1.y) + margin);
%}
%function outpoint=traci2omnet(point,netBoundsMin,netBoundsMax,margin)
function outpoint=convertInSiteToSumoCoordinates(point,netBoundsMin,netBoundsMax,margin)
if 1 %AK
    outpoint = point-netBoundsMin+margin;
else %C++ code
    outpoint=[0 0]; %initialize
    outpoint(1) = point(1)-netBoundsMin(1)+margin(1);
    outpoint(2) = netBoundsMax(2) - point(2) + margin(2);
end
end

%TraCICoord TraCIConnection::omnet2traci(Coord coord) const {
%    return TraCICoord(coord.x + netbounds1.x - margin, (netbounds2.y - netbounds1.y) - (coord.y - netbounds1.y) + margin);
%}
%function outpoint=omnet2traci(point,netBoundsMin,netBoundsMax,margin)
function outpoint=convertSumoToInSiteCoordinates(point,netBoundsMin,netBoundsMax,margin)
if 1 %AK
    outpoint = point+netBoundsMin-margin;
else %C++ code
    outpoint=[0 0]; %initialize
    outpoint(1) = point(1)+netBoundsMin(1)-margin(1);
    outpoint(2) = netBoundsMax(2) - point(2) + margin(2);
end
end

%double TraCIConnection::traci2omnetAngle(double angle) const {
%rotate angle so 0 is east (in TraCI's angle interpretation 0 is north, 90 is east)
%    angle = 90 - angle;
%// convert to rad
%angle = angle * M_PI / 180.0;
function angleInSite = traci2omnetAngle(angleSumo)
angleSumo=90-angleSumo;
angleInSite=angleSumo*pi/180;
end

%double TraCIConnection::omnet2traciAngle(double angle) const {
%angle = angle * 180 / M_PI;     // convert to degrees
%// rotate angle so 0 is south (AK???) (in OMNeT++'s angle interpretation 0 is east, 90 is north)
%angle = 90 - angle;
function angleSumo = omnet2traciAngle(angleInSite)
angleInSite=angleInSite*180/pi;
angleSumo=90-angleInSite;
end
