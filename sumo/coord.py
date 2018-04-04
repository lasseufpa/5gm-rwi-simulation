import numpy as np


def convert_distances(lane, point_sumo, lane_boundary_dict=None, margin_dict=None):
    def get_sumo_net_bounds(lane_boundary_dict):
        boundary_array = None
        for lane, boundary in lane_boundary_dict.items():
            if boundary_array is None:
                boundary_array = np.array(boundary, ndmin=2)
            else:
                boundary_array = np.concatenate((boundary_array, np.array(boundary, ndmin=2)), 0)
        return np.min(boundary_array, 0), np.max(boundary_array, 0)

    def convert_sumo_to_insite_coordinates(point, net_bounds_min, net_bounds_max, margin):
        if True:
            return point + net_bounds_min - margin
        else:
            return (point[0] + net_bounds_min[0] - margin[0],
                    net_bounds_max[1] - point[1] + margin[1])

    #margin = np.array(margin_dict[lane])
    margin = [0, 0]
    net_bounds_min, net_bounds_max = get_sumo_net_bounds(lane_boundary_dict)

    return convert_sumo_to_insite_coordinates(point_sumo, net_bounds_min, net_bounds_max, margin)

"""
%goal here is to learn how to convert a position x,y provided by
%Sumo into something InSite can properly interpret.
function convertDistances

laneA.start=[757 645]; %node1
laneA.end=[768 470]; %node2
laneB.end=[741 645]; %node3
laneB.start=[752 470]; %node4

chosenLane = 'B'; %unfortunately need to choose A or B

%the margin is below a correction factor. Could not make it
%work properly. It varies depending the lane. The vehicle length
%is not the issue.
if chosenLane == 'A'
    margin=[-1.6523   -0.0975];
else
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
%rotate angle so 0 is east (in TraCI's angle interpretation 0 is north, 90 is east) \
                                    %    angle = 90 - angle;
%// convert to rad \
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
"""
