#!/usr/bin/env python
# encoding=utf-8

import open3d as o3d
import numpy as np
from os import path
import os
from PIL import Image
import sys
import copy
import time
import cv2
import matplotlib.pyplot as plt
import math
import rospy
from std_msgs.msg import Float32
from geometry_msgs.msg import Point
# from geometry_msgs.msg import Transform
# from scipy.spatial.transform import Rotation as R

#手眼标定矩阵 
eye2hand = np.asarray([[0.0904626,0.921224,-0.378368,859.768],
    [-0.266744,0.388457,0.882014,-311.074],
    [0.959512,0.0211384,0.280872,-283.255],
    [0,0,0,1]])
T = np.zeros((4,4))#存放变换阵
rm = 1
#模板点云的上下两端
Upoint=[[0.5982], [0.01946], [1.868]]
Lowpoint=[[0.2545], [0], [1.75]]
np.set_printoptions(threshold=np.inf)

#在代码同级创建文件夹“out”
save_path = os.path.join(os.getcwd(), "out")
if not os.path.exists(save_path):
    os.mkdir(save_path)

#发送平动误差
def talker(distance):
    pub = rospy.Publisher('distance', Float32, queue_size=10)
    temp=Float32()
    temp.data=distance
    rate = rospy.Rate(10) # 10hz
    while not rospy.is_shutdown():
        rospy.loginfo(temp)
        pub.publish(temp)
        rate.sleep()
    return
#发送变换矩阵
def talker2(T):
    pub = rospy.Publisher('transform', Point, queue_size=10)
    # rospy.init_node('talker', anonymous=True)
    # avg = avg.astype(np.float64)
    temp=Transform()

    T1=np.matmul(eye2hand, T)
    UP=np.matmul(T1, Upoint)
    DOWN=np.matmul(T1, Lowpoint)

    
    # R_dcm=np.asarray([[T[0][0],T[0][1],T[0][2]], 
    #     [T[1][0],T[1][1],T[1][2]],
    #     [T[2][0], T[2][1], T[2][2]]])
    # r = R.from_dcm(R_dcm.T)##### 加.T变换为转置
    # qvec_nvm = r.as_quat()
    # qvec_nvm = np.array(qvec_nvm)
    
    # temp.translation=[T[0][3],T[1][3],T[2][3]]
    # temp.rotation=[qvec_nvm]
    # rate = rospy.Rate(10)
    # while not rospy.is_shutdown():
    #     rospy.loginfo(temp)
    #     pub.publish(temp)
    #     rate.sleep()
    rate = rospy.Rate(10)
    while not rospy.is_shutdown():
        rospy.loginfo(temp)
        pub.publish(temp)
        rate.sleep()
        return


def draw_registration_result(source, target, transformation):
    source_temp = copy.deepcopy(source)
    target_temp = copy.deepcopy(target)
    source_temp.paint_uniform_color([1, 0.706, 0])
    target_temp.paint_uniform_color([0, 0.651, 0.929])
    mesh = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.08)
    source_temp.transform(transformation)
    # print(np.matmul(A, transformation))
    talker2(T)
    # o3d.visualization.draw_geometries([source_temp,mesh, target_temp])
    return

def check(source, target, transformation):
    global T
    global rm
    evaluation1 = o3d.pipelines.registration.evaluate_registration(source, target, 1, transformation)
    if evaluation1.inlier_rmse < rm:
        rm = evaluation1.inlier_rmse
        T = transformation
        print(rm)

#降采样,估计法线,对每个点计算FPFH特征
def preprocess_point_cloud(pcd, voxel_size):
    pcd_down = pcd.voxel_down_sample(voxel_size)
    radius_normal = voxel_size * 2
    pcd_down.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=radius_normal, max_nn=30))
    radius_feature = voxel_size * 4
    pcd_fpfh = o3d.pipelines.registration.compute_fpfh_feature(pcd_down,o3d.geometry.KDTreeSearchParamHybrid(radius=radius_feature, max_nn=100))
    return pcd_down, pcd_fpfh

def prepare_dataset(voxel_size):
    source = o3d.io.read_point_cloud("out/UpModel.ply")
    target = o3d.io.read_point_cloud("out/clear.pcd")
    #source = copy.deepcopy(source).translate((-0.82, 0.85, 0.28))
    trans_init =np.identity(4)

    source.transform(trans_init)
    source_down, source_fpfh = preprocess_point_cloud(source, voxel_size)
    target_down, target_fpfh = preprocess_point_cloud1(target, voxel_size)
    return source, target, source_down, target_down, source_fpfh, target_fpfh

