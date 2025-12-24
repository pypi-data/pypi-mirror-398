from _typeshed import Incomplete
from super_gradients.training.pipelines.pipelines import Pipeline
from super_gradients.training.processing.processing import Processing, ProcessingMetadata as ProcessingMetadata
from super_gradients.training.utils.predict.prediction_results import ImagePrediction as ImagePrediction, ImagesPredictions as ImagesPredictions, Prediction as Prediction
from torch.nn import Module as Module

class EmbeddingsPipeline(Pipeline):
    use_global_pooling: Incomplete
    image_processor: Incomplete
    def __init__(self, model: Module, image_processor: Processing | list[Processing] = None, device: str | None = None, fp16: bool = True, use_global_pooling: bool = True) -> None: ...
