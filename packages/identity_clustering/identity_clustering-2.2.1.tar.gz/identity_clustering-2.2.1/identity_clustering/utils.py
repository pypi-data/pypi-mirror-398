import cv2
from PIL import Image
import numpy as np
from torchcodec.decoders import VideoDecoder
from sys import getsizeof
def _get_frames(video_path):
    """
    This function gets the video path, reads the video, stores
    the frames in a list and then returns
    """
    decoders = VideoDecoder(video_path, device = 'cuda')
    frames = decoders[:].permute(0,2,3,1).cpu().numpy() #TO FIX: match pil format
    return frames


def _get_crop(frame, bbox, pad_constant : int | tuple = 3, multiplier: int = 2):
    '''
        This function takes a frame and a bbox and then outputs the region of the image given by the bounding box
        Args : 
        - frame : np.ndarray -> image frame containing the faces to be cropped.
        - bbox : list -> the bounding box associated with that frame.
        - pad_constant : int -> The constant to control the padding. Default is None.
        - use_pad_constant : bool -> If True, uses the pad_constant to control the padding. Default is False.
        - multiplier : int -> mulitplier to multiply bbox values (must be clearly defined later) (DO NOT CHANGE THE MULTIPLIER)
        Returns :

        - crop : np.ndarray -> the cropped output of the faces.
    '''
    xmin, ymin, xmax, ymax = [int(b*multiplier) for b in bbox]
    w = xmax - xmin
    h = ymax - ymin

    # Add some padding to catch background too
    '''
                          [[B,B,B,B,B,B],
    [[F,F,F,F],            [B,F,F,F,F,B],
     [F,F,F,F],    --->    [B,F,F,F,F,B],
     [F,F,F,F]]            [B,F,F,F,F,B],
                           [B,B,B,B,B,B]]

            F -> Represents pixels with the Face.
            B -> Represents the Background.
            padding allows us to include some background around the face.
            (padding constant 3 here causes some issue with some videos)
    '''
    p_w = 0
    p_h = 0
    if type(pad_constant) == int:
        p_h = h // abs(pad_constant)
        p_w = w // abs(pad_constant)
    elif type(pad_constant) == float:
        p_h = h // abs(pad_constant[0])
        p_w = w // abs(pad_constant[1])

    
    crop_h = (ymax + p_h) - max(ymin - p_h, 0)
    crop_w = (xmax + p_w) - max(xmin - p_w, 0)

    # Make the image square
    '''
    Makes the crop equal on all sides by adjusting the pad
    '''
    if crop_h > crop_w:
        p_h -= int(((crop_h - crop_w)/2))
    else:
        p_w -= int(((crop_w - crop_h)/2))

    # Extract the face from the frame
    crop = frame[max(ymin - p_h, 0):ymax + p_h, max(xmin - p_w, 0):xmax + p_w]
    
    # Check if out of bound and correct
    h, w = crop.shape[:2]
    if h > w:
        diff = int((h - w)/2)
        if diff > 0:         
            crop = crop[diff:-diff,:]
        else:
            crop = crop[1:,:]
    elif h < w:
        diff = int((w - h)/2)
        if diff > 0:
            crop = crop[:,diff:-diff]
        else:
            crop = crop[:,:-1]

    return crop
def extract_crops(video_path, bboxes_dict, pad_constant: int | tuple = 3, multiplier :int = 2):

    frames = _get_frames(video_path)
    crops = []
    keys = [int(x) for x in list(bboxes_dict.keys())]
    for i in range(0, len(frames)):
        frame = frames[i]
        if i not in keys:
            continue
        bboxes = bboxes_dict[i]
        if not bboxes:
            continue
        for bbox in bboxes:
            if isinstance(bbox, list):
                crop = _get_crop(frame, bbox, pad_constant, multiplier)
                fram = _get_crop(frame, bbox, 8, multiplier)
            else:
                crop = _get_crop(frame, bbox[0], pad_constant,multiplier=1)
                fram = _get_crop(frame, bbox[0], 8,multiplier=1)
            # Add the extracted face to the list
            crops.append((i, Image.fromarray(crop), bbox, Image.fromarray(fram)))

    return crops

def draw_faces(frame, faces):
    for bbox, kps, embedding in faces:
        x1, y1, x2, y2 = map(int, bbox)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        for (x, y) in kps:
            cv2.circle(frame, (int(x), int(y)), 2, (0, 0, 255), -1)

    return frame

def get_straight_face(kps,lowerbound=0.85,upperbound=1.25):
    if len(kps)<5:
        return False
    len_ = np.sqrt((kps[0][0] - kps[2][0])**2 + (kps[0][1] - kps[2][1])**2)
    ren_ = np.sqrt((kps[1][0] - kps[2][0])**2 + (kps[1][1] - kps[2][1])**2)
    lmn_ = np.sqrt((kps[3][0] - kps[2][0])**2 + (kps[3][1] - kps[2][1])**2)
    rmn_ = np.sqrt((kps[4][0] - kps[2][0])**2 + (kps[4][1] - kps[2][1])**2)
    pitch_ratio = (len_ + ren_)/(lmn_ + rmn_)
    yaw_ratio = (len_+lmn_)/(ren_+rmn_)
    print(pitch_ratio, yaw_ratio)
    if not lowerbound < pitch_ratio< upperbound or not lowerbound < yaw_ratio < upperbound:
        return False
    return True
