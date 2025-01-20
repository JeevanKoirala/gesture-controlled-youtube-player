import cv2
import mediapipe as mp
import pyautogui
import time
import numpy as np

class YouTubeGestureController:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            max_num_hands=1
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.cap = cv2.VideoCapture(0)
        self.prev_gesture = None
        self.gesture_cooldown = 0.5
        self.last_gesture_time = time.time()
        self.prev_positions = []
        self.swipe_threshold = 0.15
        self.swipe_frames = 5



    def finger_is_bent(self, finger_tip, finger_pip, finger_mcp, threshold=0.07):
        return finger_tip.y > finger_pip.y and abs(finger_tip.x - finger_mcp.x) < threshold
    



    def fingers_touching(self, point1, point2, threshold=0.05):
        return (abs(point1.x - point2.x) < threshold and 
                abs(point1.y - point2.y) < threshold)

    def detect_swipe(self, hand_landmarks):
        wrist = hand_landmarks.landmark[0]
        self.prev_positions.append((wrist.x, wrist.y))
        if len(self.prev_positions) > self.swipe_frames:
            self.prev_positions.pop(0)


            
        if len(self.prev_positions) == self.swipe_frames:
            y_movement = self.prev_positions[-1][1] - self.prev_positions[0][1]
            if abs(y_movement) > self.swipe_threshold:
                return "previous_video" if y_movement < 0 else "next_video"
        return None

    def detect_gesture(self, hand_landmarks):
        landmarks = hand_landmarks.landmark
        
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]

        
        index_pip = landmarks[6]
        middle_pip = landmarks[10]
        ring_pip = landmarks[14]
        pinky_pip = landmarks[18]



        
        index_mcp = landmarks[5]
        middle_mcp = landmarks[9]
        ring_mcp = landmarks[13]
        pinky_mcp = landmarks[17]



        if self.fingers_touching(pinky_tip, thumb_tip, 0.05):
            return "mute"

        all_fingers_down = (
            self.finger_is_bent(index_tip, index_pip, index_mcp) and
            self.finger_is_bent(middle_tip, middle_pip, middle_mcp) and
            self.finger_is_bent(ring_tip, ring_pip, ring_mcp) and
            self.finger_is_bent(pinky_tip, pinky_pip, pinky_mcp)
        )
        if all_fingers_down:
            return "play_pause"
        


        index_up = not self.finger_is_bent(index_tip, index_pip, index_mcp)
        others_down = (
            self.finger_is_bent(middle_tip, middle_pip, middle_mcp) and
            self.finger_is_bent(ring_tip, ring_pip, ring_mcp) and
            self.finger_is_bent(pinky_tip, pinky_pip, pinky_mcp)
        )

        if index_up and others_down:
            return "volume_down"

        index_middle_up = (
            not self.finger_is_bent(index_tip, index_pip, index_mcp) and
            not self.finger_is_bent(middle_tip, middle_pip, middle_mcp) and
            self.finger_is_bent(ring_tip, ring_pip, ring_mcp) and
            self.finger_is_bent(pinky_tip, pinky_pip, pinky_mcp)
        )


        if index_middle_up:
            return "volume_up"

        swipe_gesture = self.detect_swipe(hand_landmarks)
        if swipe_gesture:
            return swipe_gesture

        return None

    def execute_action(self, gesture):
        current_time = time.time()
        if gesture and (gesture != self.prev_gesture or 
                       current_time - self.last_gesture_time > self.gesture_cooldown):
            
            self.prev_gesture = gesture
            self.last_gesture_time = current_time
            
            try:
                if gesture == "play_pause":
                    pyautogui.press('k')
                    print("Play/Pause")
                elif gesture == "volume_up":
                    pyautogui.press('up')
                    print("Volume Up")
                elif gesture == "volume_down":
                    pyautogui.press('down')
                    print("Volume Down")
                elif gesture == "next_video":
                    pyautogui.hotkey('shift', 'n')
                    print("Next Video")
                elif gesture == "previous_video":
                    pyautogui.hotkey('shift', 'p')
                    print("Previous Video")
                elif gesture == "mute":
                    pyautogui.press('m')
                    print("Mute")
            except Exception as e:
                print(f"Failed to execute {gesture}: {str(e)}")



    def display_controls(self, frame):
        controls = {
            "Pinky + Thumb Touch": "Mute",
            "All Fingers Down": "Play/Pause",
            "Index Only": "Volume Down",
            "Index + Middle": "Volume Up",
            "Swipe Up": "Previous Video",
            "Swipe Down": "Next Video"
        }
        
        y_pos = 30
        for gesture, action in controls.items():
            cv2.putText(frame, f"{gesture}: {action}", (10, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            y_pos += 30



    def run(self):
        print("YouTube Gesture Control System Started")
        print("Make sure YouTube is open and in focus")
        print("Press 'Q' to quit")
        
        try:
            while self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret:
                    break

                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb_frame)

                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        self.mp_draw.draw_landmarks(frame, hand_landmarks, 
                                                 self.mp_hands.HAND_CONNECTIONS)
                        gesture = self.detect_gesture(hand_landmarks)
                        self.execute_action(gesture)

                self.display_controls(frame)
                cv2.imshow('YouTube Gesture Control', frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            self.cap.release()
            cv2.destroyAllWindows()

            

if __name__ == "__main__":
    controller = YouTubeGestureController()
    controller.run()