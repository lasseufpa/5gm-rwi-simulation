%goal here is to learn how to convert a position x,y provided by
%Sumo into something InSite can properly interpret.
function convertDistances4Lanes

laneA.start = [757 457]; %node2
laneA.end = [751 657]; %node1
laneB.start = [760 457]; %node4
laneB.end = [754 657]; %node3
laneC.start = [758 657]; %node5
laneC.end = [764 457]; %node6
laneD.start = [761 657]; %node7
laneD.end = [767 457]; %node8

chosenLane = 'B'; %unfortunately need to choose A or B or C or D

%the margin is below a correction factor. Could not make it
%work properly. It varies depending the lane. The vehicle length
%is not the issue.
if chosenLane == 'A' || chosenLane == 'B'
    margin=[-1.6523   -0.0975];
else % C and D
    margin=[1.6523    0.0975];
end

[netBoundsMin, netBoundsMax]=getSumoNetBounds(laneA,laneB);

pointSumo = [20 84.98];

pointInSite2=convertSumoToInSiteCoordinates(pointSumo,netBoundsMin,netBoundsMax,margin)
pointSumo2=convertInSiteToSumoCoordinates(pointInSite2,netBoundsMin,netBoundsMax,margin)
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
