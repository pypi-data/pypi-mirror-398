from deepface import DeepFace
from deepface.commons import functions
import cv2
import os
from transformers import ViTFeatureExtractor, ViTForImageClassification
import torch
import numpy as np
from torch.nn.functional import softmax
from PIL import Image


def grey2rgb(greyscale_img):
    """
    Convert a PIL greyscale image to RGB by repeating the same channel three times.

    Parameters:
    greyscale_img (PIL.Image): A grayscale image.

    Returns:
    PIL.Image: An RGB image.
    """

    # Convert the grayscale image to a numpy array
    grey_array = np.array(greyscale_img)

    # Check if the image is already in the format with a single channel
    if len(grey_array.shape) == 2:
        # Repeat the grayscale channel three times to create an RGB image
        rgb_array = np.repeat(grey_array[:, :, np.newaxis], 3, axis=2)
    else:
        # If the image is already in a 3-dimensional format, use it as is
        rgb_array = grey_array

    # Convert the numpy array back to a PIL image
    return Image.fromarray(rgb_array)

class Vit(object):
    def __init__(self):
        self.model_dir = "HTIAN/emotion-ViT"
        self.model = ViTForImageClassification.from_pretrained(self.model_dir).to("cuda" if torch.cuda.is_available() else "cpu")
        self.feature_extractor = ViTFeatureExtractor.from_pretrained(self.model_dir)
        pass
    
    def detect_face(self,image_path,all_face=False):
        img_objs = functions.extract_faces(
        img=image_path,
        target_size=(224, 224),
        detector_backend="opencv",
        grayscale=False,
        enforce_detection=False,
        align=True,
    )
        if all_face:
            return img_objs
        max_confidence_index = max(range(len(img_objs)), key=lambda i: img_objs[i][2])
        img_content = img_objs[max_confidence_index][0]
        confidence = img_objs[max_confidence_index][2]
        img_content = (255 * img_content).astype(np.uint8)
        if img_content.shape[0] > 0 and img_content.shape[1] > 0 and confidence>0:
            return img_content[0],True
        
        return None,False
        
        
    def raw_emotion(self,face_img):
        img_gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        test_image = grey2rgb(img_gray)
        inputs = self.feature_extractor(images=test_image, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
        outputs = self.model(**inputs)
        logits = outputs.logits
        probabilities = softmax(logits, dim=-1)[0].tolist()
        labels = self.model.config.id2label.values()
        probabilities_dict = dict(zip(labels, probabilities))

        return probabilities_dict
    


    def get_emotion(self,image_path):
        image, check_val = self.detect_face(image_path)
        if check_val:
            return self.raw_emotion(image)
        else:
            return None



class Customdeepface(object):
    def __init__(self, frame_per_second = 1, *args, **kwargs):
        self.frame_per_second = frame_per_second
        # Additional initialization can go here
    
    def process_video(self, video_path):
        cap = cv2.VideoCapture(video_path)

        # Check if video opened successfully
        if not cap.isOpened():
            print(f"Error opening video file: {os.path.basename(video_path)}")
            return None

        fps = cap.get(cv2.CAP_PROP_FPS)  # Frames per second
        frame_interval = int((1/self.frame_per_second)*fps)  # Capture one frame per second

        success, image = cap.read()
        count = 0
        images = []

        while success:
            if count % frame_interval == 0:
                images.append(image)  # Add frame to list

            success, image = cap.read()
            count += 1

        cap.release()
        return images
    
    def get_video_predictions(self,video_path,detection_backend='opencv',emotion_backend='vit'):
        images = self.process_video(video_path)
        result_lst = []
        if emotion_backend == 'vit':
            model = Vit()
            for img in images:
                result = model.get_emotion(img)
                result_lst.append(result)
        else:
            for img in images:
                result = DeepFace.analyze(img_path = img, detector_backend = detection_backend, enforce_detection=False)
                result_lst.append(result[0])

       
        return result_lst

