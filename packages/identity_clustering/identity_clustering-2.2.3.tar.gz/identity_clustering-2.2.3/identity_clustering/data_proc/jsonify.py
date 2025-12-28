import os
import io
import sys
from contextlib import contextmanager
import json
import yaml
from tqdm import tqdm
import numpy as np
import torch
import cv2
from PIL import Image
from typing import Dict, List, Literal
from torchvision.transforms import PILToTensor, Resize
from identity_clustering.cluster import FaceCluster, cluster, detect_faces
from identity_clustering.utils import _get_frames, get_straight_face

__all__ = ['jsonify']

@contextmanager
def suppress_stdout():
    saved_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        yield
    finally:
        sys.stdout = saved_stdout
def get_video_config(clustered_faces : Dict[int,list], identity : int, identity_dir : str | os.PathLike, filter_straight_face : bool = False, save_format : Literal["jpg", "png", "avi", "mp4"] = "jpg", device : str = "cpu", frame_rate : int = 30)->Dict[str,object]:
    config = {}
    config["ID"] = identity
    config["path"] = identity_dir
    config["class"] = "unassinged"
    exact_crop_dir = os.path.join(identity_dir, "exact_crops")
    if not os.path.exists(exact_crop_dir):
        os.makedirs(exact_crop_dir)
    pil_to_tensor = PILToTensor()
    resize = Resize((512, 512))
    # bboxes = []
    writer_1 = None
    writer_2 = None
    box = {}
    exact_crop_faces_stack = []
    faces_stack = []
    bbox,kps,embed=None,None,None
    for frame, cropped_face, vid_info_bbox, exact_crop in clustered_faces[identity]:
        if not isinstance(vid_info_bbox, list):
            bbox, kps, embed = vid_info_bbox
        else:
            bbox = vid_info_bbox
        if save_format in ["jpg", "png"]:
            if not filter_straight_face or (filter_straight_face and kps and get_straight_face(kps)):
                face_path = os.path.join(identity_dir,f"{frame}.{save_format}")
                # image_cv = cv2.cvtColor(np.array(cropped_face), cv2.COLOR_BGR2RGB)
                # exact_crop = cv2.cvtColor(np.array(exact_crop), cv2.COLOR_BGR2RGB)
                # cropped_face = Image.fromarray(image_cv)
                exact_crop_face_path = os.path.join(exact_crop_dir,f"{frame}.{save_format}")
                # exact_crop = Image.fromarray(exact_crop)
                cropped_face.save(face_path)
                exact_crop.save(exact_crop_face_path)
        elif save_format in ["avi", "mp4"]:
            face_np = resize(pil_to_tensor(cropped_face)).permute(1, 2, 0).cpu().numpy()
            exact_np = resize(pil_to_tensor(exact_crop)).permute(1, 2, 0).cpu().numpy()
            if face_np.ndim == 2:
                face_np = cv2.cvtColor(face_np, cv2.COLOR_GRAY2BGR)
            if exact_np.ndim == 2:
                exact_np = cv2.cvtColor(exact_np, cv2.COLOR_GRAY2BGR)

            face_bgr = cv2.cvtColor(face_np, cv2.COLOR_RGB2BGR)
            exact_bgr = cv2.cvtColor(exact_np, cv2.COLOR_RGB2BGR)

            # Lazily initialize writers using first valid frame
            if writer_1 is None:
                h1, w1 = face_bgr.shape[:2]
                h2, w2 = exact_bgr.shape[:2]

                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer_1 = cv2.VideoWriter(
                    os.path.join(identity_dir, f"{identity}.{save_format}"),
                    fourcc,
                    frame_rate,
                    (w1, h1)
                )
                writer_2 = cv2.VideoWriter(
                    os.path.join(exact_crop_dir, f"{identity}.{save_format}"),
                    fourcc,
                    frame_rate,
                    (w2, h2)
                )

            writer_1.write(face_bgr)
            writer_2.write(exact_bgr)
            # exact_crop_faces_stack.append(pil_to_tensor(exact_crop).to(device))
            # faces_stack.append(pil_to_tensor(cropped_face).to(device))
            
        box[frame] = bbox
        with open(os.path.join(identity_dir,f"{frame}.json"),"w") as f:
            save = {frame:bbox}
            if not kps is None:
                save["kps"] = kps
            json.dump(save,f)
        if (not (embed is None)) and isinstance(embed,np.ndarray) and embed.shape==(512,):
            file = os.path.join(identity_dir,f"{frame}.npy")
            np.save(file,embed)
    config["bboxes"] = box
    # if save_format in ["avi", "mp4"] and False: # remove false after save_format
    #     np.save(np.array(config["bboxes"].keys()), os.path.join(identity_dir,f"{identity}_frames.npy"))
    #     faces_stack = torch.stack(faces_stack)
    #     exact_crop_faces_stack = torch.stack(exact_crop_faces_stack)
    #     encoder = VideoEncoder(faces_stack, frame_rate = frame_rate)
    #     encoder.to_file(os.path.join(identity_dir,f"{identity}.{save_format}"))
    #     encoder = VideoEncoder(exact_crop_faces_stack, frame_rate = frame_rate)
    #     encoder.to_file(os.path.join(exact_crop_dir,f"{identity}_exact_crop.{save_format}"))
    if save_format in ["avi", "mp4"]:
        if writer_1 is not None:
            writer_1.release()
        if writer_2 is not None:
            writer_2.release()
    return config
