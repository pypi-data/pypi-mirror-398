"""
maix.nn module
"""
from __future__ import annotations
import maix._maix.err
import maix._maix.image
import maix._maix.tensor
import typing
from . import F
__all__: list[str] = ['Classifier', 'DepthAnything', 'F', 'FaceDetector', 'FaceLandmarks', 'FaceLandmarksObject', 'FaceObject', 'FaceObjects', 'FaceRecognizer', 'HandLandmarks', 'InternVL', 'InternVLPostConfig', 'InternVLResp', 'LayerInfo', 'Layout', 'MUD', 'MeloTTS', 'MixFormerV2', 'NN', 'NanoTrack', 'OCR_Box', 'OCR_Object', 'OCR_Objects', 'Object', 'ObjectFloat', 'Objects', 'PP_OCR', 'Qwen', 'QwenPostConfig', 'QwenResp', 'Retinaface', 'SelfLearnClassifier', 'Speech', 'SpeechDecoder', 'SpeechDevice', 'Whisper', 'YOLO11', 'YOLOWorld', 'YOLOv5', 'YOLOv8']
class Classifier:
    label_path: str
    labels: list[str]
    mean: list[float]
    scale: list[float]
    def __init__(self, model: str = '', dual_buff: bool = True) -> None:
        ...
    def classify(self, img: maix._maix.image.Image, softmax: bool = True, fit: maix._maix.image.Fit = ...) -> list[tuple[int, float]]:
        """
        Forward image to model, get result. Only for image input, use classify_raw for tensor input.
        
        Args:
          - img: image, format should match model input_type， or will raise err.Exception
          - softmax: if true, will do softmax to result, or will return raw value
          - fit: image resize fit mode, default Fit.FIT_COVER, see image.Fit.
        
        
        Returns: result, a list of (label, score). If in dual_buff mode, value can be one element list and score is zero when not ready. In C++, you need to delete it after use.
        """
    def classify_raw(self, data: maix._maix.tensor.Tensor, softmax: bool = True) -> list[tuple[int, float]]:
        """
        Forward tensor data to model, get result
        
        Args:
          - data: tensor data, format should match model input_type， or will raise err.Excetion
          - softmax: if true, will do softmax to result, or will return raw value
        
        
        Returns: result, a list of (label, score). In C++, you need to delete it after use.
        """
    def input_format(self) -> maix._maix.image.Format:
        """
        Get input image format, only for image input
        
        Returns: input image format, image::Format type.
        """
    def input_height(self) -> int:
        """
        Get model input height, only for image input
        
        Returns: model input size of height
        """
    def input_shape(self) -> list[int]:
        """
        Get input shape, if have multiple input, only return first input shape
        
        Returns: input shape, list type
        """
    def input_size(self) -> maix._maix.image.Size:
        """
        Get model input size, only for image input
        
        Returns: model input size
        """
    def input_width(self) -> int:
        """
        Get model input width, only for image input
        
        Returns: model input size of width
        """
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file, model format is .mud,
        MUD file should contain [extra] section, have key-values:
        - model_type: classifier
        - input_type: rgb or bgr
        - mean: 123.675, 116.28, 103.53
        - scale: 0.017124753831663668, 0.01750700280112045, 0.017429193899782137
        - labels: imagenet_classes.txt
        
        Args:
          - model: MUD model path
        
        
        Returns: error code, if load failed, return error code
        """
class DepthAnything:
    mean: list[float]
    scale: list[float]
    def __init__(self, model: str = '', dual_buff: bool = True) -> None:
        ...
    def get_depth(self, img: maix._maix.image.Image, fit: maix._maix.image.Fit = ...) -> maix._maix.tensor.Tensor:
        """
        Forward model and get raw image depth estimation data.
        
        Args:
          - img: image, format should match model input_type， or will raise err.Exception
          - fit: image resize fit mode if input image not equal to model' input size,
        will auto resize to model's input size then detect, and recover to image input size.
        Default Fit.FIT_CONTAIN, see image.Fit.
        
        
        Returns: result, a tensor.Tensor object. If in dual_buff mode, value can be None(in Python) or nullptr(in C++) when not ready. In C++, you need to delete it after use.
        """
    def get_depth_image(self, img: maix._maix.image.Image, fit: maix._maix.image.Fit = ..., cmap: maix._maix.image.CMap = ...) -> maix._maix.image.Image:
        """
        Forward model and get image depth estimation data normlized to [0, 255] and as a image.Image object.
        
        Args:
          - img: image, format should match model input_type， or will raise err.Exception
          - fit: image resize fit mode if input image not equal to model' input size,
        will auto resize to model's input size then detect, and recover to image input size.
        Default Fit.FIT_CONTAIN, see image.Fit.
          - cmap: Color map used convert grayscale distance estimation image to RGB image.
        Diiferent cmap will influence finally image.
        Default image.CMap.INFERNO.
        
        
        Returns: result, a image::Image object. If in dual_buff mode, value can be None(in Python) or nullptr(in C++) when not ready. In C++, you need to delete it after use.
        """
    def input_format(self) -> maix._maix.image.Format:
        """
        Get input image format, only for image input
        
        Returns: input image format, image::Format type.
        """
    def input_height(self) -> int:
        """
        Get model input height, only for image input
        
        Returns: model input size of height
        """
    def input_shape(self) -> list[int]:
        """
        Get input shape, if have multiple input, only return first input shape
        
        Returns: input shape, list type
        """
    def input_size(self) -> maix._maix.image.Size:
        """
        Get model input size, only for image input
        
        Returns: model input size
        """
    def input_width(self) -> int:
        """
        Get model input width, only for image input
        
        Returns: model input size of width
        """
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file, model format is .mud,
        MUD file should contain [extra] section, have key-values:
        - model_type: depth_anything_v2
        - input_type: rgb or bgr
        - mean: 123.675, 116.28, 103.53
        - scale: 0.017124753831663668, 0.01750700280112045, 0.017429193899782137
        - labels: imagenet_classes.txt
        
        Args:
          - model: MUD model path
        
        
        Returns: error code, if load failed, return error code
        """
