
# Copyright (C) 2022 RoboticsWare (neopia.uz@gmail.com)
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General
# Public License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330,
# Boston, MA  02111-1307  USA

import cv2
import numpy as np
import mediapipe as mp

# The following import method is recommended instead of directly importing framework.formats.
# This method automatically finds and loads the appropriate protobuf module internally.
NormalizedLandmarkList = mp.solutions.drawing_utils.landmark_pb2.NormalizedLandmarkList
NormalizedLandmark = mp.solutions.drawing_utils.landmark_pb2.NormalizedLandmark

TEXT_COLOR = (255, 0, 0)
LABEL_FONT_SIZE = 1
LABEL_THICKNESS = 2

class AiUtil(object):
    @staticmethod
    # Draws bounding boxes on the input image and return it. And the input image should be BGR.
    def draw_boundingbox(image, detection_result, cpc) -> tuple:
        category_names = []
        coordinates_list = []  # To store the center coordinates
        
        if not detection_result or not hasattr(detection_result, 'detections'):
            return image, category_names, coordinates_list

        for detection in detection_result.detections:
            # Draw bounding_box
            bbox = detection.bounding_box
            start_point = int(bbox.origin_x), int(bbox.origin_y)
            end_point = int(bbox.origin_x + bbox.width), int(bbox.origin_y + bbox.height)
            cv2.rectangle(image, start_point, end_point, TEXT_COLOR, 3)

            # Draw label and score
            category = detection.categories[0]
            category_name = category.category_name
            category_names.append(category_name)
            
            result_text = f"{category_name} ({round(category.score, 2)})"
            text_location = (10 + start_point[0], 20 + start_point[1])
            cv2.putText(image, result_text, text_location, cv2.FONT_HERSHEY_PLAIN,
                        1, TEXT_COLOR, 1)
            
            # Draw center point coordinates
            if cpc:
                center_x = int(bbox.origin_x + bbox.width / 2)
                center_y = int(bbox.origin_y + bbox.height / 2)
                center_point = (center_x, center_y)
                coordinates_list.append(center_point)
                cv2.circle(image, center_point, 5, TEXT_COLOR, -1)
                cv2.putText(image, f"({center_x}, {center_y})", (center_x + 10, center_y - 10),
                            cv2.FONT_HERSHEY_PLAIN, 1, TEXT_COLOR, 1)

        return image, category_names, coordinates_list  # But returns only the last detection

    @staticmethod
    def get_handlandmarks(current_frame, detection_result_list):
        category_name = None
        hand_landmarks_proto = None

        # Only first hand is processed even if multiple hands are detected
        if not detection_result_list.hand_landmarks:
            return None, None

        for hand_index, hand_landmarks in enumerate(detection_result_list.hand_landmarks):
            # Create landmark list
            hand_landmarks_proto = NormalizedLandmarkList()
            for landmark in hand_landmarks:
                hand_landmarks_proto.landmark.add(
                    x=landmark.x, y=landmark.y, z=landmark.z
                )

            # Get gesture name
            if detection_result_list.gestures:
                gesture = detection_result_list.gestures[hand_index]
                category_name = gesture[0].category_name
                score = round(gesture[0].score, 2)
                result_text = f'{category_name} ({score})'

                # --- Decide a position of text ---
                frame_height, frame_width = current_frame.shape[:2]
                # Find the topmost (y_min) coordinate of the hand
                y_min = min([landmark.y for landmark in hand_landmarks])
                x_min = min([landmark.x for landmark in hand_landmarks])
                
                x_min_px = int(x_min * frame_width)
                y_min_px = int(y_min * frame_height)

                # Measure text size (for background box or precise positioning)
                (text_width, text_height), _ = cv2.getTextSize(
                    result_text, cv2.FONT_HERSHEY_DUPLEX, 1, 2
                )

                # If there's no space above the hand, display below it
                text_x = x_min_px
                text_y = y_min_px - 10
                if text_y < 20:  # If it goes beyond the top boundary
                    text_y = y_min_px + text_height + 20

                # Draw the text
                cv2.putText(current_frame, result_text, (text_x, text_y),
                            cv2.FONT_HERSHEY_DUPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

        return hand_landmarks_proto, category_name