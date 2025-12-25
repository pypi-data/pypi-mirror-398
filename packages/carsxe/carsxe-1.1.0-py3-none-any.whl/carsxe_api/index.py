import requests
from typing import Optional
from .types import (
    VinInput,
    PlateDecoderParams,
    ImageInput,
    ObdcodesdecoderInput,
    PlateImageRecognitionInput,
    VinOcrInput,
    YearMakeModelInput,
    SpecsInput,
    LienAndTheftInput,
)

def get_required_optional(params_dict, params=None):
    """
    Given a parameter definition dict (e.g., VinInput), returns (required, optional) lists of keys.
    For PlateDecoderParams, applies country-specific logic:
        - If country is PK or Pakistan, require both state and district.
        - For all other countries, require 'state'.
    Also checks that all required attributes are present in params (if provided).
    """
    required = [k for k, v in params_dict.items() if v != Optional[str] and v != Optional[bool]]
    optional = [k for k, v in params_dict.items() if v == Optional[str] or v == Optional[bool]]
    if params_dict is PlateDecoderParams and params is not None:
        country = params.get('country', 'US').lower() if params.get('country') else 'us'
        if country == 'pk':
            required.append('state')
            required.append('district')
        else:
            if 'state' not in required:
                required.append('state')
    if params is not None:
        for attr in required:
            if attr not in params or params[attr] is None:
                raise ValueError(f"Missing required parameter: {attr}")
    return required, optional

def greeter(name: str) -> str:
    return f"CarsXE API says hello {name}!"

class CarsXE:

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_api_key(self):
        return self.api_key

    def get_api_base_url(self):
        return 'https://api.carsxe.com'

    def _build_url(self, endpoint: str, params: dict, required: list, optional: list):
        query = {k: v for k, v in params.items() if k in required + optional and v is not None}
        query['key'] = self.get_api_key()
        query['source'] = "pip"
        return f"{self.get_api_base_url()}/{endpoint}", query

    def _get(self, endpoint: str, params: dict, param_def: dict):
        required, optional = get_required_optional(param_def, params)
        url, query = self._build_url(endpoint, params, required, optional)
        response = requests.get(url, params=query)
        return response.json()

    def specs(self, params: dict):
        return self._get('specs', params, SpecsInput)

    def int_vin_decoder(self, params: dict):
        return self._get('v1/international-vin-decoder', params, VinInput)

    def recalls(self, params: dict):
        return self._get('v1/recalls', params, VinInput)

    def plate_decoder(self, params: dict):
        if 'country' not in params or not params['country']:
            params['country'] = 'US'
        return self._get('v2/platedecoder', params, PlateDecoderParams)

    def images(self, params: dict):
        return self._get('images', params, ImageInput)

    def market_value(self, params: dict):
        # Only 'state' is optional
        required, optional = get_required_optional(VinInput, params)
        optional = list(set(optional + ['state']))
        url, query = self._build_url('v2/marketvalue', params, required, optional)
        response = requests.get(url, params=query)
        return response.json()

    def history(self, params: dict):
        return self._get('history', params, VinInput)

    def plate_image_recognition(self, params: dict):
        url = f"{self.get_api_base_url()}/platerecognition?key={self.get_api_key()}&source=pip"
        if 'upload_url' not in params:
            raise ValueError("Missing required parameter: upload_url")
        data = {'upload_url': params['upload_url']}
        response = requests.post(url, json=data)
        return response.json()

    def vin_ocr(self, params: dict):
        url = f"{self.get_api_base_url()}/v1/vinocr?key={self.get_api_key()}&source=pip"
        if 'upload_url' not in params:
            raise ValueError("Missing required parameter: upload_url")
        data = {'upload_url': params['upload_url']}
        response = requests.post(url, json=data)
        return response.json()

    def year_make_model(self, params: dict):
        return self._get('v1/ymm', params, YearMakeModelInput)

    def obd_codes_decoder(self, params: dict):
        return self._get('obdcodesdecoder', params, ObdcodesdecoderInput)

    def lien_and_theft(self, params: dict):
        return self._get('v1/lien-theft', params, LienAndTheftInput)