#CorrespondenceCheckerBasedOnDistance检查对应的点云是否接近(也就是距离是否小于指定阈值)
#CorrespondenceCheckerBasedOnEdgeLength检查从源点云和目标点云对应中分别画上两条任意边(两个顶点连成的线)是否近似
#CorrespondenceCheckerBasedOnNormal考虑的所有的对应的顶点法线的密切关系.他计算了两个法线向量的点积.使用弧度作为阈值
def execute_global_registration(source_down, target_down, source_fpfh,target_fpfh, voxel_size):
    distance_threshold = voxel_size * 0.2
    result = o3d.pipelines.registration.registration_ransac_based_on_feature_matching(
        source_down, target_down, source_fpfh, target_fpfh, distance_threshold,
        o3d.pipelines.registration.TransformationEstimationPointToPoint(False), 4, [
            o3d.pipelines.registration.CorrespondenceCheckerBasedOnEdgeLength(0.9),
            o3d.pipelines.registration.CorrespondenceCheckerBasedOnDistance(distance_threshold)], o3d.pipelines.registration.RANSACConvergenceCriteria(4000000, 500))
    return result

def execute_fast_global_registration(source_down, target_down, source_fpfh,target_fpfh, voxel_size):
    distance_threshold = voxel_size * 0.5
    result = o3d.pipelines.registration.registration_fast_based_on_feature_matching(
        source_down, target_down, source_fpfh, target_fpfh,
        o3d.pipelines.registration.FastGlobalRegistrationOption(maximum_correspondence_distance=distance_threshold))
    return result


if __name__ == "__main__":

    distance=0
    while distance==0:

        rospy.init_node('talker', anonymous=True)
        start = time.time()
        os.system('./PointCloud')
        print("拍照用时 %.3f 秒." % (time.time() - start))    

        pcd = o3d.io.read_point_cloud("out/0.ply")
        pcd_down = pcd.voxel_down_sample(voxel_size=0.005)

        points = np.asarray(pcd_down.points)
        pcd_down = pcd_down.select_by_index(np.where(points[:, 0] > 0.1)[0])

        plane_model, inliers = pcd_down.segment_plane(distance_threshold=0.01, ransac_n=3, num_iterations=1000)
        [a, b, c, d] = plane_model
        print(f"Plane equation: {a:.5f}x + {b:.5f}y + {c:.5f}z + {d:.5f} = 0")

        inlier_cloud = pcd_down.select_by_index(inliers)
        inlier_cloud.paint_uniform_color([1.0, 0, 0])
        outlier_cloud = pcd_down.select_by_index(inliers, invert=True)

        #删除平面外的点
        points = np.asarray(outlier_cloud.points)
        mask = a*points[:, 0] + b*points[:, 1] + c*points[:, 2] + d < 0
        outlier_cloud.points = o3d.utility.Vector3dVector(points[mask])

        # 半径离群值移除
        cl, ind = outlier_cloud.remove_radius_outlier(nb_points=12, radius=0.02)
        outlier_remove = outlier_cloud.select_by_index(ind)

        # 基于密度的DBSCAN聚类
        with o3d.utility.VerbosityContextManager(o3d.utility.VerbosityLevel.Debug) as cm:
            labels = np.array(outlier_remove.cluster_dbscan(eps=0.05, min_points=20, print_progress=True))
        max_label = labels.max()
        #print(f"point cloud has {max_label + 1} clusters")
        colors = plt.get_cmap("tab20")(labels / (max_label if max_label > 0 else 1))
        colors[labels < 0] = 0
        outlier_remove.colors = o3d.utility.Vector3dVector(colors[:, :3])

        label = np.array(labels)
        outlier_remove = outlier_remove.select_by_index(np.where(label[:] <= int(max_label/2))[0]+1)

        mesh = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.2)
        o3d.io.write_point_cloud('out/clear.pcd', outlier_remove)

        i = 0
        while ( i < 3):
            i+=1
            key = cv2.waitKey(150)
            threshold =0.005
            voxel_size = 0.005 # means 0.5cm for this dataset
            source, target, source_down, target_down, source_fpfh, target_fpfh = prepare_dataset(voxel_size)

            result_ransac = execute_fast_global_registration(source_down, target_down,source_fpfh, target_fpfh,voxel_size)
            check(source_down, target_down, result_ransac.transformation)

            reg_p2p = o3d.pipelines.registration.registration_icp(source_down, target_down, threshold, result_ransac.transformation,
                o3d.pipelines.registration.TransformationEstimationPointToPoint())
            check(source_down, target_down, reg_p2p.transformation)

            reg_p2l = o3d.pipelines.registration.registration_icp(source_down, target_down, threshold, result_ransac.transformation,
            	o3d.pipelines.registration.TransformationEstimationPointToPlane())
            check(source_down, target_down, reg_p2l.transformation)

        print("配准结果得分:", rm)
        print("共用时 %.3f 秒." % (time.time() - start))
        number =0
        draw_registration_result(source_down, target_down, T)
        aa=(a-0.2764)/2
        bb=(b-0.3679)/2
        cc=(c+0.8879)/2
        dd=d+1.6093
        distance=-dd/(math.sqrt(aa*aa+bb*bb+cc*cc))
        if abs(distance) < 0.9:
            print("车车平移距离：",distance)
            talker(distance)








