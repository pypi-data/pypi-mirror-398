from abc import ABC, abstractmethod
from typing import List

from facenet_pytorch.models.mtcnn import MTCNN
import insightface
import numpy as np
import warnings

class VideoFaceDetector(ABC):

    def __init__(self, **kwargs) -> None:
        super().__init__()

    @property
    @abstractmethod
    def _batch_size(self) -> int:
        pass

    @abstractmethod
    def _detect_faces(self, frames) -> List:
        pass


class FacenetDetector(VideoFaceDetector):

    def __init__(self, device="cuda:0") -> None:
        super(FacenetDetector,self).__init__()

        self.detector = MTCNN(
            device=device,
            thresholds=[0.85, 0.95, 0.95],
            margin=0,
        )

    def _detect_faces(self, frames) -> List:
        """
        passes all the frames of a video and then returns the bboxes
        of each frame into batch_boxes.
        """
        batch_boxes, *_ = self.detector.detect(frames, landmarks=False)
        if batch_boxes is None:
            return []
        return [b.tolist() if b is not None else None for b in batch_boxes]
    @property
    def _batch_size(self):
        return 32

class FaceInfoExtractor(VideoFaceDetector):

    def __init__(self, device="cuda:0", need_embed=True, need_kps=True):
        super(FaceInfoExtractor,self).__init__()
        self.ret_model = insightface.app.FaceAnalysis(name="buffalo_l")
        if device == "cuda" or device == "cuda:0":
            device = 0
        elif device == "cpu":
            device = -1
        self.ret_model.prepare(ctx_id=device)
        self.need_embed = need_embed
        self.need_kps = need_kps
    def _extract_face_info(self, frame):
        details = self.ret_model.get(frame)
        faces_in_frame = []
        if len(details) == 0:
            warnings.warn("No faces detected in the frame")
            return []
        for detail in details:
            landmarks = detail.landmark_2d_106
            kps = detail.kps.tolist() if self.need_kps else np.zeros((1,))
            bbox = detail.bbox.tolist()
            embd = detail.embedding if self.need_embed else np.zeros((1,))
            faces_in_frame.append((bbox,kps,embd))
        del details
        return faces_in_frame
    def _detect_faces(self,frames) -> List:
        extracted_info = []
        for frame in frames:
            if not isinstance(frame, np.ndarray):
                warnings.warn("Frame is not a numpy array")
                continue
            extracted_info.append(self._extract_face_info(frame))
        return extracted_info
    @property
    def _batch_size(self):
        return 32