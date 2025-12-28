import base64
import datetime
import hashlib
import hmac
import io
import logging

import requests


def sign_request(method, bucket, object_key, headers, access_key_id, access_key_secret):
    # This is a simplified representation. Actual OSS signing is more complex.
    # It involves creating a canonicalized resource and headers string.
    # Refer to Alibaba Cloud OSS documentation for precise signing details.

    canonical_string = f"{method}\n"
    canonical_string += f"{headers.get('Content-MD5', '')}\n"
    canonical_string += f"{headers.get('Content-Type', '')}\n"
    canonical_string += f"{headers.get('Date', '')}\n"

    # Add canonicalized OSS headers if present (e.g., x-oss-meta-*)
    for key in sorted(headers.keys()):
        if key.lower().startswith("x-oss-"):
            canonical_string += f"{key.lower()}:{headers[key]}\n"

    canonical_string += f"/{bucket}/{object_key}"

    h = hmac.new(
        access_key_secret.encode("utf-8"),
        canonical_string.encode("utf-8"),
        hashlib.sha1,
    )
    signature = base64.b64encode(h.digest()).decode("utf-8")
    return f"OSS {access_key_id}:{signature}"


def upload_file_without_sdk(
    file_content: io.BytesIO,
    bucket,
    object_key,
    endpoint,
    access_key_id,
    access_key_secret,
    security_token,
    **kwargs,
):
    logging.info(f"Uploading file to {bucket}.{endpoint}/{object_key}")
    date = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    headers = {
        "Host": f"{bucket}.{endpoint}",
        "Date": date,
        "Content-Type": "application/octet-stream",
        "Content-Length": str(file_content.getbuffer().nbytes),
        "x-oss-security-token": security_token,
    }

    headers["Authorization"] = sign_request(
        "PUT", bucket, object_key, headers, access_key_id, access_key_secret
    )

    url = f"https://{bucket}.{endpoint}/{object_key}"

    try:
        response = requests.put(url, headers=headers, data=file_content)
        response.raise_for_status()  # Raise an exception for bad status codes
        logging.info(f"File '{object_key}' uploaded successfully.")
        return url
    except requests.exceptions.RequestException as e:
        logging.error(f"Error uploading file: {e}")
        if response is not None:
            logging.error(f"Response content: {response.text}")
        raise e


def parse_upload_token(resp) -> dict:
    logging.debug(f"parsing token resp: {resp}")
    if "data" not in resp:
        logging.error(f"Invalid response, data not found: {resp}")
        raise ValueError(f"Invalid response: {resp}")
    data = resp["data"]
    if "file" not in data:
        logging.error(f"Invalid response, file not found: {resp}")
        raise ValueError(f"Invalid response: {resp}")
    file = data["file"]
    if "storage" not in data:
        logging.error(f"Invalid response, storage not found: {resp}")
        raise ValueError(f"Invalid response: {resp}")
    storage = data["storage"]
    return file | storage
