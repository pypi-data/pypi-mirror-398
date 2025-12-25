# 🚗 CarsXE API (Python Package)

[![PyPI version](https://img.shields.io/pypi/v/carsxe.svg?cacheSeconds=0)](https://pypi.org/project/carsxe/)

**CarsXE** is a powerful and developer-friendly API that gives you instant access to a wide range of vehicle data. From VIN decoding and market value estimation to vehicle history, images, OBD code explanations, and plate recognition, CarsXE provides everything you need to build automotive applications at scale.

🌐 **Website:** [https://api.carsxe.com](https://api.carsxe.com)  
📄 **Docs:** [https://api.carsxe.com/docs](https://api.carsxe.com/docs)  
📦 **All Products:** [https://api.carsxe.com/all-products](https://api.carsxe.com/all-products)

To get started with the CarsXE API, follow these steps:

1. **Sign up for a CarsXE account:**

   - [Register here](https://api.carsxe.com/register)
   - Add a [payment method](https://api.carsxe.com/dashboard/billing#payment-methods) to activate your subscription and get your API key.

2. **Install the CarsXE pip package:**

   Run this command in your terminal:

   ```bash
   pip install carsxe
   ```

3. **Import the CarsXE API into your code:**

   ```python
   from carsxe_api import CarsXE
   ```

4. **Initialize the API with your API key:**

   ```python
   API_KEY = 'YOUR_API_KEY'
   carsxe = CarsXE(API_KEY)
   ```

5. **Use the various endpoint methods provided by the API to access the data you need.**

## Usage

```python
vin = 'WBAFR7C57CC811956'

try:
    vehicle = carsxe.specs({"vin": vin})
    print(vehicle["input"]["vin"])
except Exception as error:
    print(f"Error: {error}")
```

---

## 📚 Endpoints

The CarsXE API provides the following endpoint methods:

### `specs` – Decode VIN & get full vehicle specifications

**Required:**

- `vin`

**Optional:**

- `deepdata`
- `disableIntVINDecoding`

**Example:**

```python
vehicle = carsxe.specs({"vin": "WBAFR7C57CC811956"})
```

---

### `int_vin_decoder` – Decode VIN with worldwide support

**Required:**

- `vin`

**Optional:**

- None

**Example:**

```python
intvin = carsxe.int_vin_decoder({"vin": "WF0MXXGBWM8R43240"})
```

---

### `plate_decoder` – Decode license plate info (plate, country)

**Required:**

- `plate`
- `country` (always required except for US, where it is optional and defaults to 'US')

**Optional:**

- `state` (required for some countries, e.g. US, AU, CA)
- `district` (required for Pakistan)

> **Note:**
>
> - The `state` parameter is required only when applicable (for
>   specific countries such as US, AU, CA, etc.).
> - For Pakistan (`country='pk'`), both `state` and `district`
>   are required.

**Example:**

```python
decoded_plate = carsxe.plate_decoder({"plate": "7XER187", "state": "CA", "country": "US"})
```

---

### `market_value` – Estimate vehicle market value based on VIN

**Required:**

- `vin`

**Optional:**

- `state`

**Example:**

```python
marketvalue = carsxe.market_value({"vin": "WBAFR7C57CC811956"})
```

---

### `history` – Retrieve vehicle history

**Required:**

- `vin`

**Optional:**

- None

**Example:**

```python
history = carsxe.history({"vin": "WBAFR7C57CC811956"})
```

---

### `images` – Fetch images by make, model, year, trim

**Required:**

- `make`
- `model`

**Optional:**

- `year`
- `trim`
- `color`
- `transparent`
- `angle`
- `photoType`
- `size`
- `license`

**Example:**

```python
images = carsxe.images({"make": "BMW", "model": "X5", "year": "2019"})
```

---

### `recalls` – Get safety recall data for a VIN

**Required:**

- `vin`

**Optional:**

- None

**Example:**

```python
recalls = carsxe.recalls({"vin": "1C4JJXR64PW696340"})
```

---

### `plate_image_recognition` – Read & decode plates from images

**Required:**

- `upload_url`

**Optional:**

- None

**Example:**

```python
plateimg = carsxe.plate_image_recognition({"upload_url": "https://api.carsxe.com/img/apis/plate_recognition.JPG"})
```

---

### `vin_ocr` – Extract VINs from images using OCR

**Required:**

- `upload_url`

**Optional:**

- None

**Example:**

```python
vinocr = carsxe.vin_ocr({"upload_url": "https://api.carsxe.com/img/apis/plate_recognition.JPG"})
```

---

### `year_make_model` – Query vehicle by year, make, model and trim (optional)

**Required:**

- `year`
- `make`
- `model`

**Optional:**

- `trim`

**Example:**

```python
yymm = carsxe.year_make_model({"year": "2012", "make": "BMW", "model": "5 Series"})
```

---

### `obd_codes_decoder` – Decode OBD error/diagnostic codes

**Required:**

- `code`

**Optional:**

- None

**Example:**

```python
obdcode = carsxe.obd_codes_decoder({"code": "P0115"})
```

---

### `lien_and_theft` – Get lien and theft information for a VIN

**Required:**

- `vin`

**Optional:**

- None

**Example:**

```python
lien_and_theft = carsxe.lien_and_theft({"vin": "2C3CDXFG1FH762860"})
```

---

## Notes & Best Practices

- **Parameter requirements:** Each endpoint requires specific parameters—see the Required/Optional fields above.
- **Return values:** All responses are Python dictionaries for easy access and manipulation.
- **Error handling:** Use try/except blocks to gracefully handle API errors.
- **More info:** For advanced usage and full details, visit the [official API documentation](https://api.carsxe.com/docs).

---

## Overall

CarsXE API provides a wide range of powerful, easy-to-use tools for accessing and integrating vehicle data into your applications and services. Whether you're a developer or a business owner, you can quickly get the information you need to take your projects to the next level—without hassle or inconvenience.
