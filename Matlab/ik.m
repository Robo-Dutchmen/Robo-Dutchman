function [joint_space, valid] = ik(work_space, elbow_up)

    l1 = 1; %First link (15 in)
    l2 = 1; % Second Link (13 in)
    l3 = 0.2; % Wrist Distance (5 1/8th in)

    %otal d: 1.5

    % Dist between ecenters of tubes: 2 and 5/8s
    %Robot in [0 0 0 0] configuration is pointing straight in x direction
    % Arm moves in x y plane of end effector

    %Angle is measured with respect to x axis


    target_theta = work_space(3);
    target_x = work_space(1);
    target_y = work_space(2);
    target_wrist = work_space(4);

    joint_space = [0 0 0];

    %Place first joint down first
    wrist_center = [target_x-l3*cos(target_theta);...
        target_y-l3*sin(target_theta);...
        target_theta]';

    %elbow
    joint_space(2) = acos( ...
        (wrist_center(1)^2 + wrist_center(2)^2 - l1^2 - l2^2)...
        / (2 * l1 * l2));

    % shoulder
    joint_space(1) = atan2(wrist_center(2),wrist_center(1))...
        - atan2( (l2 * sin(joint_space(2))), ...
                 (l1 + l2 * cos(joint_space(2))));
            
    % Change elbow up or down
    if (nargin > 1 && elbow_up(1))
        joint_space = flip_elbow(joint_space);
    end

    % wrist 1
    joint_space(3) = target_theta - joint_space(2) - joint_space(1);

    % wrist 2
    joint_space(4) = target_wrist;
    
    % second motor (elbow) has flipped axis
    joint_space(2) = -joint_space(2);
    
    valid = true;
    
    function joint_space = flip_elbow(joint_space)
        angle_to_wrist_center = atan2(wrist_center(2),wrist_center(1));
        diff_wrist_angle_to_shoulder = angle_to_wrist_center...
            - joint_space(1);
        joint_space(1) =  joint_space(1) + 2 * diff_wrist_angle_to_shoulder;
        joint_space(2) = -joint_space(2);
    end
    
end