class FaceDetector:
    mean: list[float]
    scale: list[float]
    def __init__(self, model: str = '', dual_buff: bool = True) -> None:
        ...
    def detect(self, img: maix._maix.image.Image, conf_th: float = 0.5, iou_th: float = 0.45, fit: maix._maix.image.Fit = ...) -> list[Object]:
        """
        Detect objects from image
        
        Args:
          - img: Image want to detect, if image's size not match model input's, will auto resize with fit method.
          - conf_th: Confidence threshold, default 0.5.
          - iou_th: IoU threshold, default 0.45.
          - fit: Resize method, default image.Fit.FIT_CONTAIN.
        
        
        Returns: Object list. In C++, you should delete it after use.
        """
    def input_format(self) -> maix._maix.image.Format:
        """
        Get input image format
        
        Returns: input image format, image::Format type.
        """
    def input_height(self) -> int:
        """
        Get model input height
        
        Returns: model input size of height
        """
    def input_size(self) -> maix._maix.image.Size:
        """
        Get model input size
        
        Returns: model input size
        """
    def input_width(self) -> int:
        """
        Get model input width
        
        Returns: model input size of width
        """
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model: Model path want to load
        
        
        Returns: err::Err
        """
class FaceLandmarks:
    landmarks_num: int
    mean: list[float]
    scale: list[float]
    def __init__(self, model: str = '') -> None:
        ...
    def crop_image(self, img: maix._maix.image.Image, x: int, y: int, w: int, h: int, points: list[int], new_width: int = -1, new_height: int = -1, scale: float = 1.2) -> maix._maix.image.Image:
        """
        Crop image from source image by 2 points(2 eyes)
        
        Args:
          - x,y,w,h: face rectangle, x,y is left-top point.
          - img: source image
          - points: 2 points, eye_left_x, eye_left_y, eye_right_x, eye_right_y
          - scale: crop size scale relative to rectangle's max side length(w or h), final value is `scale *max(w, h)`,default 1.2.
        """
    def detect(self, img: maix._maix.image.Image, conf_th: float = 0.5, landmarks_abs: bool = True, landmarks_rel: bool = False) -> FaceLandmarksObject:
        """
        Detect objects from image
        
        Args:
          - img: Image want to detect, if image's size not match model input's, will auto resize with fit method.
          - conf_th: Hand detect confidence threshold, default 0.7.
          - landmarks_rel: outputs the relative coordinates of 21 points with respect to the top-left vertex of the hand.
        In obj.points, the last 21x2 values are arranged as x0y0x1y1...x20y20.
        Value from 0 to obj.w.
        
        
        Returns: Object list. In C++, you should delete it after use.
        Object's points value format: box_topleft_x, box_topleft_y, box_topright_x, box_topright_y, box_bottomright_x, box_bottomright_y， box_bottomleft_x, box_bottomleft_y,
        x0, y0, z1, x1, y1, z2, ..., x20, y20, z20.
        If landmarks_rel is True, will be box_topleft_x, box_topleft_y...,x20,y20,z20,x0_rel,y0_rel,...,x20_rel,y20_rel.
        Z is depth, the larger the value, the farther away from the palm, and the positive value means closer to the camera.
        """
    def draw_face(self, img: maix._maix.image.Image, points: list[int], num: int, points_z: list[int] = [], r_min: int = 2, r_max: int = 4) -> None:
        """
        Draw hand and landmarks on image
        
        Args:
          - img: image object, maix.image.Image type.
          - leftright,: 0 means left, 1 means right
          - points: points result from detect method: x0, y0, x1, y1, ..., xn-1, yn-1.
          - points_z: points result from detect method: z0, z1, ..., zn-1.
          - r_min: min radius of points.
          - r_max: min radius of points.
        """
    def input_format(self) -> maix._maix.image.Format:
        """
        Get input image format
        
        Returns: input image format, image::Format type.
        """
    def input_height(self, detect: bool = True) -> int:
        """
        Get model input height
        
        Args:
          - detect: detect or landmarks model, default true.
        
        
        Returns: model input size of height
        """
    def input_size(self, detect: bool = True) -> maix._maix.image.Size:
        """
        Get model input size
        
        Args:
          - detect: detect or landmarks model, default true.
        
        
        Returns: model input size
        """
    def input_width(self, detect: bool = True) -> int:
        """
        Get model input width
        
        Args:
          - detect: detect or landmarks model, default true.
        
        
        Returns: model input size of width
        """
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model: Model path want to load
        
        
        Returns: err::Err
        """
class FaceLandmarksObject:
    points: list[int]
    points_z: list[int]
    score: float
    valid: bool
    def __init__(self) -> None:
        ...
class FaceObject:
    class_id: int
    face: maix._maix.image.Image
    feature: list[float]
    h: int
    points: list[int]
    score: float
    w: int
    x: int
    y: int
    def __init__(self, x: int = 0, y: int = 0, w: int = 0, h: int = 0, class_id: int = 0, score: float = 0, points: list[int] = [], feature: list[float] = [], face: maix._maix.image.Image = ...) -> None:
        ...
    def __str__(self) -> str:
        """
        FaceObject info to string
        
        Returns: FaceObject info string
        """
class FaceObjects:
    def __getitem__(self, idx: int) -> FaceObject:
        """
        Get object item
        """
    def __init__(self) -> None:
        ...
    def __iter__(self) -> typing.Iterator:
        ...
    def __len__(self) -> int:
        """
        Get size
        """
    def add(self, x: int = 0, y: int = 0, w: int = 0, h: int = 0, class_id: int = 0, score: float = 0, points: list[int] = [], feature: list[float] = [], face: maix._maix.image.Image = ...) -> FaceObject:
        """
        Add object to FaceObjects
        """
    def at(self, idx: int) -> FaceObject:
        """
        Get object item
        """
    def remove(self, idx: int) -> maix._maix.err.Err:
        """
        Remove object form FaceObjects
        """
