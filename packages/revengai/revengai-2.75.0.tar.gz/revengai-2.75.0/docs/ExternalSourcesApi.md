# revengai.ExternalSourcesApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_external_task_vt**](ExternalSourcesApi.md#create_external_task_vt) | **POST** /v2/analysis/{analysis_id}/external/vt | Pulls data from VirusTotal
[**get_vt_data**](ExternalSourcesApi.md#get_vt_data) | **GET** /v2/analysis/{analysis_id}/external/vt | Get VirusTotal data
[**get_vt_task_status**](ExternalSourcesApi.md#get_vt_task_status) | **GET** /v2/analysis/{analysis_id}/external/vt/status | Check the status of VirusTotal data retrieval


# **create_external_task_vt**
> BaseResponseStr create_external_task_vt(analysis_id)

Pulls data from VirusTotal

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_str import BaseResponseStr
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
    api_instance = revengai.ExternalSourcesApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Pulls data from VirusTotal
        api_response = api_instance.create_external_task_vt(analysis_id)
        print("The response of ExternalSourcesApi->create_external_task_vt:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ExternalSourcesApi->create_external_task_vt: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

### Return type

[**BaseResponseStr**](BaseResponseStr.md)

### Authorization

[APIKey](../README.md#APIKey)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**202** | Successful Response |  -  |
**422** | Invalid request parameters |  -  |
**409** | Request already queued |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_vt_data**
> BaseResponseExternalResponse get_vt_data(analysis_id)

Get VirusTotal data

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_external_response import BaseResponseExternalResponse
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
    api_instance = revengai.ExternalSourcesApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Get VirusTotal data
        api_response = api_instance.get_vt_data(analysis_id)
        print("The response of ExternalSourcesApi->get_vt_data:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ExternalSourcesApi->get_vt_data: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

### Return type

[**BaseResponseExternalResponse**](BaseResponseExternalResponse.md)

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
**404** | No data retrieved from VirusTotal for the given analysis_id |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_vt_task_status**
> BaseResponseTaskResponse get_vt_task_status(analysis_id)

Check the status of VirusTotal data retrieval

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_task_response import BaseResponseTaskResponse
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
    api_instance = revengai.ExternalSourcesApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Check the status of VirusTotal data retrieval
        api_response = api_instance.get_vt_task_status(analysis_id)
        print("The response of ExternalSourcesApi->get_vt_task_status:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ExternalSourcesApi->get_vt_task_status: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

### Return type

[**BaseResponseTaskResponse**](BaseResponseTaskResponse.md)

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

