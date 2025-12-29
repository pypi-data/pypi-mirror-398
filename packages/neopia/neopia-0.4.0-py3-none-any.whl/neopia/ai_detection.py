# Part of the RoboticsWare project - https://roboticsware.uz
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
import speech_recognition as sr
import gtts
import uuid, os, time, atexit, signal
import threading
import playsound3

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from neopia.opencv_camera import Camera
from neopia.ai_util import AiUtil

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


class FaceMeshDetection(Camera):
    def __init__(self):
        super().__init__()
        # DrawingSpec for 0.10.x mediapipe API 
        self.drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True, 
            max_num_faces=1, 
            min_detection_confidence=0.5
        )

    def start_detection(self, just_rtn_frame=False):
        rtn_val = False
        success, frame = self._videoInput.read()
        if not success: return False
        
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # BGR to RGB conversion
        results = self.face_mesh.process(rgb_frame)

        # Draw face mesh landmarks on the image
        if results.multi_face_landmarks:
            rtn_val = True
            for face_landmarks in results.multi_face_landmarks:
                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=mp.solutions.face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=self.drawing_spec,
                    connection_drawing_spec=self.drawing_spec
                )
        # Just return frame
        if just_rtn_frame:
            return frame
        
        cv2.imshow('Face Mesh Detection', frame)
        if cv2.waitKey(1) == 27: os._exit(1)  # ESC pressed
        return rtn_val

class FaceDetection(Camera):
    def __init__(self):
        super().__init__()
        # 0.10.x mediapipe Task API
        model_path = os.path.join(os.path.dirname(__file__), 'model', 'face_detector.tflite')
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceDetectorOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.LIVE_STREAM,
            result_callback=self._visualize_callback
        )
        self._detector = vision.FaceDetector.create_from_options(options)
        self._result = None
        self._counter = 0

    def _visualize_callback(self, result, output_image, timestamp_ms):
        self._result = result

    def start_detection(self, just_rtn_frame=False):
        success, frame = self._videoInput.read()
        if not success: return (frame, 0) if just_rtn_frame else 0

        self._counter += 1
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert the frame to RGB
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        self._detector.detect_async(mp_image, int(time.time() * 1000))

        face_count = 0
        if self._result and self._result.detections:
            face_count = len(self._result.detections)
            for detection in self._result.detections:
                # Draw bounding box
                bbox = detection.bounding_box
                start_point = int(bbox.origin_x), int(bbox.origin_y)
                end_point = int(bbox.origin_x + bbox.width), int(bbox.origin_y + bbox.height)
                cv2.rectangle(frame, start_point, end_point, (255, 0, 0), 2)
        
        # Just return frame
        if just_rtn_frame:
            return (frame, face_count)
        
        cv2.imshow('Face Detection', frame)
        if cv2.waitKey(1) == 27: os._exit(1)  # ESC pressed
        return face_count
class PoseDetection(Camera):
    def __init__(self):
        super().__init__()
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose()

    def start_detection(self, just_rtn_frame=False):
        success, frame = self._videoInput.read()
        if not success: return (0, 0)

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # BGR to RGB conversion
        result = self.pose.process(rgb_frame)
        
        coords = (0, 0)
        if result.pose_landmarks:
            nose = result.pose_landmarks.landmark[self.mp_pose.PoseLandmark.NOSE]
            coords = (nose.x * self._width, nose.y * self._height)
            mp_drawing.draw_landmarks(frame, result.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)

        # Just return frame
        if just_rtn_frame:
            return (frame, coords)
        
        cv2.imshow('Pose Detection', frame)
        if cv2.waitKey(1) == 27: os._exit(1)  # ESC pressed
        return coords


class ObjectDetection(Camera):
    def __init__(self, target_fps=30, center_point_xy=False):
        super().__init__()
        # Changed model to ssd_mobilenet_v2 for better performance in low-end systems
        model_path = os.path.join(os.path.dirname(__file__), 'model', 'ssd_mobilenet_v2.tflite')
        
        base_options = python.BaseOptions(model_asset_path=model_path)

        # Choose VIDEO mode for Windows CPU optimization
        options = vision.ObjectDetectorOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO, 
            score_threshold=0.5,
            max_results=3
        )
        self._detector = vision.ObjectDetector.create_from_options(options)
        self.target_fps = target_fps
        self.prev_time = 0
        self.center_point_xy = center_point_xy

    def start_detection(self, just_rtn_frame=False):
        now = time.time()
        # Limiting framerate
        if (now - self.prev_time) < 1.0 / self.target_fps:
            return None

        success, frame = self._videoInput.read()
        if not success: return None
        
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # In VIDEO mode, results are returned immediately without callback
        detection_result = self._detector.detect_for_video(mp_image, int(now * 1000))
        self.prev_time = now

        rtn_data = None
        if detection_result:
            # Draw bounding box using AiUtil
            frame, obj_name, obj_coords = AiUtil.draw_boundingbox(frame, detection_result, self.center_point_xy)
            rtn_data = (obj_name, obj_coords)

        if just_rtn_frame:
            return (frame, rtn_data)
        else:
            cv2.imshow('Object Detection', frame)
            if cv2.waitKey(1) == 27: os._exit(1)  # ESC pressed
        
        return rtn_data
    