def jsonify(dataset_root_path: str | os.PathLike, 
            project_name : str,
            save_path : str | os.PathLike,
            save_embed : bool = False,
            filter_straight_face : bool = False,
            save_kps : bool = False,
            save_landmarks : bool = False,
            save_format : Literal["png", "jpg", "avi", "mp4"] = "jpg",
            save_codec : Literal["libx264", "h264", None] = None,
            frame_rate : int = 30,
            padding_constant : int = 3,
            multiplier : int = 2,
            similarity_threshold : float = 0.9,
            max_identities_limit : int = 6,
            device : str = "cpu"):
    '''
        dataset_root_path: str - Path to the videos in the dataset
        project_name: str - Name of the project. This name will be used to create a folder in which all the extracted information will be stored.
        save_path: str - Path to which the generated results will be saved
        save_format : Literal["png", "jpg", "avi", "mp4"] - processed frames can be stored as frames or videos per identity, this is introduced with the torchcodec update made to the identity_clustering package
        save_codec : Literal["libx264", "h264", None] - refers to the video codec to be used while saving the video.
        frame_rate : int - frame rate of the video.
        save_embed : bool - saves arcface (insightface webface_r50.onnx) embeddings of the face.
        save_kps : bool - saves the key landmarks of the face, eyes, nose and the two ends of the mouth
        save_landamrks : bool - saves the 81 face landmark from dlib (exp)
        filter_straight_face : bool - filters straight face i.e. videos with no straight face is dropped (not recomm, always set to False)
        max_identities_limit : int - clustered identities can sometimes exceed the actual identities in the video because of poor model performance, so to cap the number of identities to be saved one can use this. default 6. (recommended)

        Here is the folder structure:
                | PROJECT_NAME
                    | VIDEO 1
                        | IDENTITY 1
                            FRAME_NO.jpg
                            FRAME_NO.jpg
                        | IDENTITY 2
                            FRAME_NO.jpg
                            FRAME_NO.jpg
                        ....
                        ....
                        ....
                        | IDENTITY N
                            FRAME_NO.jpg
                            FRAME_NO.jpg
                        PROJECT_NAME.json
                    ....
                    ....
                    ....
                    | VIDEO N
                        | IDENTITY 1
                            FRAME_NO.jpg
                            FRAME_NO.jpg
                        | IDENTITY 2
                            FRAME_NO.jpg
                            FRAME_NO.jpg
                        ....
                        ....
                        ....
                        | IDENTITY N
                            FRAME_NO.jpg
                            FRAME_NO.jpg
                        PROJECT_NAME.json
    '''
    try:
        '''
            - The dictionary below will follow the template as mentioned in the above markdown cell.
            - It will contain information about the dataset, the videos in the dataset, the extracted identities, the path in which the identities'
              cropped face images will be stored and finally the bounding box information of the faces of each identity in the dataset.
            - The dictionary will ultimately be stored as a JSON file.
        '''
        videos_list = os.listdir(dataset_root_path)
        dataset_json = {}
        dataset_json["root_path"] = dataset_root_path
        dataset_json["project"] = project_name
        '''
            - The below videos array will be a part of dataset_json['videos']. Refer to the videos key in the above markdown.
            - This array will contain all the information about the videos in the dataset. It is an array of objects. Each object will refer to one video in
            the dataset. Inside each object, you'll find information about the path to the video, the fps of the video, and information regarding each
            identity in the video.
            - Intialize the Clustere class for clustering identities.
        '''
        # videos = []
        clust = FaceCluster() # type: ignore
        '''
            Refer to the comment at the start of the function for the folder structure.
            Now let's create a folder in which we will store the JSON file, the cropped faces of each identity in the videos.
            For reference, this folder is the root folder PROJECT_NAME
        '''
        project_path = os.path.join(save_path,project_name)
        if not os.path.exists(project_path):
            os.mkdir(project_path)
        '''
            Now let's go through every video in the dataset and process them to get the identities. Here are the steps:
                1. For each video, extract all the faces in every frame. Store them in an array.
                2. Cluster the faces. Each cluster is an identity, i.e, faces of a person.
                3. Store them in a folder.
            While doing each step, let's log them and also store the required information in the dataset_json
        '''
        error_directory = os.path.join(project_path,"error_logs")
        if not os.path.exists(error_directory):
            os.mkdir(error_directory)
        for video_name in tqdm(sorted(videos_list)):
            try:
                torch.cuda.empty_cache()
                '''
                    video_config: dict - It is a dictionary that goes into the videos array. It contains information about the identities in the video and other
                    meta information about the video. Refer to the object in videos key in the above JSON.
                '''
                video_config = {}
                '''
                    video_name: str - Full path to the video.
                    destination_path: str - path to the folder in which the identities' cropped faces will be stored.
                '''
                video_path = os.path.join(dataset_root_path,video_name)
                destination_path = os.path.join(project_path, video_name)
                ### Create a folder for the video, if the folder exists skip that video
                if not os.path.exists(destination_path):
                    os.mkdir(destination_path)
                else:
                    continue
                video_config["path"] = video_path
                #extract faces
                faces,fps=None,None
                with suppress_stdout():
                    if save_embed and filter_straight_face:
                        faces,fps = detect_faces(video_path,"cuda",v2=True)
                    elif filter_straight_face:
                        faces,fps= detect_faces(video_path,"cuda",v2=True,need_embed=False)
                    elif save_embed:
                        faces,fps= detect_faces(video_path,"cuda",v2=True,need_kps=False)
                    else:
                        faces, fps = detect_faces(video_path, "cuda:0")
                video_config["fps"] = fps
                clustered_faces = cluster(clust, video_path, faces, padding_constant, similarity_threshold, multiplier)
                if len(clustered_faces) > max_identities_limit:
                    continue
                ### Identity means one person in a video (clustered faces)
                '''
                    identities: [
                        {
                            path: str - path to the face crops of a single person,
                            ID: int - a unique number attached to that person,
                            class: str - enum(fake/real)
                        }
                    ]
                '''
                ### Identities is a collection of the faces of all the people in a video
                # Identities = []
                ###
                for identity in list(clustered_faces.keys()):
                    if not clustered_faces[identity]:
                        ### If no faces in a specific cluster
                        continue
                    ### Create a folder for each identity
                    identity_dir = os.path.join(destination_path,str(identity)) ## Stored ad path in the array
                    if not os.path.exists(identity_dir):
                        os.mkdir(identity_dir)
                    with suppress_stdout():
                        config = get_video_config(clustered_faces, identity, identity_dir, filter_straight_face, save_format, device, frame_rate)
                    with open(os.path.join(identity_dir,f"{identity}_info.json"),"w") as f:
                        json.dump(config,f)
                #     identities.append(config)
                # video_config["Identities"] = identities
                with open(os.path.join(destination_path,f"{video_name}.json"),"w") as f:
                        json.dump(video_config,f)
            except Exception as e:
                with open(os.path.join(error_directory,f"{video_name}.txt"),"w") as f:
                    f.write(str(e))
                print(str(e))
                continue
        torch.cuda.empty_cache()
        with open(os.path.join(project_path,f"{project_name}.json"),"w") as f:
            json.dump(dataset_json,f)
    except Exception as e:
        raise Exception(e)
if __name__ == "__main__":
    # /mnt/c/Users/ASUS/Desktop/PhospheneAI2/pkg-face-clustering/
    with open("/mnt/c/Users/ASUS/Desktop/PhospheneAI2/pkg-face-clustering/identity_clustering/data_proc/config/jsonify.yaml",'r') as file:
        config_jsonify = yaml.safe_load(file)
    #Path to store the JSON file and Some extracted Images
    SAVE_PATH = config_jsonify["SAVE_PATH"]
    #setting Two main JSON attributes the root path and the project name, the root path will
    ROOT_PATH =   config_jsonify["ROOT_PATH"]
    # MASK_PATH = config_jsonify["MASK_PATH"]
    PROJECT_NAME = config_jsonify["PROJECT_NAME"]
    save_embed = config_jsonify["save_embed"]
    filter_straight_face = config_jsonify["straight_face"]
    #device
    device = torch.device(config_jsonify["DEVICE"])
    jsonify(ROOT_PATH, PROJECT_NAME,SAVE_PATH, save_embed, filter_straight_face, save_format="jpg", device=device, frame_rate=10)