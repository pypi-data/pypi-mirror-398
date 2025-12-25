# from dataclasses import dataclass
# from typing import List

# from validated_dc import ValidatedDC
# import json

# @dataclass

from typing import List, Optional

VinInput = {
    'vin': str,
}

PlateDecoderParams = {
    'plate': str,
    'country': str,
    'state': Optional[str],
    'district' : Optional[str],
}

ImageInput = {
    'make': str,
    'model': str,
    'year': Optional[str],
    'trim': Optional[str],
    'color': Optional[str],
    'transparent': Optional[bool],
    'angle': Optional[str],
    'photoType': Optional[str],
    'size': Optional[str],
    'license': Optional[str],
}

ObdcodesdecoderInput = {
    'code': str,
}

PlateImageRecognitionInput = {
    'upload_url': str,
}

VinOcrInput = {
    'upload_url': str,
}

YearMakeModelInput = {
    "year": str,
    "make": str,
    "model": str,
    "trim": Optional[str],
}

SpecsInput = {
    'vin': str,
    'deepData': Optional[bool],
    'disableIntVINDecoding': Optional[bool],
}

LienAndTheftInput = {
    'vin': str,
}