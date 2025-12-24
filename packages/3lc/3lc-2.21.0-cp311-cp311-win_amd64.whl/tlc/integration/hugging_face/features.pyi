import datasets
from tlc.client.sample_type import AtomicSampleType as AtomicSampleType, Bool as Bool, CategoricalLabel as CategoricalLabel, Float as Float, Int as Int, List as List, PILImage as PILImage, SampleType as SampleType, String as String, StringKeyDict as StringKeyDict
from tlc.core.builtins.constants.string_roles import STRING_ROLE_MULTILINE as STRING_ROLE_MULTILINE

def features_to_sample_type(features: datasets.Features) -> SampleType:
    """
    Convert a Hugging Face dataset's features to a 3LC SampleType.

    :param features: The features of a Hugging Face dataset.
    :return: The corresponding 3LC SampleType.
    :raises NotImplementedError: If an unsupported feature type is encountered.
    """