class FaceRecognizer:
    features: list[list[float]]
    labels: list[str]
    mean_detector: list[float]
    mean_feature: list[float]
    scale_detector: list[float]
    scale_feature: list[float]
    def __init__(self, detect_model: str = '', feature_model: str = '', dual_buff: bool = True) -> None:
        ...
    def add_face(self, face: FaceObject, label: str) -> maix._maix.err.Err:
        """
        Add face to lib
        
        Args:
          - face: face object, find by recognize
          - label: face label(name)
        """
    def input_format(self) -> maix._maix.image.Format:
        """
        Get input image format
        
        Returns: input image format, image::Format type.
        """
    def input_height(self) -> int:
        """
        Get model input height
        
        Returns: model input size of height
        """
    def input_size(self) -> maix._maix.image.Size:
        """
        Get model input size
        
        Returns: model input size
        """
    def input_width(self) -> int:
        """
        Get model input width
        
        Returns: model input size of width
        """
    def load(self, detect_model: str, feature_model: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - detect_model: face detect model path, default empty, you can load model later by load function.
          - feature_model: feature extract model
        
        
        Returns: err::Err
        """
    def load_faces(self, path: str) -> maix._maix.err.Err:
        """
        Load faces info from a file
        
        Args:
          - path: from where to load, string type.
        
        
        Returns: err::Err type
        """
    def recognize(self, img: maix._maix.image.Image, conf_th: float = 0.5, iou_th: float = 0.45, compare_th: float = 0.8, get_feature: bool = False, get_face: bool = False, fit: maix._maix.image.Fit = ...) -> FaceObjects:
        """
        Detect objects from image
        
        Args:
          - img: Image want to detect, if image's size not match model input's, will auto resize with fit method.
          - conf_th: Detect confidence threshold, default 0.5.
          - iou_th: Detect IoU threshold, default 0.45.
          - compare_th: Compare two face score threshold, default 0.8, if two faces' score < this value, will see this face fas unknown.
          - get_feature: return feature or not, if true will copy features to result, if false will not copy feature to result to save time and memory.
          - get_face: return face image or not, if true result object's face attribute will valid, or face sttribute is empty. Get face image will alloc memory and copy image, so will lead to slower speed.
          - fit: Resize method, default image.Fit.FIT_CONTAIN.
        
        
        Returns: FaceObjects object. In C++, you should delete it after use.
        """
    def remove_face(self, idx: int = -1, label: str = '') -> maix._maix.err.Err:
        """
        remove face from lib
        
        Args:
          - idx: index of face in lib, default -1 means use label, value [0,face_num), idx and label must have one, idx have high priotiry.
          - label: which face to remove, default to empty string mean use idx, idx and label must have one, idx have high priotiry.
        """
    def save_faces(self, path: str) -> maix._maix.err.Err:
        """
        Save faces info to a file
        
        Args:
          - path: where to save, string type.
        
        
        Returns: err.Err type
        """
class HandLandmarks:
    label_path: str
    labels: list[str]
    mean: list[float]
    scale: list[float]
    def __init__(self, model: str = '') -> None:
        ...
    def detect(self, img: maix._maix.image.Image, conf_th: float = 0.7, iou_th: float = 0.45, conf_th2: float = 0.8, landmarks_rel: bool = False) -> Objects:
        """
        Detect objects from image
        
        Args:
          - img: Image want to detect, if image's size not match model input's, will auto resize with fit method.
          - conf_th: Hand detect confidence threshold, default 0.7.
          - iou_th: IoU threshold, default 0.45.
          - conf_th2: Hand detect confidence second time check threshold, default 0.8.
          - landmarks_rel: outputs the relative coordinates of 21 points with respect to the top-left vertex of the hand.
        In obj.points, the last 21x2 values are arranged as x0y0x1y1...x20y20.
        Value from 0 to obj.w.
        
        
        Returns: Object list. In C++, you should delete it after use.
        Object's points value format: box_topleft_x, box_topleft_y, box_topright_x, box_topright_y, box_bottomright_x, box_bottomright_y， box_bottomleft_x, box_bottomleft_y,
        x0, y0, z1, x1, y1, z2, ..., x20, y20, z20.
        If landmarks_rel is True, will be box_topleft_x, box_topleft_y...,x20,y20,z20,x0_rel,y0_rel,...,x20_rel,y20_rel.
        Z is depth, the larger the value, the farther away from the palm, and the positive value means closer to the camera.
        """
    def draw_hand(self, img: maix._maix.image.Image, leftright: int, points: list[int], r_min: int = 4, r_max: int = 10, box: bool = True, box_thickness: int = 1, box_color_l: maix._maix.image.Color = ..., box_color_r: maix._maix.image.Color = ...) -> None:
        """
        Draw hand and landmarks on image
        
        Args:
          - img: image object, maix.image.Image type.
          - leftright,: 0 means left, 1 means right
          - points: points result from detect method: box_topleft_x, box_topleft_y, box_topright_x, box_topright_y, box_bottomright_x, box_bottomright_y， box_bottomleft_x, box_bottomleft_y,
        x0, y0, z1, x1, y1, z2, ..., x20, y20, z20
          - r_min: min radius of points.
          - r_max: min radius of points.
          - box: draw box or not, default true.
          - box_color: color of box.
        """
    def input_format(self) -> maix._maix.image.Format:
        """
        Get input image format
        
        Returns: input image format, image::Format type.
        """
    def input_height(self, detect: bool = True) -> int:
        """
        Get model input height
        
        Args:
          - detect: detect or landmarks model, default true.
        
        
        Returns: model input size of height
        """
    def input_size(self, detect: bool = True) -> maix._maix.image.Size:
        """
        Get model input size
        
        Args:
          - detect: detect or landmarks model, default true.
        
        
        Returns: model input size
        """
    def input_width(self, detect: bool = True) -> int:
        """
        Get model input width
        
        Args:
          - detect: detect or landmarks model, default true.
        
        
        Returns: model input size of width
        """
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model: Model path want to load
        
        
        Returns: err::Err
        """
class InternVL:
    post_config: InternVLPostConfig
    def __init__(self, model: str) -> None:
        ...
    def cancel(self) -> None:
        """
        Cancel running
        """
    def clear_image(self) -> None:
        """
        Clear image, InternVL2.5 based on Qwen2.5, so you can clear image and only use LLM function.
        """
    def get_reply_callback(self) -> typing.Callable[[InternVL, InternVLResp], None]:
        """
        Get reply callback
        
        Returns: reply callback
        """
    def get_system_prompt(self) -> str:
        """
        Get system prompt
        
        Returns: system prompt
        """
    def input_format(self) -> maix._maix.image.Format:
        """
        Image input format
        
        Returns: input format.
        """
    def input_height(self) -> int:
        """
        Image input height
        
        Returns: input height.
        """
    def input_width(self) -> int:
        """
        Image input width
        
        Returns: input width.
        """
    def is_image_set(self) -> bool:
        """
        Whether image set by set_image
        
        Returns: Return true if image set by set_image function, or return false.
        """
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model: direction [in], model file path, model format can be MUD(model universal describe file) file.
        
        
        Returns: error code, if load success, return err::ERR_NONE
        """
    def loaded(self) -> bool:
        """
        Is model loaded
        
        Returns: true if model loaded, else false
        """
    def send(self, msg: str) -> InternVLResp:
        """
        Send message to model
        
        Args:
          - msg: message to send
        
        
        Returns: model response
        """
    def set_image(self, img: maix._maix.image.Image, fit: maix._maix.image.Fit = ...) -> maix._maix.err.Err:
        """
        Set image and will encode image.
        You can set image once and call send multiple times.
        
        Args:
          - img: the image you want to use.
          - fit: Image resize fit method, only used when img size not equal to model input.
        
        
        Returns: err.Err return err.Err.ERR_NONE is no error happen.
        """
    def set_log_level(self, level: ..., color: bool) -> None:
        """
        Set log level
        
        Args:
          - level: log level, @see maix.log.LogLevel
          - color: true to enable color, false to disable color
        """
    def set_reply_callback(self, callback: typing.Callable[[InternVL, InternVLResp], None] = None) -> None:
        """
        Set reply callback.
        
        Args:
          - callback: reply callback, when token(words) generated, this function will be called,
        so you can get response message in real time in this callback funtion.
        If set to None(nullptr in C++), you can get response after all response message generated.
        """
    def set_system_prompt(self, prompt: str) -> None:
        """
        Set system prompt
        
        Args:
          - prompt: system prompt
        """
    def unload(self) -> maix._maix.err.Err:
        """
        Unload model
        
        Returns: error code, if unload success, return err::ERR_NONE
        """
    def version(self) -> str:
        """
        Get model version
        
        Returns: model version
        """
class InternVLPostConfig:
    enable_repetition_penalty: bool
    enable_temperature: bool
    enable_top_k_sampling: bool
    enable_top_p_sampling: bool
    penalty_window: int
    repetition_penalty: float
    temperature: float
    top_k: int
    top_p: float
class InternVLResp:
    err_code: maix._maix.err.Err
    err_msg: str
    msg: str
    msg_new: str
class LayerInfo:
    dtype: maix._maix.tensor.DType
    layout: Layout
    name: str
    shape: list[int]
    def __init__(self, name: str = '', dtype: maix._maix.tensor.DType = ..., shape: list[int] = []) -> None:
        ...
    def __str__(self) -> str:
        """
        To string
        """
    def shape_int(self) -> int:
        """
        Shape as one int type, multiply all dims of shape
        """
    def to_str(self) -> str:
        """
        To string
        """
class Layout:
    """
    Members:
    
      NCHW
    
      NHWC
    
      UNKNOWN
    """
    NCHW: typing.ClassVar[Layout]  # value = <Layout.NCHW: 0>
    NHWC: typing.ClassVar[Layout]  # value = <Layout.NHWC: 1>
    UNKNOWN: typing.ClassVar[Layout]  # value = <Layout.UNKNOWN: 4>
    __members__: typing.ClassVar[dict[str, Layout]]  # value = {'NCHW': <Layout.NCHW: 0>, 'NHWC': <Layout.NHWC: 1>, 'UNKNOWN': <Layout.UNKNOWN: 4>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: int) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: int) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class MUD:
    items: dict[str, dict[str, str]]
    model_path: str
    type: str
    def __init__(self, model_path: str = '') -> None:
        ...
    def load(self, model_path: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model_path: direction [in], model file path, model format can be MUD(model universal describe file) file.
        
        
        Returns: error code, if load success, return err::ERR_NONE
        """
    def parse_labels(self, key: str = 'labels') -> list[str]:
        """
        Please load() first, parse labels in items["extra"]["labels"],
        if items["extra"]["labels"] is a file path: will parse file, every one line is a label;
        if items["extra"]["labels"] is a string, labels split by comma(",").
        Execute this method will replace items["extra"]["labels"];
        
        Args:
          - key: parse from items[key], default "labels".
        
        
        Returns: parsed labels list.
        """
class MeloTTS:
    @staticmethod
    def infer(*args, **kwargs):
        """
        Text to speech
        
        Args:
          - text: input text
          - path: The output path of the voice file, the default sampling rate is 44100,
        the number of channels is 1, and the number of sampling bits is 16. default is empty.
          - output_pcm: Enable or disable the output of raw PCM data. The default output sampling rate is 44100,
        the number of channels is 1, and the sampling depth is 16 bits. default is false.
        
        
        Returns: raw PCM data
        """
    def __init__(self, model: str = '', language: str = 'zh', speed: float = 0.800000011920929, noise_scale: float = 0.30000001192092896, noise_scale_w: float = 0.6000000238418579, sdp_ratio: float = 0.20000000298023224) -> None:
        ...
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model: Model path want to load
        
        
        Returns: err::Err
        """
    def samplerate(self) -> int:
        """
        Get pcm samplerate
        
        Returns: pcm samplerate
        """
    def speed(self) -> float:
        """
        Get the speed of the text
        
        Returns: text speed
        """
class MixFormerV2:
    frame_id: int
    lost_find_interval: int
    mean: list[float]
    scale: list[float]
    update_interval: int
    def __init__(self, model: str = '', update_interval: int = 200, lost_find_interval: int = 60) -> None:
        ...
    def init(self, img: maix._maix.image.Image, x: int, y: int, w: int, h: int) -> None:
        """
        Init tracker, give tacker first target image and target position.
        
        Args:
          - img: Image want to detect, target should be in this image.
          - x: the target position left top coordinate x.
          - y: the target position left top coordinate y.
          - w: the target width.
          - h: the target height.
        """
    def input_format(self) -> maix._maix.image.Format:
        """
        Get input image format
        
        Returns: input image format, image::Format type.
        """
    def input_height(self) -> int:
        """
        Get model input height
        
        Returns: model input size of height
        """
    def input_size(self) -> maix._maix.image.Size:
        """
        Get model input size
        
        Returns: model input size
        """
    def input_width(self) -> int:
        """
        Get model input width
        
        Returns: model input size of width
        """
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model: Model path want to load
        
        
        Returns: err::Err
        """
    def track(self, img: maix._maix.image.Image, threshold: float = 0.5) -> ...:
        """
        Track object acoording to last object position and the init function learned target feature.
        
        Args:
          - img: image to detect object and track, can be any resolution, before detect it will crop a area according to last time target's position.
          - threshold: If score < threshold, will see this new detection is invalid, but remain return this new detecion,  default 0.9.
        
        
        Returns: object, attribute [x, y, w, h] and score are the predict target position and score, points attribute provide more info:
        0~3  [ search_x, search_y, search_w, search_h ]: search area for this time track, based on last correct start position.
        4~5  [ predict_cx, predict_cy]: predict center according to this time input.
        6    [ search_size ]: search_area size based on last correct start position, center is (search_x - search_w / 2, search_y - search_h / 2).
        7    [ predict_template_size ]: template size based on predict target, center is (predict_cx, predict_cy).
        8~11 [ correct_cx, correct_cy, correct_w, correct_h]: latest correct (score > threshold) target position.
        """
class NN:
    def __init__(self, model: str = '', dual_buff: bool = False) -> None:
        ...
    def extra_info(self) -> dict[str, str]:
        """
        Get model extra info define in MUD file
        
        Returns: extra info, dict type, key-value object, attention: key and value are all string type.
        """
    def extra_info_labels(self) -> list[str]:
        """
        Get model parsed extra info labels define in MUD file
        
        Returns: labels list in extra info, string list type.
        """
    def forward(self, inputs: maix._maix.tensor.Tensors, copy_result: bool = True, dual_buff_wait: bool = False) -> maix._maix.tensor.Tensors:
        """
        forward run model, get output of model,
        this is specially for MaixPy, not efficient, but easy to use in MaixPy
        
        Args:
          - input: direction [in], input tensor
          - copy_result: If set true, will copy result to a new variable; else will use a internal memory, you can only use it until to the next forward.
        Default true to avoid problems, you can set it to false manually to make speed faster.
          - dual_buff_wait: bool type, only for dual_buff mode, if true, will inference this image and wait for result, default false.
        
        
        Returns: output tensor. In C++, you should manually delete tensors in return value and return value.
        If dual_buff mode, it can be NULL(None in MaixPy) means not ready.
        """
    def forward_image(self, img: maix._maix.image.Image, mean: list[float] = [], scale: list[float] = [], fit: maix._maix.image.Fit = ..., copy_result: bool = True, dual_buff_wait: bool = False, chw: bool = True) -> maix._maix.tensor.Tensors:
        """
        forward model, param is image
        
        Args:
          - img: input image
          - mean: mean value, a list type, e.g. [0.485, 0.456, 0.406], default is empty list means not normalize.
          - scale: scale value, a list type, e.g. [1/0.229, 1/0.224, 1/0.225], default is empty list means not normalize.
          - fit: fit mode, if the image size of input not equal to model's input, it will auto resize use this fit method,
        default is image.Fit.FIT_FILL for easy coordinate calculation, but for more accurate result, use image.Fit.FIT_CONTAIN is better.
          - copy_result: If set true, will copy result to a new variable; else will use a internal memory, you can only use it until to the next forward.
        Default true to avoid problems, you can set it to false manually to make speed faster.
          - dual_buff_wait: bool type, only for dual_buff mode, if true, will inference this image and wait for result, default false.
          - chw: !!depracated!! This arg will be ignored!!! Please set extra.input_layout in mud file instead.
        chw channel format, forward model with hwc format image input if set to false, default true(chw).
        
        
        Returns: output tensor. In C++, you should manually delete tensors in return value and return value.
        If dual_buff mode, it can be NULL(None in MaixPy) means not ready.
        """
    def inputs_info(self) -> list[LayerInfo]:
        """
        Get model input layer info
        
        Returns: input layer info
        """
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model: direction [in], model file path, model format can be MUD(model universal describe file) file.
        
        
        Returns: error code, if load success, return err::ERR_NONE
        """
    def loaded(self) -> bool:
        """
        Is model loaded
        
        Returns: true if model loaded, else false
        """
    def outputs_info(self) -> list[LayerInfo]:
        """
        Get model output layer info
        
        Returns: output layer info
        """
    def set_dual_buff(self, enable: bool) -> None:
        """
        Enable dual buff or disable dual buff
        
        Args:
          - enable: true to enable, false to disable
        """
class NanoTrack:
    mean: list[float]
    scale: list[float]
    def __init__(self, model: str = '') -> None:
        ...
    def init(self, img: maix._maix.image.Image, x: int, y: int, w: int, h: int) -> None:
        """
        Init tracker, give tacker first target image and target position.
        
        Args:
          - img: Image want to detect, target should be in this image.
          - x: the target position left top coordinate x.
          - y: the target position left top coordinate y.
          - w: the target width.
          - h: the target height.
        """
    def input_format(self) -> maix._maix.image.Format:
        """
        Get input image format
        
        Returns: input image format, image::Format type.
        """
    def input_height(self) -> int:
        """
        Get model input height
        
        Returns: model input size of height
        """
    def input_size(self) -> maix._maix.image.Size:
        """
        Get model input size
        
        Returns: model input size
        """
    def input_width(self) -> int:
        """
        Get model input width
        
        Returns: model input size of width
        """
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model: Model path want to load
        
        
        Returns: err::Err
        """
    def track(self, img: maix._maix.image.Image, threshold: float = 0.9) -> Object:
        """
        Track object acoording to last object position and the init function learned target feature.
        
        Args:
          - img: image to detect object and track, can be any resolution, before detect it will crop a area according to last time target's position.
          - threshold: If score < threshold, will see this new detection is invalid, but remain return this new detecion,  default 0.9.
        
        
        Returns: object, attribute [x, y, w, h] and score are the predict target position and score, points attribute provide more info:
        0~3  [ search_x, search_y, search_w, search_h ]: search area for this time track, based on last correct start position.
        4~5  [ predict_cx, predict_cy]: predict center according to this time input.
        6    [ search_size ]: search_area size based on last correct start position, center is (search_x - search_w / 2, search_y - search_h / 2).
        7    [ predict_template_size ]: template size based on predict target, center is (predict_cx, predict_cy).
        8~11 [ correct_cx, correct_cy, correct_w, correct_h]: latest correct (score > threshold) target position.
        """
class OCR_Box:
    x1: int
    x2: int
    x3: int
    x4: int
    y1: int
    y2: int
    y3: int
    y4: int
    def __init__(self, x1: int = 0, y1: int = 0, x2: int = 0, y2: int = 0, x3: int = 0, y3: int = 0, x4: int = 0, y4: int = 0) -> None:
        ...
    def to_list(self) -> list[int]:
        """
        convert box point to a list type.
        
        Returns: list type, element is int type, value [x1, y1, x2, y2, x3, y3, x4, y4].
        """
class OCR_Object:
    box: OCR_Box
    char_pos: list[int]
    idx_list: list[int]
    score: float
    def __init__(self, box: OCR_Box, idx_list: list[int], char_list: list[str], score: float = 0, char_pos: list[int] = []) -> None:
        ...
    def __str__(self) -> str:
        """
        OCR_Object info to string
        
        Returns: OCR_Object info string
        """
    def char_list(self) -> list[str]:
        """
        Get OCR_Object's charactors, return a list type.
        
        Returns: All charactors in list type.
        """
    def char_str(self) -> str:
        """
        Get OCR_Object's charactors, return a string type.
        
        Returns: All charactors in string type.
        """
    def update_chars(self, char_list: list[str]) -> None:
        """
        Set OCR_Object's charactors
        
        Args:
          - char_list: All charactors in list type.
        """
class OCR_Objects:
    def __getitem__(self, idx: int) -> OCR_Object:
        """
        Get object item
        """
    def __init__(self) -> None:
        ...
    def __iter__(self) -> typing.Iterator:
        ...
    def __len__(self) -> int:
        """
        Get size
        """
    def add(self, box: OCR_Box, idx_list: list[int], char_list: list[str], score: float = 0, char_pos: list[int] = []) -> OCR_Object:
        """
        Add object to objects
        """
    def at(self, idx: int) -> OCR_Object:
        """
        Get object item
        """
    def remove(self, idx: int) -> maix._maix.err.Err:
        """
        Remove object form objects
        """
class Object:
    angle: float
    class_id: int
    h: int
    points: list[int]
    score: float
    seg_mask: maix._maix.image.Image
    w: int
    x: int
    y: int
    def __init__(self, x: int = 0, y: int = 0, w: int = 0, h: int = 0, class_id: int = 0, score: float = 0, points: list[int] = [], angle: float = -9999) -> None:
        ...
    def __str__(self) -> str:
        """
        Object info to string
        
        Returns: Object info string
        """
    def get_obb_points(self) -> list[int]:
        """
        Get OBB(oriented bounding box) points, auto calculated according to x,y,w,h,angle
        """
class ObjectFloat:
    angle: float
    class_id: float
    h: float
    points: list[float]
    score: float
    w: float
    x: float
    y: float
    def __init__(self, x: float = 0, y: float = 0, w: float = 0, h: float = 0, class_id: float = 0, score: float = 0, points: list[float] = [], angle: float = -1) -> None:
        ...
    def __str__(self) -> str:
        """
        Object info to string
        
        Returns: Object info string
        """
class Objects:
    def __getitem__(self, idx: int) -> Object:
        """
        Get object item
        """
    def __init__(self) -> None:
        ...
    def __iter__(self) -> typing.Iterator:
        ...
    def __len__(self) -> int:
        """
        Get size
        """
    def add(self, x: int = 0, y: int = 0, w: int = 0, h: int = 0, class_id: int = 0, score: float = 0, points: list[int] = [], angle: float = -1) -> Object:
        """
        Add object to objects
        """
    def at(self, idx: int) -> Object:
        """
        Get object item
        """
    def remove(self, idx: int) -> maix._maix.err.Err:
        """
        Remove object form objects
        """
class PP_OCR:
    det: bool
    labels: list[str]
    mean: list[float]
    rec: bool
    rec_mean: list[float]
    rec_scale: list[float]
    scale: list[float]
    def __init__(self, model: str = '') -> None:
        ...
    def detect(self, img: maix._maix.image.Image, thresh: float = 0.3, box_thresh: float = 0.6, fit: maix._maix.image.Fit = ..., char_box: bool = False) -> OCR_Objects:
        """
        Detect objects from image
        
        Args:
          - img: Image want to detect, if image's size not match model input's, will auto resize with fit method.
          - thresh: Confidence threshold where pixels have charactor, default 0.3.
          - box_thresh: Box threshold, the box prob higher than this value will be valid, default 0.6.
          - fit: Resize method, default image.Fit.FIT_CONTAIN.
          - char_box: Calculate every charactor's box, default false, if true then you can get charactor's box by nn.OCR_Object's char_boxes attribute.
        
        
        Returns: nn.OCR_Objects type. In C++, you should delete it after use.
        """
    def draw_seg_mask(self, img: maix._maix.image.Image, x: int, y: int, seg_mask: maix._maix.image.Image, threshold: int = 127) -> None:
        """
        Draw segmentation on image
        
        Args:
          - img: image object, maix.image.Image type.
          - seg_mask: segmentation mask image by detect method, a grayscale image
          - threshold: only mask's value > threshold will be draw on image, value from 0 to 255.
        """
    def input_format(self) -> maix._maix.image.Format:
        """
        Get input image format
        
        Returns: input image format, image::Format type.
        """
    def input_height(self) -> int:
        """
        Get model input height
        
        Returns: model input size of height
        """
    def input_size(self) -> maix._maix.image.Size:
        """
        Get model input size
        
        Returns: model input size
        """
    def input_width(self) -> int:
        """
        Get model input width
        
        Returns: model input size of width
        """
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model: Model path want to load
        
        
        Returns: err::Err
        """
    def recognize(self, img: maix._maix.image.Image, box_points: list[int] = []) -> OCR_Object:
        """
        Only recognize, not detect
        
        Args:
          - img: image to recognize chractors, can be a stanrd cropped charactors image,
        if crop image not standard, you can use box_points to assgin where the charactors' 4 corner is.
          - box_points: list type, length must be 8 or 0, default empty means not transfer image to standard image.
        4 points postiion, format: [x1, y1, x2, y2, x3, y3, x4, y4], point 1 at the left-top, point 2 right-top...
          - char_box: Calculate every charactor's box, default false, if true then you can get charactor's box by nn.OCR_Object's char_boxes attribute.
        """
class Qwen:
    post_config: QwenPostConfig
    def __init__(self, model: str) -> None:
        ...
    def cancel(self) -> None:
        """
        Cancel running
        """
    def clear_context(self) -> maix._maix.err.Err:
        """
        Clear context
        
        Returns: error code, if clear success, return err::ERR_NONE
        """
    def get_reply_callback(self) -> typing.Callable[[Qwen, QwenResp], None]:
        """
        Get reply callback
        
        Returns: reply callback
        """
    def get_system_prompt(self) -> str:
        """
        Get system prompt
        
        Returns: system prompt
        """
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model: direction [in], model file path, model format can be MUD(model universal describe file) file.
        
        
        Returns: error code, if load success, return err::ERR_NONE
        """
    def loaded(self) -> bool:
        """
        Is model loaded
        
        Returns: true if model loaded, else false
        """
    def send(self, msg: str) -> QwenResp:
        """
        Send message to model
        
        Args:
          - msg: message to send
        
        
        Returns: model response
        """
    def set_log_level(self, level: ..., color: bool) -> None:
        """
        Set log level
        
        Args:
          - level: log level, @see maix.log.LogLevel
          - color: true to enable color, false to disable color
        """
    def set_reply_callback(self, callback: typing.Callable[[Qwen, QwenResp], None] = None) -> None:
        """
        Set reply callback
        
        Args:
          - callback: reply callback, when token(words) generated, this function will be called,
        so you can get response message in real time in this callback funtion.
        If set to None(nullptr in C++), you can get response after all response message generated.
        """
    def set_system_prompt(self, prompt: str) -> None:
        """
        Set system prompt, will auto call clear_context.
        
        Args:
          - prompt: system prompt
        """
    def unload(self) -> maix._maix.err.Err:
        """
        Unload model
        
        Returns: error code, if unload success, return err::ERR_NONE
        """
    def version(self) -> str:
        """
        Get model version
        
        Returns: model version
        """
class QwenPostConfig:
    enable_repetition_penalty: bool
    enable_temperature: bool
    enable_top_k_sampling: bool
    enable_top_p_sampling: bool
    penalty_window: int
    repetition_penalty: float
    temperature: float
    top_k: int
    top_p: float
class QwenResp:
    err_code: maix._maix.err.Err
    err_msg: str
    msg: str
    msg_new: str
class Retinaface:
    mean: list[float]
    scale: list[float]
    def __init__(self, model: str = '', dual_buff: bool = True) -> None:
        ...
    def detect(self, img: maix._maix.image.Image, conf_th: float = 0.4, iou_th: float = 0.45, fit: maix._maix.image.Fit = ...) -> list[...]:
        """
        Detect objects from image
        
        Args:
          - img: Image want to detect, if image's size not match model input's, will auto resize with fit method.
          - conf_th: Confidence threshold, default 0.4.
          - iou_th: IoU threshold, default 0.45.
          - fit: Resize method, default image.Fit.FIT_CONTAIN.
        
        
        Returns: Object list. In C++, you should delete it after use.
        """
    def input_format(self) -> maix._maix.image.Format:
        """
        Get input image format
        
        Returns: input image format, image::Format type.
        """
    def input_height(self) -> int:
        """
        Get model input height
        
        Returns: model input size of height
        """
    def input_size(self) -> maix._maix.image.Size:
        """
        Get model input size
        
        Returns: model input size
        """
    def input_width(self) -> int:
        """
        Get model input width
        
        Returns: model input size of width
        """
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model: Model path want to load
        
        
        Returns: err::Err
        """
class SelfLearnClassifier:
    label_path: str
    labels: list[str]
    mean: list[float]
    scale: list[float]
    def __init__(self, model: str = '', dual_buff: bool = True) -> None:
        ...
    def add_class(self, img: maix._maix.image.Image, fit: maix._maix.image.Fit = ...) -> None:
        """
        Add a class to recognize
        
        Args:
          - img: Add a image as a new class
          - fit: image resize fit mode, default Fit.FIT_COVER, see image.Fit.
        """
    def add_sample(self, img: maix._maix.image.Image, fit: maix._maix.image.Fit = ...) -> None:
        """
        Add sample, you should call learn method after add some samples to learn classes.
        Sample image can be any of classes we already added.
        
        Args:
          - img: Add a image as a new sample.
        """
    def class_num(self) -> int:
        """
        Get class number
        """
    def classify(self, img: maix._maix.image.Image, fit: maix._maix.image.Fit = ...) -> list[tuple[int, float]]:
        """
        Classify image
        
        Args:
          - img: image, format should match model input_type， or will raise err.Exception
          - fit: image resize fit mode, default Fit.FIT_COVER, see image.Fit.
        
        
        Returns: result, a list of (idx, distance), smaller distance means more similar. In C++, you need to delete it after use.
        """
    def clear(self) -> None:
        """
        Clear all class and samples
        """
    def input_format(self) -> maix._maix.image.Format:
        """
        Get input image format, only for image input
        
        Returns: input image format, image::Format type.
        """
    def input_height(self) -> int:
        """
        Get model input height, only for image input
        
        Returns: model input size of height
        """
    def input_shape(self) -> list[int]:
        """
        Get input shape, if have multiple input, only return first input shape
        
        Returns: input shape, list type
        """
    def input_size(self) -> maix._maix.image.Size:
        """
        Get model input size, only for image input
        
        Returns: model input size
        """
    def input_width(self) -> int:
        """
        Get model input width, only for image input
        
        Returns: model input size of width
        """
    def learn(self) -> int:
        """
        Start auto learn class features from classes image and samples.
        You should call this method after you add some samples.
        
        Returns: learn epoch(times), 0 means learn nothing.
        """
    def load(self, path: str) -> list[str]:
        """
        Load features info from binary file
        
        Args:
          - path: feature info binary file path, e.g. /root/my_classes.bin
        """
    def load_model(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file, model format is .mud,
        MUD file should contain [extra] section, have key-values:
        - model_type: classifier_no_top
        - input_type: rgb or bgr
        - mean: 123.675, 116.28, 103.53
        - scale: 0.017124753831663668, 0.01750700280112045, 0.017429193899782137
        
        Args:
          - model: MUD model path
        
        
        Returns: error code, if load failed, return error code
        """
    def rm_class(self, idx: int) -> maix._maix.err.Err:
        """
        Remove a class
        
        Args:
          - idx: index, value from 0 to class_num();
        """
    def rm_sample(self, idx: int) -> maix._maix.err.Err:
        """
        Remove a sample
        
        Args:
          - idx: index, value from 0 to sample_num();
        """
    def sample_num(self) -> int:
        """
        Get sample number
        """
    def save(self, path: str, labels: list[str] = []) -> maix._maix.err.Err:
        """
        Save features and labels to a binary file
        
        Args:
          - path: file path to save, e.g. /root/my_classes.bin
          - labels: class labels, can be None, or length must equal to class num, or will return err::Err
        
        
        Returns: maix.err.Err if labels exists but length not equal to class num, or save file failed, or class num is 0.
        """
class Speech:
    mean: list[float]
    scale: list[float]
    def __init__(self, model: str = '') -> None:
        ...
    def clear(self) -> None:
        """
        Reset internal cache operation
        """
    def dec_deinit(self, decoder: SpeechDecoder) -> None:
        """
        Deinit the decoder.
        
        Args:
          - decoder: decoder type want to deinit
        can choose between DECODER_RAW, DECODER_DIG, DECODER_LVCSR, DECODER_KWS or DECODER_ALL.
        """
    def dev_type(self) -> SpeechDevice:
        """
        get device type
        
        Returns: nn::SpeechDevice type, see SpeechDevice of this module
        """
    def devive(self, dev_type: SpeechDevice, device_name: str) -> maix._maix.err.Err:
        """
        Reset the device, usually used for PCM/WAV recognition,
        such as identifying the next WAV file.
        
        Args:
          - dev_type: device type want to detect, can choose between WAV, PCM, or MIC.
          - device_name: device name want to detect, can choose a WAV file, a PCM file, or a MIC device name.
        
        
        Returns: err::Err type, if init success, return err::ERR_NONE
        """
    def digit(self, blank: int, callback: typing.Callable[[str, int], None]) -> maix._maix.err.Err:
        """
        Init digit decoder, it will output the Chinese digit recognition results within the last 4 seconds.
        
        Args:
          - blank: If it exceeds this value, insert a '_' in the output result to indicate idle mute.
          - callback: digit decoder user callback.
        
        
        Returns: err::Err type, if init success, return err::ERR_NONE
        """
    def frame_time(self) -> int:
        """
        Get the time of one frame.
        
        Returns: int type, return the time of one frame.
        """
    def init(self, dev_type: SpeechDevice, device_name: str = '') -> maix._maix.err.Err:
        """
        Init the ASR library and select the type and name of the audio device.
        
        Args:
          - dev_type: device type want to detect, can choose between WAV, PCM, or MIC.
          - device_name: device name want to detect, can choose a WAV file, a PCM file, or a MIC device name.
        
        
        Returns: err::Err type, if init success, return err::ERR_NONE
        """
    def kws(self, kw_tbl: list[str], kw_gate: list[float], callback: typing.Callable[[list[float], int], None], auto_similar: bool = True) -> maix._maix.err.Err:
        """
        Init kws decoder, it will output a probability list of all registered keywords in the latest frame,
        users can set their own thresholds for wake-up.
        
        Args:
          - kw_tbl: Keyword list, filled in with spaces separated by pinyin, for example: xiao3 ai4 tong2 xue2
          - kw_gate: kw_gate, keyword probability gate table, the number should be the same as kw_tbl
          - auto_similar: Whether to perform automatic homophone processing,
        setting it to true will automatically calculate the probability by using pinyin with different tones as homophones
          - callback: digit decoder user callback.
        
        
        Returns: err::Err type, if init success, return err::ERR_NONE
        """
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model: Model path want to load
        
        
        Returns: err::Err
        """
    def lvcsr(self, sfst_name: str, sym_name: str, phones_txt: str, words_txt: str, callback: typing.Callable[[tuple[str, str], int], None], beam: float = 8, bg_prob: float = 10, scale: float = 0.5, mmap: bool = False) -> maix._maix.err.Err:
        """
        Init lvcsr decoder, it will output continuous speech recognition results (less than 1024 Chinese characters).
        
        Args:
          - sfst_name: Sfst file path.
          - sym_name: Sym file path (output symbol table).
          - phones_txt: Path to phones.bin (pinyin table).
          - words_txt: Path to words.bin (dictionary table).
          - callback: lvcsr decoder user callback.
          - beam: The beam size for WFST search is set to 8 by default, and it is recommended to be between 3 and 9.
        The larger the size, the larger the search space, and the more accurate but slower the search.
          - bg_prob: The absolute value of the natural logarithm of the default probability value for background pinyin
        outside of BEAM-CNT is set to 10 by default.
          - scale: acoustics_cost = log(pny_prob)*scale.
          - mmap: use mmap to load the WFST decoding image,
        If set to true, the beam should be less than 5.
        
        
        Returns: err::Err type, if init success, return err::ERR_NONE
        """
    def raw(self, callback: typing.Callable[[list[tuple[int, float]], int], None]) -> maix._maix.err.Err:
        """
        Init raw decoder, it will output the prediction results of the original AM.
        
        Args:
          - callback: raw decoder user callback.
        
        
        Returns: err::Err type, if init success, return err::ERR_NONE
        """
    def run(self, frame: int) -> int:
        """
        Run speech recognition, user can run 1 frame at a time and do other processing after running,
        or it can run continuously within a thread and be stopped by an external thread.
        
        Args:
          - frame: The number of frames per run.
        
        
        Returns: int type, return actual number of frames in the run.
        """
    def similar(self, pny: str, similar_pnys: list[str]) -> maix._maix.err.Err:
        """
        Manually register mute words, and each pinyin can register up to 10 homophones,
        please note that using this interface to register homophones will overwrite,
        the homophone table automatically generated in the "automatic homophone processing" feature.
        
        Args:
          - dev_type: device type want to detect, can choose between WAV, PCM, or MIC.
          - device_name: device name want to detect, can choose a WAV file, a PCM file, or a MIC device name.
        
        
        Returns: err::Err type, if init success, return err::ERR_NONE
        """
    def skip_frames(self, num: int) -> None:
        """
        Run some frames and drop, this can be used to avoid
        incorrect recognition results when switching decoders.
        
        Args:
          - num: number of frames to run and drop
        """
class SpeechDecoder:
    """
    Members:
    
      DECODER_RAW
    
      DECODER_DIG
    
      DECODER_LVCSR
    
      DECODER_KWS
    
      DECODER_ALL
    """
    DECODER_ALL: typing.ClassVar[SpeechDecoder]  # value = <SpeechDecoder.DECODER_ALL: 65535>
    DECODER_DIG: typing.ClassVar[SpeechDecoder]  # value = <SpeechDecoder.DECODER_DIG: 2>
    DECODER_KWS: typing.ClassVar[SpeechDecoder]  # value = <SpeechDecoder.DECODER_KWS: 8>
    DECODER_LVCSR: typing.ClassVar[SpeechDecoder]  # value = <SpeechDecoder.DECODER_LVCSR: 4>
    DECODER_RAW: typing.ClassVar[SpeechDecoder]  # value = <SpeechDecoder.DECODER_RAW: 1>
    __members__: typing.ClassVar[dict[str, SpeechDecoder]]  # value = {'DECODER_RAW': <SpeechDecoder.DECODER_RAW: 1>, 'DECODER_DIG': <SpeechDecoder.DECODER_DIG: 2>, 'DECODER_LVCSR': <SpeechDecoder.DECODER_LVCSR: 4>, 'DECODER_KWS': <SpeechDecoder.DECODER_KWS: 8>, 'DECODER_ALL': <SpeechDecoder.DECODER_ALL: 65535>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: int) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: int) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class SpeechDevice:
    """
    Members:
    
      DEVICE_NONE
    
      DEVICE_PCM
    
      DEVICE_MIC
    
      DEVICE_WAV
    """
    DEVICE_MIC: typing.ClassVar[SpeechDevice]  # value = <SpeechDevice.DEVICE_MIC: 1>
    DEVICE_NONE: typing.ClassVar[SpeechDevice]  # value = <SpeechDevice.DEVICE_NONE: -1>
    DEVICE_PCM: typing.ClassVar[SpeechDevice]  # value = <SpeechDevice.DEVICE_PCM: 0>
    DEVICE_WAV: typing.ClassVar[SpeechDevice]  # value = <SpeechDevice.DEVICE_WAV: 2>
    __members__: typing.ClassVar[dict[str, SpeechDevice]]  # value = {'DEVICE_NONE': <SpeechDevice.DEVICE_NONE: -1>, 'DEVICE_PCM': <SpeechDevice.DEVICE_PCM: 0>, 'DEVICE_MIC': <SpeechDevice.DEVICE_MIC: 1>, 'DEVICE_WAV': <SpeechDevice.DEVICE_WAV: 2>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: int) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: int) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class Whisper:
    def __init__(self, model: str = '', language: str = 'zh') -> None:
        ...
    def input_pcm_bits_per_frame(self) -> int:
        """
        Get input pcm bits per frame
        
        Returns: input pcm bits per frame
        """
    def input_pcm_channels(self) -> int:
        """
        Get input pcm channels
        
        Returns: input pcm channels
        """
    def input_pcm_samplerate(self) -> int:
        """
        Get input pcm samplerate
        
        Returns: input pcm samplerate
        """
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model: Model path want to load
        
        
        Returns: err::Err
        """
    def transcribe(self, file: str) -> str:
        """
        Transcribe audio file to text
        
        Args:
          - file: Pass in an audio file, supporting files in wav,pcm format.
        
        
        Returns: The output result after automatic speech recognition.
        """
    def transcribe_raw(self, pcm: maix.Bytes(bytes), sample_rate: int = 16000, channels: int = 1, bits_per_frame: int = 16) -> str:
        """
        Transcribe pcm data to text
        
        Args:
          - pcm: RAW data
        
        
        Returns: The output result after automatic speech recognition.
        """
class YOLO11:
    label_path: str
    labels: list[str]
    mean: list[float]
    scale: list[float]
    def __init__(self, model: str = '', dual_buff: bool = True) -> None:
        ...
    def detect(self, img: maix._maix.image.Image, conf_th: float = 0.5, iou_th: float = 0.45, fit: maix._maix.image.Fit = ..., keypoint_th: float = 0.5, sort: int = 0) -> ...:
        """
        Detect objects from image
        
        Args:
          - img: Image want to detect, if image's size not match model input's, will auto resize with fit method.
          - conf_th: Confidence threshold, default 0.5.
          - iou_th: IoU threshold, default 0.45.
          - fit: Resize method, default image.Fit.FIT_CONTAIN.
          - keypoint_th: keypoint threshold, default 0.5, only for yolo11-pose model.
          - sort: sort result according to object size, default 0 means not sort, 1 means bigger in front, -1 means smaller in front.
        
        
        Returns: Object list. In C++, you should delete it after use.
        If model is yolo11-pose, object's points have value, and if points' value < 0 means that point is invalid(conf < keypoint_th).
        """
    def draw_pose(self, img: maix._maix.image.Image, points: list[int], radius: int = 4, color: maix._maix.image.Color = ..., colors: list[maix._maix.image.Color] = [], body: bool = True, close: bool = False) -> None:
        """
        Draw pose keypoints on image
        
        Args:
          - img: image object, maix.image.Image type.
          - points: keypoits, int list type, [x, y, x, y ...]
          - radius: radius of points.
          - color: color of points.
          - colors: assign colors for points, list type, element is image.Color object.
          - body: true, if points' length is 17*2 and body is ture, will draw lines as human body, if set to false won't draw lines, default true.
          - close: connect all points to close a polygon, default false.
        """
    def draw_seg_mask(self, img: maix._maix.image.Image, x: int, y: int, seg_mask: maix._maix.image.Image, threshold: int = 127) -> None:
        """
        Draw segmentation on image
        
        Args:
          - img: image object, maix.image.Image type.
          - seg_mask: segmentation mask image by detect method, a grayscale image
          - threshold: only mask's value > threshold will be draw on image, value from 0 to 255.
        """
    def input_format(self) -> maix._maix.image.Format:
        """
        Get input image format
        
        Returns: input image format, image::Format type.
        """
    def input_height(self) -> int:
        """
        Get model input height
        
        Returns: model input size of height
        """
    def input_size(self) -> maix._maix.image.Size:
        """
        Get model input size
        
        Returns: model input size
        """
    def input_width(self) -> int:
        """
        Get model input width
        
        Returns: model input size of width
        """
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model: Model path want to load
        
        
        Returns: err::Err
        """
class YOLOWorld:
    labels: list[str]
    mean: list[float]
    scale: list[float]
    @staticmethod
    def learn_text_feature(model: str, labels: list[str], feature_path: str, labels_path: str) -> maix._maix.err.Err:
        """
        Set detector class labels dynamically, will generate class text feature and save to text_feature path set in load method or constructor.
        
        Args:
          - labels: class labels you want to recognize, list type. e.g. ["person", "car", "cat"]
        
        
        Returns: err::Err
        """
    def __init__(self, model: str = '', text_feature: str = '', labels: str = '', dual_buff: bool = True) -> None:
        ...
    def detect(self, img: maix._maix.image.Image, conf_th: float = 0.5, iou_th: float = 0.45, fit: maix._maix.image.Fit = ..., sort: int = 0) -> Objects:
        """
        Detect objects from image
        
        Args:
          - img: Image want to detect, if image's size not match model input's, will auto resize with fit method.
          - conf_th: Confidence threshold, default 0.5.
          - iou_th: IoU threshold, default 0.45.
          - fit: Resize method, default image.Fit.FIT_CONTAIN.
          - sort: sort result according to object size, default 0 means not sort, 1 means bigger in front, -1 means smaller in front.
        
        
        Returns: Object list. In C++, you should delete it after use.
        """
    def input_format(self) -> maix._maix.image.Format:
        """
        Get input image format
        
        Returns: input image format, image::Format type.
        """
    def input_height(self) -> int:
        """
        Get model input height
        
        Returns: model input size of height
        """
    def input_size(self) -> maix._maix.image.Size:
        """
        Get model input size
        
        Returns: model input size
        """
    def input_width(self) -> int:
        """
        Get model input width
        
        Returns: model input size of width
        """
    def load(self, model: str, text_feature: str, labels: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model: Model path want to load
          - text_feature: Class text feature bin file path.
          - labels: Class labels or labels file path.
        If string class labels: labels split by comma, e.g. "person, car, cat".
        If file path: labels file path, each line is a label.
        
        
        Returns: err::Err
        """
class YOLOv5:
    anchors: list[float]
    label_path: str
    labels: list[str]
    mean: list[float]
    scale: list[float]
    def __init__(self, model: str = '', dual_buff: bool = True) -> None:
        ...
    def detect(self, img: maix._maix.image.Image, conf_th: float = 0.5, iou_th: float = 0.45, fit: maix._maix.image.Fit = ..., sort: int = 0) -> list[Object]:
        """
        Detect objects from image
        
        Args:
          - img: Image want to detect, if image's size not match model input's, will auto resize with fit method.
          - conf_th: Confidence threshold, default 0.5.
          - iou_th: IoU threshold, default 0.45.
          - fit: Resize method, default image.Fit.FIT_CONTAIN.
          - sort: sort result according to object size, default 0 means not sort, 1 means bigger in front, -1 means smaller in front.
        
        
        Returns: Object list. In C++, you should delete it after use.
        """
    def input_format(self) -> maix._maix.image.Format:
        """
        Get input image format
        
        Returns: input image format, image::Format type.
        """
    def input_height(self) -> int:
        """
        Get model input height
        
        Returns: model input size of height
        """
    def input_size(self) -> maix._maix.image.Size:
        """
        Get model input size
        
        Returns: model input size
        """
    def input_width(self) -> int:
        """
        Get model input width
        
        Returns: model input size of width
        """
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model: Model path want to load
        
        
        Returns: err::Err
        """
class YOLOv8:
    label_path: str
    labels: list[str]
    mean: list[float]
    scale: list[float]
    def __init__(self, model: str = '', dual_buff: bool = True) -> None:
        ...
    def detect(self, img: maix._maix.image.Image, conf_th: float = 0.5, iou_th: float = 0.45, fit: maix._maix.image.Fit = ..., keypoint_th: float = 0.5, sort: int = 0) -> Objects:
        """
        Detect objects from image
        
        Args:
          - img: Image want to detect, if image's size not match model input's, will auto resize with fit method.
          - conf_th: Confidence threshold, default 0.5.
          - iou_th: IoU threshold, default 0.45.
          - fit: Resize method, default image.Fit.FIT_CONTAIN.
          - keypoint_th: keypoint threshold, default 0.5, only for yolov8-pose model.
          - sort: sort result according to object size, default 0 means not sort, 1 means bigger in front, -1 means smaller in front.
        
        
        Returns: Object list. In C++, you should delete it after use.
        If model is yolov8-pose, object's points have value, and if points' value < 0 means that point is invalid(conf < keypoint_th).
        """
    def draw_pose(self, img: maix._maix.image.Image, points: list[int], radius: int = 4, color: maix._maix.image.Color = ..., colors: list[maix._maix.image.Color] = [], body: bool = True, close: bool = False) -> None:
        """
        Draw pose keypoints on image
        
        Args:
          - img: image object, maix.image.Image type.
          - points: keypoits, int list type, [x, y, x, y ...]
          - radius: radius of points.
          - color: color of points.
          - colors: assign colors for points, list type, element is image.Color object.
          - body: true, if points' length is 17*2 and body is ture, will draw lines as human body, if set to false won't draw lines, default true.
          - close: connect all points to close a polygon, default false.
        """
    def draw_seg_mask(self, img: maix._maix.image.Image, x: int, y: int, seg_mask: maix._maix.image.Image, threshold: int = 127) -> None:
        """
        Draw segmentation on image
        
        Args:
          - img: image object, maix.image.Image type.
          - seg_mask: segmentation mask image by detect method, a grayscale image
          - threshold: only mask's value > threshold will be draw on image, value from 0 to 255.
        """
    def input_format(self) -> maix._maix.image.Format:
        """
        Get input image format
        
        Returns: input image format, image::Format type.
        """
    def input_height(self) -> int:
        """
        Get model input height
        
        Returns: model input size of height
        """
    def input_size(self) -> maix._maix.image.Size:
        """
        Get model input size
        
        Returns: model input size
        """
    def input_width(self) -> int:
        """
        Get model input width
        
        Returns: model input size of width
        """
    def load(self, model: str) -> maix._maix.err.Err:
        """
        Load model from file
        
        Args:
          - model: Model path want to load
        
        
        Returns: err::Err
        """