class GestureDetection(Camera):
    def __init__(self, target_fps=30):
        super().__init__()
        model_path = os.path.join(os.path.dirname(__file__), 'model', 'gesture_recognizer.task')
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.GestureRecognizerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.LIVE_STREAM,
            result_callback=self._visualize_callback
        )
        self._detector = vision.GestureRecognizer.create_from_options(options)
        self._result = None
        self.target_fps = target_fps
        self.prev_time = 0

    def _visualize_callback(self, result, output_image, timestamp_ms):
        self._result = result

    def start_detection(self, just_rtn_frame=False):
        now = time.time()
        # Limiting framerate
        if (now - self.prev_time) < 1.0 / self.target_fps:
            return (None, None) if just_rtn_frame else None

        success, frame = self._videoInput.read()
        if not success: return (None, None) if just_rtn_frame else None

        frame = cv2.flip(frame, 1)  # Flip the frame horizontally
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # BGR to RGB conversion
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        self._detector.recognize_async(mp_image, int(now * 1000))
        self.prev_time = now

        gesture_name = None
        if self._result:
            # Get landmarks and gesture name using AiUtil
            hand_landmarks_proto, gesture_name = AiUtil.get_handlandmarks(frame, self._result)
            
            if hand_landmarks_proto:
                # Drawing landmarks using Solutions API
                mp.solutions.drawing_utils.draw_landmarks(
                    frame,
                    hand_landmarks_proto,
                    mp.solutions.hands.HAND_CONNECTIONS,
                    mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                    mp.solutions.drawing_styles.get_default_hand_connections_style()
                )

        # Just return frame
        if just_rtn_frame:
            return (frame, gesture_name)
        
        cv2.imshow('Gesture Detection', frame)
        if cv2.waitKey(1) == 27: os._exit(1)   # ESC pressed
        return gesture_name


class QRDetection(Camera):
    def __init__(self):
        super().__init__()
        self._detector = cv2.QRCodeDetector()

    def start_detection(self, just_rtn_frame=False):
        _, frame = self._videoInput.read()
        data, bbox, _ = self._detector.detectAndDecode(frame)

        if bbox is not None:
            bb_pts = bbox.astype(int).reshape(-1, 2)
            num_bb_pts = len(bb_pts)
            for i in range(num_bb_pts):
                cv2.line(frame, tuple(bb_pts[i]), tuple(bb_pts[(i+1) % num_bb_pts]),
                        color=(255, 0, 0), thickness=2)
                cv2.putText(frame, data, (bb_pts[0][0], bb_pts[0][1] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)        
                
        # Just return frame
        if just_rtn_frame:
            return (frame, data)
        else:
            cv2.imshow('QR detection', frame)
            if cv2.waitKey(1) == 27: os._exit(1)  # ESC pressed
        return data

    def __del__(self):
        super().__del__()


class Voice:
    _lock = threading.Lock()
    _temp_files = [] 

    @staticmethod  # Use staticmethod instead of classmethod to avoid an error of registering atexit
    def _cleanup_temp_files(signum=None):
        for fname in Voice._temp_files:
            if os.path.exists(fname):
                os.remove(fname)
        Voice._temp_files.clear()

        # Exit this process normally if a signal is received
        if signum is not None:
            os._exit(1)

    @staticmethod
    def stt(audioId=0, language='uz-UZ'):
        r = sr.Recognizer()
        with sr.Microphone(device_index=audioId) as source:
            r.adjust_for_ambient_noise(source)
            try:
                audio = r.listen(source, timeout=3)
                return r.recognize_google(audio, language=language)
            except:
                return False
    
    @staticmethod
    def tts(text, lang='en'):
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        try:
            gtts.gTTS(text=text, lang=lang).save(filename)
            Voice._temp_files.append(filename)
            playsound3.playsound(filename)
        except Exception as e:
            print(f"TTS Error: {e}")
        finally:
            if os.path.exists(filename):
                os.remove(filename)
                if filename in Voice._temp_files:
                    Voice._temp_files.remove(filename)

    @staticmethod
    def playsound(fname):
        def run():
            with Voice._lock:
                playsound3.playsound(fname)
        threading.Thread(target=run, daemon=True).start()

# In case unexpected termination, register cleanup events
atexit.register(Voice._cleanup_temp_files)
# In case Ctrl+C (SIGINT) or Force Exit (SIGTERM)
signal.signal(signal.SIGINT, Voice._cleanup_temp_files)
signal.signal(signal.SIGTERM, Voice._cleanup_temp_files)