from typing import Dict, List

import networkx as nx
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1
from torch.utils.data.dataloader import DataLoader
from torchvision.transforms import Resize, ToTensor, Compose
from PIL import Image
import os
from identity_clustering.dataset import VideoDataset
from identity_clustering.facedetector import FacenetDetector, FaceInfoExtractor
from identity_clustering.utils import extract_crops


class FaceCluster:

    def __init__(
            self, crops=None, similarity_threshold: int = 0.85, device: str = "cpu", allow_single_face_cluster: bool = False, is_profiling : bool = False, is_inference : bool = False, shape:tuple = (128,128),
            arcface_model_path : str | os.PathLike = None, arcface : bool = False
    ):
        import tempfile
        self.similarity_threshold = similarity_threshold
        self.device = torch.device(device)
        self.crops = crops 
        self.shape = shape
        self.is_inference = is_inference
        self.tempdir = tempfile.TemporaryDirectory()
        self.save_path = os.path.join(self.tempdir.name,"webface_r50.onnx")
        self.is_external_path_provided = False
        if arcface_model_path:
            self.is_external_path_provided = True
            if os.path.isdir(arcface_model_path):
                self.save_path = os.path.join(arcface_model_path,"webface_r50.onnx")
            else:
                self.save_path = arcface_model_path
        self.embedding_extractor = InceptionResnetV1(pretrained="vggface2").eval().to(self.device)
        self.url = "https://drive.usercontent.google.com/download?id=1N0GL-8ehw_bz2eZQWz2b0A5XBdXdxZhg&export=download&authuser=0&confirm=t&uuid=ac614f9a-9111-4a83-80c3-6dea200a6819&at=ALoNOgl4wR5G2t7y0FvEgdkxJISP%3A1748804040944"
        self.headers = {
            "Host": "drive.usercontent.google.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Cookie": "HSID=AAj_x9vXkihL9Wl9Z; SSID=AIfz0uEnXkliBvcK8; APISID=kbgv6u2tlFych_Xr/AJ4JNwhja4T19yItr; SAPISID=kini1tsMuoqYlEOb/AgN4kdzVHGsjDe9pm; __Secure-1PAPISID=kini1tsMuoqYlEOb/AgN4kdzVHGsjDe9pm; __Secure-3PAPISID=kini1tsMuoqYlEOb/AgN4kdzVHGsjDe9pm; AEC=AVcja2eVApAUPUzOftIotspLVp1IMhw3JuJJMnkgxOV2tK4G00dPNkFnO8M; __Secure-ENID=28.SE=kSIBR3PxTal8ix_r69VXmQKa8rs_hcM3qF1-93E2MGvcS20Qz-OCx9KuyGh949IAUTTwb4cPZNOzPY252n1YkozKWiIEOaF7VfyjAIX64aebwdbPg_6zk1uFYSNalScjefZADI6-yz33yPdXrhsi994XArloINd31lg7lAMs78Ryu94gnr-4bfhSasPeqPfSyGegzyXCj7SkNqQAC2xP7fo09w6bZt09bRhtjCWAX7z-sOs; SID=g.a000xgjwjpJCTOAYkiI1p46Jy5WLY1dcq_Qk3o1O-XVrI-F25XnZ6Rj5y9PQ8bOEI9ONjpPxegACgYKAeYSARASFQHGX2MiGDwHX9rrwap652xZENzjBxoVAUF8yKplSmVrxy7RA8rKkmE0DiIX0076; __Secure-1PSID=g.a000xgjwjpJCTOAYkiI1p46Jy5WLY1dcq_Qk3o1O-XVrI-F25XnZdtrdI_skkHuBB4e3PaV3GwACgYKAQcSARASFQHGX2MiSBAPwysTR5T-jzaAcCNnmBoVAUF8yKqRlur3_p8SGS2Sf5wLJyco0076; __Secure-3PSID=g.a000xgjwjpJCTOAYkiI1p46Jy5WLY1dcq_Qk3o1O-XVrI-F25XnZC3tUsnbAHnWOcSTVf1_bngACgYKAbMSARASFQHGX2MievIUdQ8AcwyK3rY_FB8oFxoVAUF8yKoLotLjezpFFzLW9b-LnQAx0076; NID=524=ZlLiwZ7sGQUsyranW44RKFNN-5jH5tmsDwzBEwPmReJjNzezcPxAa2gWJ56-iXT2TFGyTstBaru5SjswZw3Zcihs7oHMN-c3kWKOrH-BnT2xPrcvE0-0CEXMZ4TWe_3Z9E0tFGEZfReIswlp5gKsq6ktHvhv4H108JqUa7jLCOB6P0w0qCCRDPJenC8XYHlKI1WpfQ_fJu82ejkn64ClycIVpasv8fhcALyzDB3Phn5032ZucxD7H6l4WQPMaMYFj0UTTmfdd1fMBWps5NkuWbw-wf1xpcLSxOfGGe3EK1x1CHUcsZZ0ZJ8Qsje95iOm0fhlqYZmnio7YWoynMJ_FWqLX7tCMkTIFub3cScRCUVacQCM_R9nY49MARNPCPUIIuV0-sXbCRnHXem4CBQLd6sYA1JgwLpD7TH-J9CapnUBzeK-Z-m8OKX4WCu3q0WrDXpHnrjMl316OlzppRGHBHTV1QCTzohLANx9RUQe2nJ6XxQMrkf95IgA1J62avn81g5oN-oR9mgZzH1V2HxHP5eUDuObFa_CHz9pvoUjaGi9EqN4owM59-2IUL7P5WSnf9ZN87exthQfH5JxA450dOhblRtsj1Q1r1vxqdHbUI2QLWtPt0iwkPIkjyzUzA4sQvLkIBgTZa2iANZLowgFudq1OCSDvTGs_J2U9-awBNW3NwiyrdoTNy0jq1FEAnuEKdxeBNlrOxJ6aXbaUYycIAqXSxWvhUPG0tX52aVxRatNLMIBEVGG66FWlRYTSBBi8Wbs3Zbjt1nTSn0u5AGLTx2nqV8ZNZ2mUqBPG9bXO5kHDfTEkcegnu5B5gbsQGTDCpStcoYF2_e49SYH2FSchSNn7ciulHrQSJgxzX_LOHWzxtjC5Di5KEf1sbdX8-2XTnb2rTKmz0hPO8to-0S9yKy-9UshubIUZ4ftM2i7Bz6YEWwcnDZuGDm1doPvd7CYBB8tkazSlgawIl4m-igOXs-mol_wT2sn09TVMwiys9UrlbrEjuupwrv-m04CrMNAjYSPPpN8ZbtHb4Nibd2alT8XcvKsZvg23qzf19GNo1VbzHs; __Secure-1PSIDTS=sidts-CjEB5H03Pwouwt_2gm8il5It9bTxqGgrqrreWDmzQopuCUppITOFgRcked6FLgH5zrs_EAA; __Secure-3PSIDTS=sidts-CjEB5H03Pwouwt_2gm8il5It9bTxqGgrqrreWDmzQopuCUppITOFgRcked6FLgH5zrs_EAA; SIDCC=AKEyXzVLdNWidgn3FSzfTNgWxKPf-DGgVVBi6WUOlzGMJ1QtVk8WR4PBDLoiWUqjIDqnWBPB2uUc; __Secure-1PSIDCC=AKEyXzVqZPA-FcYMdNDHDBh1k1xAwzyW6PSUMrbQQ4XUlewpvLH-LBH1n_YyZOJGV0PuPMHidmqh; __Secure-3PSIDCC=AKEyXzU9T2QhcI2Wks2F9FEJ07fvJkTs_Wt6dburMNakc6khQf4uiXKavAEsdlicf6Oh5stqapz2",
            "Connection": "keep-alive"
        }
        self.arcface = arcface
        if self.arcface:
            self.use_arcface()
    def __enter__(self):
        return self

    def __exit__(self,exc_type, exc_value, traceback):
        self.clean_up()

    def use_arcface(self):
        '''
        if using without with statement call this function to use arcface model at the begining. don't forget to call clean up later.
        '''
        import onnx
        from onnx2torch import convert
        import warnings
        import requests
        import tqdm
        if not os.path.exists(self.save_path):
            response = requests.get(self.url, stream=True, headers=self.headers)
            total_size = int(response.headers.get("content-length", 0))

            with open(self.save_path, "wb") as file, tqdm.tqdm(
                desc=self.save_path,
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for data in response.iter_content(chunk_size=1024):
                    size = file.write(data)
                    bar.update(size)
        if os.path.exists(self.save_path):
            onnx_model = onnx.load(self.save_path)
            model = convert(onnx_model)
            self.embedding_extractor = model.eval().to(self.device)
            self.shape = (112,112)
        else:
            warnings.warn(f"Arcface weights download failed, falling back to InceptionNetv2(vggface)")

    def clean_up(self):
        import gc
        if not self.is_external_path_provided and os.path.exists(self.save_path):
            os.remove(self.save_path)
        self.tempdir.cleanup()
        del self.embedding_extractor
        gc.collect()
        torch.cuda.empty_cache()
    def _set_crops(self, crops) -> None:
        '''
        A setter function to set the threshold attribute
        Args :
         - crops : List[tuple] -> contains tuples with (frame_no(int), PIL Image of the cropped face, bbox(list(int)))

        Returns :
            None
        '''
        self.crops = crops

    def _set_threshold(self, threshold : float) -> None:
        '''
        A setter function to set the threshold attribute
        Args :
         - threshold : float -> threshold value.

        Returns :
            None
        '''
        self.similarity_threshold = threshold

    def _generate_connected_components(self, similarities):
        '''
        Helper function for the clustering function, takes in dot product similarities and clusters them based on a predefined threshold,
        the threshold can be set by the user when intializing the class or can be set while calling the `cluster_faces` function
        
        Args :
         - similarities : np.ndarray -> similarity matrix (attention without scaling)

        Returns :
         - components : list -> list of clustered faces
        '''
        graph = nx.Graph()
        n = similarities.shape[0]
        threshold = self.similarity_threshold
        mask = (similarities > threshold) & (~np.eye(n, dtype = bool))
        edges = np.argwhere(mask)
        graph.add_edges_from(map(tuple,edges))
        components_list = [list(component) for component in nx.connected_components(graph)]
        return components_list
    @torch.no_grad
    def get_similarities_on_images(self, crops_images):
        '''
        Being Kept for compatibility
        '''
        transform = Compose([Resize(self.shape), ToTensor()])
        faces = torch.stack([transform(face) for face in crops_images])
        faces = faces.to(self.device, non_blocking=True)
        embeddings = self.embedding_extractor(faces)
        if self.arcface:
            embeddings = torch.nn.functional.normalize(embeddings, p=2)
        similarities = torch.mm(embeddings, embeddings.T).cpu().numpy()
        return similarities
    def get_similarities_on_embeds(self, crops_embeds):
        embeddings = torch.stack([torch.tensor(face) for face in crops_embeds])
        embeddings = embeddings.to(self.device, non_blocking=True)
        embeddings = torch.nn.functional.normalize(embeddings, p=2)
        similarities = torch.mm(embeddings, embeddings.T).cpu().numpy()
        return similarities
    def cluster_faces(self, crops, threshold=None):
        '''
        Function that clusters the faces using the dot product similarity metric.
        
        Args:
         - crops : List[tuple] -> contains tuples with (frame_no(int), PIL Image of the cropped face, bbox(list(int)))
         - threshold : Optional[float] -> set to change the threshold attribute.
        
        Returns :
         - clustered_faces : Dict[int,list] -> returns a dictionary containing the identity as keys and all the faces associated with a single
                                               identity as a list.
        '''

        if threshold:
            self._set_threshold(threshold)

        if crops and self.is_inference:
            self._set_crops(crops)

        # Convert crops to PIL images
        try:
            assert isinstance(crops[0][2][-1], np.ndarray) and crops[0][2][-1].shape == (512,)
            crops_embeds = [row[2][-1] for row in crops]
            similarities = self.get_similarities_on_embeds(crops_embeds)
        except AssertionError:
            assert isinstance(crops[0][3], Image.Image)
            crops_images = [row[3] for row in crops]
            similarities = self.get_similarities_on_images(crops_images)
        
        components = self._generate_connected_components(similarities)
        components = [sorted(component) for component in components]

        # Assigning each cluster to a unique identity
        clustered_faces = {}
        for identity_index, component in enumerate(components):
            for index, face_index in enumerate(component):
                component[index] = crops[face_index]

            clustered_faces[identity_index] = component



        return clustered_faces


def cluster(
    clust: FaceCluster,
    video_path: str,
    faces: List[tuple],
    pad_constant: int | tuple | None = 3,
    similarity_threshold : float = 0.9,
    multiplier : int = 2 # NOTE: new changes made with torchcodec makes how the mulitplier work in the _get_crop func a bit mysterious, must be investigated later.
) -> Dict[int, list]:
    crops = extract_crops(video_path, faces, pad_constant, multiplier)
    clustered_faces = clust.cluster_faces(crops, similarity_threshold)
    return clustered_faces

def detect_faces(video_path, device, need_embed=True, need_kps=True, v2=False):
    """  
    We'll be using the facenet detector that is required to detect the faces
    present in each frame. This function is only responsible to return
    a dictionary that contains the bounding boxes of each frame.
    Args:
        video_path: str - Path to the video.
        device: str - indicates whether to leverage CPU or GPU for processing.
        need_embed: bool - set to true if you wish to save arcface embeddings of faces in frames.
        need_kps: bool - set to true if you want kps points for each face.
        v2: bool - set to true to make sure the VideoDataset class loads data in the proper format.
    returns: 
        dict: dict template:
            {
                frame_no: [[
                    [number, number, number, number],
                    [number, number, number, number],
                    ...
                    ...
                    [number, number, number, number]
                ]]
            }
        int: fps of the video
    """
    detector = FacenetDetector(device=device)
    if v2:
        detector = FaceInfoExtractor(device=device, need_embed=need_embed, need_kps=need_kps)

    # Read the video and its information
    dataset = VideoDataset([video_path],v2=v2)
    # loader = DataLoader(
    #     dataset, shuffle=False, num_workers=0, batch_size=1
    # )
    import unittest
    # Detect the faces
    for item in dataset:
        bboxes = {}
        video, indices, fps, frames = item
        # assert len(frames) > 0 and (isinstance(frames[0], np.ndarray) or isinstance(frames[0], Image.Image)) or isinstance(frames[0],unittest.mock.MagicMock), f"No Frames read in the video or the frames are not in the correct type {type(frames[0])}"
        """
            Update bboxes dict with the bounding boxes present in each frame with the 
            frame number as the index and 
            a two dimensional list containing the bounding boxes as the value. 
        """
        bboxes.update({i: b for i, b in zip(indices, detector._detect_faces(frames))})
        found_faces = False
        for key in list(bboxes.keys()):
            if isinstance(bboxes[key], list):
                found_faces = True
                break

        if not found_faces:
            return None, indices[-1]
    return bboxes, fps