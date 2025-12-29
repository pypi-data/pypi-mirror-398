# revengai.FirmwareApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_binaries_for_firmware_task**](FirmwareApi.md#get_binaries_for_firmware_task) | **GET** /v2/firmware/get-binaries/{task_id} | Upload firmware for unpacking
[**upload_firmware**](FirmwareApi.md#upload_firmware) | **POST** /v2/firmware | Upload firmware for unpacking


# **get_binaries_for_firmware_task**
> object get_binaries_for_firmware_task(task_id)

Upload firmware for unpacking

Uploads a firmware file and begins a 'Firmware Unpacker' task. Returns a result identifier, which can be used to poll for the response.

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.reveng.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = revengai.Configuration(
    host = "https://api.reveng.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: APIKey
configuration.api_key['APIKey'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['APIKey'] = 'Bearer'

# Enter a context with an instance of the API client
with revengai.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = revengai.FirmwareApi(api_client)
    task_id = 'task_id_example' # str | 

    try:
        # Upload firmware for unpacking
        api_response = api_instance.get_binaries_for_firmware_task(task_id)
        print("The response of FirmwareApi->get_binaries_for_firmware_task:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FirmwareApi->get_binaries_for_firmware_task: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **task_id** | **str**|  | 

### Return type

**object**

### Authorization

[APIKey](../README.md#APIKey)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Invalid request parameters |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **upload_firmware**
> object upload_firmware(file, password=password)

Upload firmware for unpacking

Uploads a firmware file and begins a 'Firmware Unpacker' task. Returns a result identifier, which can be used to poll for the response.

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.reveng.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = revengai.Configuration(
    host = "https://api.reveng.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: APIKey
configuration.api_key['APIKey'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['APIKey'] = 'Bearer'

# Enter a context with an instance of the API client
with revengai.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = revengai.FirmwareApi(api_client)
    file = None # bytearray | 
    password = 'password_example' # str |  (optional)

    try:
        # Upload firmware for unpacking
        api_response = api_instance.upload_firmware(file, password=password)
        print("The response of FirmwareApi->upload_firmware:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FirmwareApi->upload_firmware: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **file** | **bytearray**|  | 
 **password** | **str**|  | [optional] 

### Return type

**object**

### Authorization

[APIKey](../README.md#APIKey)

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Successful Response |  -  |
**422** | Invalid request parameters |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

