import os
import numpy as np
import pandas as pd
import cv2
from deepface import DeepFace
from deepface.commons import functions
from deepface.commons.logger import Logger
from .face_models import Vit

logger = Logger(module="commons.realtime")

# dependency configuration
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# pylint: disable=too-many-nested-blocks


def face_center(face):
    x, y, w, h = face
    return x + w // 2, y + h // 2

# Function to calculate Euclidean distance between two points
def distance(point1, point2):
    return np.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)
    
def horizontal_distance(x1,x2):
    return abs(x1-x2)

def analysis(
    db_path,
    find_similar_face=False,
    model_name="VGG-Face",
    detector_backend="opencv",
    distance_metric="cosine",
    enable_face_analysis=True,
    source=0,
    output_file="test_out.mp4",
):
    # global variables
    text_color = (255, 255, 255)
    pivot_img_size = 112  # face recognition result image

    enable_emotion = True
    enable_age_gender = True
    

    if enable_face_analysis:
        DeepFace.build_model(model_name="Age")
        logger.info("Age model is just built")
        DeepFace.build_model(model_name="Gender")
        logger.info("Gender model is just built")
        DeepFace.build_model(model_name="Emotion")
        logger.info("Emotion model is just built")
    # -----------------------
    # call a dummy find function for db_path once to create embeddings in the initialization
    target_size = functions.find_target_size(model_name=model_name)
    if find_similar_face == True:
        # ------------------------
        # find custom values for this input set
        # ------------------------
        # build models once to store them in the memory
        # otherwise, they will be built after cam started and this will cause delays
        DeepFace.build_model(model_name=model_name)
        logger.info(f"facial recognition model {model_name} is just built")

        DeepFace.find(
        img_path=np.zeros([224, 224, 3]),
        db_path=db_path,
        model_name=model_name,
        detector_backend=detector_backend,
        distance_metric=distance_metric,
        enforce_detection=False,
    )
    
    face_detected = False

    cap = cv2.VideoCapture(source)  # webcam or videe

    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_size = (frame_width, frame_height)
    
    fourcc = cv2.VideoWriter_fourcc(*'MP4V')
    out = cv2.VideoWriter(output_file, fourcc, frame_rate, frame_size)

    frames = []
    while True:
        _, img = cap.read()

        if img is None:
            break

        raw_img = img.copy()
        resolution_x = img.shape[1]
        resolution_y = img.shape[0]

        height, width, _ = img.shape
        center_x, center_y = width // 2, height // 2

        try:
            # just extract the regions to highlight in webcam
            face_objs = DeepFace.extract_faces(
                img_path=img,
                target_size=target_size,
                detector_backend=detector_backend,
                enforce_detection=False,
            )
            faces = []
            closest_face = None
            min_distance = float('inf')
            for face_obj in face_objs:
                facial_area = face_obj["facial_area"]
                confidence = face_obj["confidence"]
                if confidence > 0: 
                    face_location = (
                            facial_area["x"],
                            facial_area["y"],
                            facial_area["w"],
                            facial_area["h"],
                        )
                    face_center_point = face_center(face_location)
                    dist = distance(face_center_point, (center_x, center_y))
                    horizontal_dist = horizontal_distance(face_center_point[0],center_x)
                    if dist < min_distance and horizontal_dist<(1/4*width):
                        min_distance = dist
                        closest_face = face_location
                    faces.append(face_location)
        except:  # to avoid exception if no face detected
            faces = []
        
        detected_faces = []
        face_index = 0
        for x, y, w, h in faces:
            #print(x,y,w,h)
            if w > 10:
                face_detected = True
                cv2.rectangle(
                    img, (x, y), (x + w, y + h), (67, 67, 67), 1
                )  # draw rectangle to main image
                if (x,y,w,h) == closest_face:
                    cv2.putText(
                    img,
                    str("Main Speaker"),
                    (int(x + w / 4), int(y + h / 1.5)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    4,
                    (255, 255, 255),
                    2,
                )
                else:
                    cv2.putText(
                        img,
                        str(face_index),
                        (int(x + w / 4), int(y + h / 1.5)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        4,
                        (255, 255, 255),
                        2,
                    )

                detected_face = img[int(y) : int(y + h), int(x) : int(x + w)]  # crop detected face

                # -------------------------------------

                detected_faces.append((x, y, w, h))
                face_index = face_index + 1

        if face_detected == True:
            base_img = raw_img.copy()
            detected_faces_final = detected_faces.copy()
            freeze_img = base_img.copy()
            for detected_face in detected_faces_final:
                x = detected_face[0]
                y = detected_face[1]
                w = detected_face[2]
                h = detected_face[3]

                cv2.rectangle(
                    freeze_img, (x, y), (x + w, y + h), (67, 67, 67), 1
                )  # draw rectangle to main image
  
                # -------------------------------
                # extract detected face
                custom_face = base_img[y : y + h, x : x + w]
                # -------------------------------
                # facial attribute analysis

                if enable_face_analysis == True:

                    demographies = DeepFace.analyze(
                        img_path=custom_face,
                        detector_backend=detector_backend,
                        enforce_detection=False,
                        silent=True,
                    )

                    if len(demographies) > 0:
                        # directly access 1st face cos img is extracted already
                        demography = demographies[0]

                        if enable_emotion:
                            emotion_model = Vit()
                            emotion_dic = emotion_model.raw_emotion(custom_face)
                            emotion = emotion_dic
                            emotion_df = pd.DataFrame(
                                emotion.items(), columns=["emotion", "score"]
                            )
                            emotion_df['score'] = emotion_df['score'] * 100
                            emotion_df = emotion_df.sort_values(
                                by=["score"], ascending=False
                            ).reset_index(drop=True)

                            # background of mood box

                            # transparency
                            overlay = freeze_img.copy()
                            opacity = 0.4

                            if x + w + pivot_img_size < resolution_x:
                                # right
                                cv2.rectangle(
                                    freeze_img
                                    # , (x+w,y+20)
                                    ,
                                    (x + w, y),
                                    (x + w + pivot_img_size, y + h),
                                    (64, 64, 64),
                                    cv2.FILLED,
                                )

                                cv2.addWeighted(
                                    overlay, opacity, freeze_img, 1 - opacity, 0, freeze_img
                                )

                            elif x - pivot_img_size > 0:
                                # left
                                cv2.rectangle(
                                    freeze_img
                                    # , (x-pivot_img_size,y+20)
                                    ,
                                    (x - pivot_img_size, y),
                                    (x, y + h),
                                    (64, 64, 64),
                                    cv2.FILLED,
                                )

                                cv2.addWeighted(
                                    overlay, opacity, freeze_img, 1 - opacity, 0, freeze_img
                                )

                            for index, instance in emotion_df.iterrows():
                                current_emotion = instance["emotion"]
                                emotion_label = f"{current_emotion} "
                                emotion_score = instance["score"] / 100

                                bar_x = 35  # this is the size if an emotion is 100%
                                bar_x = int(bar_x * emotion_score)

                                if x + w + pivot_img_size < resolution_x:

                                    text_location_y = y + 20 + (index + 1) * 20
                                    text_location_x = x + w

                                    if text_location_y < y + h:
                                        cv2.putText(
                                            freeze_img,
                                            emotion_label,
                                            (text_location_x, text_location_y),
                                            cv2.FONT_HERSHEY_SIMPLEX,
                                            0.5,
                                            (255, 255, 255),
                                            1,
                                        )

                                        cv2.rectangle(
                                            freeze_img,
                                            (x + w + 70, y + 13 + (index + 1) * 20),
                                            (
                                                x + w + 70 + bar_x,
                                                y + 13 + (index + 1) * 20 + 5,
                                            ),
                                            (255, 255, 255),
                                            cv2.FILLED,
                                        )

                                elif x - pivot_img_size > 0:

                                    text_location_y = y + 20 + (index + 1) * 20
                                    text_location_x = x - pivot_img_size

                                    if text_location_y <= y + h:
                                        cv2.putText(
                                            freeze_img,
                                            emotion_label,
                                            (text_location_x, text_location_y),
                                            cv2.FONT_HERSHEY_SIMPLEX,
                                            0.5,
                                            (255, 255, 255),
                                            1,
                                        )

                                        cv2.rectangle(
                                            freeze_img,
                                            (
                                                x - pivot_img_size + 70,
                                                y + 13 + (index + 1) * 20,
                                            ),
                                            (
                                                x - pivot_img_size + 70 + bar_x,
                                                y + 13 + (index + 1) * 20 + 5,
                                            ),
                                            (255, 255, 255),
                                            cv2.FILLED,
                                        )

                        if enable_age_gender:
                            apparent_age = demography["age"]
                            dominant_gender = demography["dominant_gender"]
                            gender = "M" if dominant_gender == "Man" else "W"
                            logger.debug(f"{apparent_age} years old {dominant_gender}")
                            analysis_report = str(int(apparent_age)) + " " + gender

                            # -------------------------------
                            if (x,y,w,h) == closest_face:
                                info_box_color = (0, 0, 255)
                            else:
                                info_box_color = (46, 200, 255)

                            # top
                            if y - pivot_img_size + int(pivot_img_size / 5) > 0:

                                triangle_coordinates = np.array(
                                    [
                                        (x + int(w / 2), y),
                                        (
                                            x + int(w / 2) - int(w / 10),
                                            y - int(pivot_img_size / 3),
                                        ),
                                        (
                                            x + int(w / 2) + int(w / 10),
                                            y - int(pivot_img_size / 3),
                                        ),
                                    ]
                                )

                                cv2.drawContours(
                                    freeze_img,
                                    [triangle_coordinates],
                                    0,
                                    info_box_color,
                                    -1,
                                )

                                cv2.rectangle(
                                    freeze_img,
                                    (
                                        x + int(w / 5),
                                        y - pivot_img_size + int(pivot_img_size / 5),
                                    ),
                                    (x + w - int(w / 5), y - int(pivot_img_size / 3)),
                                    info_box_color,
                                    cv2.FILLED,
                                )

                                cv2.putText(
                                    freeze_img,
                                    analysis_report,
                                    (x + int(w / 3.5), y - int(pivot_img_size / 2.1)),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    1,
                                    (0, 111, 255),
                                    2,
                                )

                            # bottom
                            elif (
                                y + h + pivot_img_size - int(pivot_img_size / 5)
                                < resolution_y
                            ):

                                triangle_coordinates = np.array(
                                    [
                                        (x + int(w / 2), y + h),
                                        (
                                            x + int(w / 2) - int(w / 10),
                                            y + h + int(pivot_img_size / 3),
                                        ),
                                        (
                                            x + int(w / 2) + int(w / 10),
                                            y + h + int(pivot_img_size / 3),
                                        ),
                                    ]
                                )

                                cv2.drawContours(
                                    freeze_img,
                                    [triangle_coordinates],
                                    0,
                                    info_box_color,
                                    -1,
                                )

                                cv2.rectangle(
                                    freeze_img,
                                    (x + int(w / 5), y + h + int(pivot_img_size / 3)),
                                    (
                                        x + w - int(w / 5),
                                        y + h + pivot_img_size - int(pivot_img_size / 5),
                                    ),
                                    info_box_color,
                                    cv2.FILLED,
                                )

                                cv2.putText(
                                    freeze_img,
                                    analysis_report,
                                    (x + int(w / 3.5), y + h + int(pivot_img_size / 1.5)),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    1,
                                    (0, 111, 255),
                                    2,
                                )

                # --------------------------------
                # face recognition
                # call find function for custom_face
                if find_similar_face == True:
                    dfs = DeepFace.find(
                        img_path=custom_face,
                        db_path=db_path,
                        model_name=model_name,
                        detector_backend=detector_backend,
                        distance_metric=distance_metric,
                        enforce_detection=False,
                        silent=True,
                    )

                    if len(dfs) > 0:
                        # directly access 1st item because custom face is extracted already
                        df = dfs[0]

                        if df.shape[0] > 0:
                            candidate = df.iloc[0]
                            label = candidate["identity"]

                            # to use this source image as is
                            display_img = cv2.imread(label)
                            # to use extracted face
                            source_objs = DeepFace.extract_faces(
                                img_path=label,
                                target_size=(pivot_img_size, pivot_img_size),
                                detector_backend=detector_backend,
                                enforce_detection=False,
                                align=False,
                            )

                            if len(source_objs) > 0:
                                # extract 1st item directly
                                source_obj = source_objs[0]
                                display_img = source_obj["face"]
                                display_img *= 255
                                display_img = display_img[:, :, ::-1]
                            # --------------------
                            label = label.split("/")[-1]

                            try:
                                if (
                                    y - pivot_img_size > 0
                                    and x + w + pivot_img_size < resolution_x
                                ):
                                    # top right
                                    freeze_img[
                                        y - pivot_img_size : y,
                                        x + w : x + w + pivot_img_size,
                                    ] = display_img

                                    overlay = freeze_img.copy()
                                    opacity = 0.4
                                    cv2.rectangle(
                                        freeze_img,
                                        (x + w, y),
                                        (x + w + pivot_img_size, y + 20),
                                        (46, 200, 255),
                                        cv2.FILLED,
                                    )
                                    cv2.addWeighted(
                                        overlay,
                                        opacity,
                                        freeze_img,
                                        1 - opacity,
                                        0,
                                        freeze_img,
                                    )

                                    cv2.putText(
                                        freeze_img,
                                        label,
                                        (x + w, y + 10),
                                        cv2.FONT_HERSHEY_SIMPLEX,
                                        0.5,
                                        text_color,
                                        1,
                                    )

                                    # connect face and text
                                    cv2.line(
                                        freeze_img,
                                        (x + int(w / 2), y),
                                        (x + 3 * int(w / 4), y - int(pivot_img_size / 2)),
                                        (67, 67, 67),
                                        1,
                                    )
                                    cv2.line(
                                        freeze_img,
                                        (x + 3 * int(w / 4), y - int(pivot_img_size / 2)),
                                        (x + w, y - int(pivot_img_size / 2)),
                                        (67, 67, 67),
                                        1,
                                    )

                                elif (
                                    y + h + pivot_img_size < resolution_y
                                    and x - pivot_img_size > 0
                                ):
                                    # bottom left
                                    freeze_img[
                                        y + h : y + h + pivot_img_size,
                                        x - pivot_img_size : x,
                                    ] = display_img

                                    overlay = freeze_img.copy()
                                    opacity = 0.4
                                    cv2.rectangle(
                                        freeze_img,
                                        (x - pivot_img_size, y + h - 20),
                                        (x, y + h),
                                        (46, 200, 255),
                                        cv2.FILLED,
                                    )
                                    cv2.addWeighted(
                                        overlay,
                                        opacity,
                                        freeze_img,
                                        1 - opacity,
                                        0,
                                        freeze_img,
                                    )

                                    cv2.putText(
                                        freeze_img,
                                        label,
                                        (x - pivot_img_size, y + h - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX,
                                        0.5,
                                        text_color,
                                        1,
                                    )

                                    # connect face and text
                                    cv2.line(
                                        freeze_img,
                                        (x + int(w / 2), y + h),
                                        (
                                            x + int(w / 2) - int(w / 4),
                                            y + h + int(pivot_img_size / 2),
                                        ),
                                        (67, 67, 67),
                                        1,
                                    )
                                    cv2.line(
                                        freeze_img,
                                        (
                                            x + int(w / 2) - int(w / 4),
                                            y + h + int(pivot_img_size / 2),
                                        ),
                                        (x, y + h + int(pivot_img_size / 2)),
                                        (67, 67, 67),
                                        1,
                                    )

                                elif y - pivot_img_size > 0 and x - pivot_img_size > 0:
                                    # top left
                                    freeze_img[
                                        y - pivot_img_size : y, x - pivot_img_size : x
                                    ] = display_img

                                    overlay = freeze_img.copy()
                                    opacity = 0.4
                                    cv2.rectangle(
                                        freeze_img,
                                        (x - pivot_img_size, y),
                                        (x, y + 20),
                                        (46, 200, 255),
                                        cv2.FILLED,
                                    )
                                    cv2.addWeighted(
                                        overlay,
                                        opacity,
                                        freeze_img,
                                        1 - opacity,
                                        0,
                                        freeze_img,
                                    )

                                    cv2.putText(
                                        freeze_img,
                                        label,
                                        (x - pivot_img_size, y + 10),
                                        cv2.FONT_HERSHEY_SIMPLEX,
                                        0.5,
                                        text_color,
                                        1,
                                    )

                                    # connect face and text
                                    cv2.line(
                                        freeze_img,
                                        (x + int(w / 2), y),
                                        (
                                            x + int(w / 2) - int(w / 4),
                                            y - int(pivot_img_size / 2),
                                        ),
                                        (67, 67, 67),
                                        1,
                                    )
                                    cv2.line(
                                        freeze_img,
                                        (
                                            x + int(w / 2) - int(w / 4),
                                            y - int(pivot_img_size / 2),
                                        ),
                                        (x, y - int(pivot_img_size / 2)),
                                        (67, 67, 67),
                                        1,
                                    )

                                elif (
                                    x + w + pivot_img_size < resolution_x
                                    and y + h + pivot_img_size < resolution_y
                                ):
                                    # bottom righ
                                    freeze_img[
                                        y + h : y + h + pivot_img_size,
                                        x + w : x + w + pivot_img_size,
                                    ] = display_img

                                    overlay = freeze_img.copy()
                                    opacity = 0.4
                                    cv2.rectangle(
                                        freeze_img,
                                        (x + w, y + h - 20),
                                        (x + w + pivot_img_size, y + h),
                                        (46, 200, 255),
                                        cv2.FILLED,
                                    )
                                    cv2.addWeighted(
                                        overlay,
                                        opacity,
                                        freeze_img,
                                        1 - opacity,
                                        0,
                                        freeze_img,
                                    )

                                    cv2.putText(
                                        freeze_img,
                                        label,
                                        (x + w, y + h - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX,
                                        0.5,
                                        text_color,
                                        1,
                                    )

                                    # connect face and text
                                    cv2.line(
                                        freeze_img,
                                        (x + int(w / 2), y + h),
                                        (
                                            x + int(w / 2) + int(w / 4),
                                            y + h + int(pivot_img_size / 2),
                                        ),
                                        (67, 67, 67),
                                        1,
                                    )
                                    cv2.line(
                                        freeze_img,
                                        (
                                            x + int(w / 2) + int(w / 4),
                                            y + h + int(pivot_img_size / 2),
                                        ),
                                        (x + w, y + h + int(pivot_img_size / 2)),
                                        (67, 67, 67),
                                        1,
                                    )
                            except Exception as err:  # pylint: disable=broad-except
                                logger.error(str(err))

            #frames.append(freeze_img)
            out.write(freeze_img)
        else:
            #frames.append(img)
            out.write(img)
    
    cap.release()
    
    out.release()
