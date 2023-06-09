#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
import cv2
from cv_bridge import CvBridge, CvBridgeError
import numpy as np
import sys
import tf2_ros
import tf2_geometry_msgs
from geometry_msgs.msg import PoseStamped, Point, Pose, Quaternion, TransformStamped
from std_msgs.msg import Header
#from pose_msgs.msg import poseDictionaryMsg

# Importa a biblioteca ArUco
import cv2.aruco as aruco

calib_data_path = "./calib_data/MultiMatrix.npz"

calib_data = np.load(calib_data_path)
print(calib_data.files)

cam_mat = calib_data["camMatrix"]
dist_coef = calib_data["distCoef"]
r_vectors = calib_data["rVector"]
t_vectors = calib_data["tVector"]

# Define o ID dos ArUcos a serem detectados
aruco_id = 0
MARKER_SIZE = 0.8 # inches / perimetro
class ArUcoDetector(Node):
    def __init__(self):
        super().__init__('aruco_detector')
        
        # receber as imagens da câmera
        self.create_subscription(Image, '/camera_test', self.image_callback, 10)
        self.create_subscription(CameraInfo, '/camera_test_info', self.camera_info_callback, 10)
        
        # receber as informações da câmera
        #self.create_subscription(CameraInfo, '/camera/camera_info', self.camera_info_callback, 10)

        
        # Configura o publicador para publicar a imagem com os ArUcos detectados
        self.image_publisher = self.create_publisher(Image, '/aruco_detector/output_image', 10)
        #self.positionWorld_publisher = self.create_publisher(poseDictionaryMsg, 'robot_pose_topic', 10)

        self.publisher_stamp = self.create_publisher(PoseStamped, 'pose_stamped_topic', 10)
        
        # Inicializa o objeto cv_bridge
        self.bridge = CvBridge()
        
        # Inicializa a matriz de calibração da câmera (será atualizada na callback de informações da câmera)
        #self.position_tf_publisher = tf2_ros.Transform


        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        arucoDicts = {
            "DICT_4X4_50": aruco.DICT_4X4_50,
            "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
            "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
            "DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,
            "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
            "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
            "DICT_5X5_250": cv2.aruco.DICT_5X5_250,
            "DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,
            "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
            "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
            "DICT_6X6_250": cv2.aruco.DICT_6X6_250,
            "DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,
            "DICT_7X7_50": cv2.aruco.DICT_7X7_50,
            "DICT_7X7_100": cv2.aruco.DICT_7X7_100,
            "DICT_7X7_250": cv2.aruco.DICT_7X7_250,
            "DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,
            "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL
            }
        aruco_type = "DICT_4X4_1000"
        self.aruco_dict = cv2.aruco.Dictionary_get(arucoDicts[aruco_type])
        self.parameters = aruco.DetectorParameters_create()

    def image_callback(self, msg : Image):
        print('asfas', msg.height)
        print('asfas1', msg.width)
        # Converte a imagem ROS em uma imagem OpenCV
        print('aqui')
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
             # Converte a imagem para tons de fe(self.cv_image_pixel.copy(), (500, 400), interpolation = cv2.INTER_AREA))
            # cv2.imwrite(dirPath + '/pixel_test.png', cv2.resize(self.cv_image_pixel.copy(), (500, 400), interpolation = cv2.INTER_AREA))
            cv2.waitKey(3)
        except CvBridgeError as e:
            print(e)
        
        # Inicializa o detector de ArUcos com as configurações padrão

        
        
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        # Detecta os ArUcos na imagem
        marker_corners, ids, rejected_img_points = aruco.detectMarkers(gray, self.aruco_dict, parameters=self.parameters)
        
        # Se pelo menos um ArUco for detectado
        if ids is not None:
            # Procura o ArUco com o ID especificado
            index = np.where(ids == aruco_id)[0]
            #print("oi")

            if marker_corners:
                rVec, tVec, _ = aruco.estimatePoseSingleMarkers(
                marker_corners, MARKER_SIZE, cam_mat, dist_coef
                )
                total_markers = range(0, ids.size)

                print('cheguei aqui', rVec, tVec)
            
            dictPose = {}
            if len(index) > 0:
                print("oi")
                aruco_pos_robot = []
                for i in range(ids.size):

                    #print("for pos")
                    aruco_pos_cam = Point()
                    aruco_pos_cam.x, aruco_pos_cam.y, aruco_pos_cam.z = tVec[i][0][0], tVec[i][0][1], tVec[i][0][2]
                    aruco_ori = Quaternion()
                    aruco_ori.w = 1.    
                    #print(aruco_pos_cam)
                    print('-------')
                    
                    aruco_pos_robot.append(PoseStamped(
                                                        header=Header(
                                                            # seq=msg.header.seq,
                                                            stamp=msg.header.stamp,
                                                            frame_id=msg.header.frame_id
                                                        ),
                                                        pose=Pose(
                                                            position=aruco_pos_cam,
                                                            orientation=aruco_ori
                                                        )
                                                    ))
                # print(frame_id)
                 #   try:
                        #transform_stamped = self.tf_buffer.lookup_transform('odom_demo', 'chassibigga', rclpy.time.Time())
                        #aruco_position_world = tf2_geometry_msgs.do_transform_point(
                        #    tf2_geometry_msgs.PointStamped(
                        #        header=transform_stamped.header,
                        #        point=aruco_pos_cam
                        #),
                        #transform_stamped
                #)
                  #  except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException):
                   #     pass
                
                print('aa')
                #robotWorld = aruco_position_world/aruco_pos_cam
                #print('aruco_position_world', transform_stamped)
                #print('robotWorld', robotWorld)
                # Desenha o contorno do ArUco encontrado
                for ids, corners, i in zip(ids, marker_corners, total_markers):
                    print("to aq")
                    cv2.polylines(
                        cv_image, [corners.astype(np.int32)], True, (0, 255, 0), 2, cv2.LINE_AA
                    )
                    corners = corners.reshape(4, 2)
                    corners = corners.astype(int)
                    top_right = tuple(corners[0].ravel())
                    top_left = tuple(corners[1].ravel())
                    bottom_right = tuple(corners[2].ravel())
                    bottom_left = tuple(corners[3].ravel())

                    #calcula a distancia.
                    distance = np.sqrt(
                        tVec[i][0][2] ** 2 + tVec[i][0][0] ** 2 + tVec[i][0][1] ** 2
                    )
                    #print(distance)

                    point = cv2.drawFrameAxes(cv_image, cam_mat, dist_coef, rVec[i], tVec[i], 4, 4)
                    cv2.putText(
                        cv_image,
                        f"id: {ids[0]} Dist: {round(distance, 2)}",
                        top_left,
                        cv2.FONT_HERSHEY_PLAIN,
                        2,
                        (255, 0, 0),
                        2,
                        cv2.LINE_AA,
                    )
                    cv2.putText(
                        cv_image,
                        f"x:{round(tVec[i][0][0],1)} y: {round(tVec[i][0][1],1)} ",
                        top_right,
                        cv2.FONT_HERSHEY_PLAIN,
                        2,
                        (0, 0, 255),
                        2,
                        cv2.LINE_AA,
                    )

                    dictPose[aruco_id] = aruco_pos_cam
                
                # Publica a imagem com os ArUcos detectados
                output_msg = self.bridge.cv2_to_imgmsg(cv_image, encoding='bgr8')
                self.image_publisher.publish(output_msg)

                try:
                    cv2.imshow("O(t)_output", cv2.resize(cv_image, (500, 400), interpolation = cv2.INTER_AREA))
                    # cv2.imwrite(dirPath + '/pixel_test.png', cv2.resize(self.cv_image_pixel.copy(), (500, 400), interpolation = cv2.INTER_AREA))
                    cv2.waitKey(3)
                except CvBridgeError as e:
                    print(e)

    def camera_info_callback(self, msg : CameraInfo):
        # Atualiza a matriz de calibração da câmera
        self.cam_mat = np.array(msg.k).reshape((3, 3))
        self.dist_coef = np.array(msg.d)
        
def main(args=None):
    print('hello')
    rclpy.init(args=args)

    # Cria o nó do detector de ArUcos
    aruco_detector = ArUcoDetector()
    while rclpy.ok():
        rclpy.spin_once(aruco_detector)
    # Encerra o programa caso o usuário pressione Ctrl+C
    aruco_detector.destroy_node()
    rclpy.shutdown()
        
if __name__ == '__main__':
	main()