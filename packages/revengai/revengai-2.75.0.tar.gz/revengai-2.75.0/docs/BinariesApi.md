# revengai.BinariesApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**download_zipped_binary**](BinariesApi.md#download_zipped_binary) | **GET** /v2/binaries/{binary_id}/download-zipped | Downloads a zipped binary with password protection
[**get_binary_additional_details**](BinariesApi.md#get_binary_additional_details) | **GET** /v2/binaries/{binary_id}/additional-details | Gets the additional details of a binary
[**get_binary_details**](BinariesApi.md#get_binary_details) | **GET** /v2/binaries/{binary_id}/details | Gets the details of a binary
[**get_binary_die_info**](BinariesApi.md#get_binary_die_info) | **GET** /v2/binaries/{binary_id}/die-info | Gets the die info of a binary
[**get_binary_externals**](BinariesApi.md#get_binary_externals) | **GET** /v2/binaries/{binary_id}/externals | Gets the external details of a binary
[**get_related_binaries**](BinariesApi.md#get_related_binaries) | **GET** /v2/binaries/{binary_id}/related | Gets the related binaries of a binary.


# **download_zipped_binary**
> object download_zipped_binary(binary_id)

Downloads a zipped binary with password protection

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
    api_instance = revengai.BinariesApi(api_client)
    binary_id = 56 # int | 

    try:
        # Downloads a zipped binary with password protection
        api_response = api_instance.download_zipped_binary(binary_id)
        print("The response of BinariesApi->download_zipped_binary:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BinariesApi->download_zipped_binary: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **binary_id** | **int**|  | 

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

# **get_binary_additional_details**
> BaseResponseBinaryAdditionalResponse get_binary_additional_details(binary_id)

Gets the additional details of a binary

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_binary_additional_response import BaseResponseBinaryAdditionalResponse
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
    api_instance = revengai.BinariesApi(api_client)
    binary_id = 56 # int | 

    try:
        # Gets the additional details of a binary
        api_response = api_instance.get_binary_additional_details(binary_id)
        print("The response of BinariesApi->get_binary_additional_details:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BinariesApi->get_binary_additional_details: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **binary_id** | **int**|  | 

### Return type

[**BaseResponseBinaryAdditionalResponse**](BaseResponseBinaryAdditionalResponse.md)

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

# **get_binary_details**
> BaseResponseBinaryDetailsResponse get_binary_details(binary_id)

Gets the details of a binary

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_binary_details_response import BaseResponseBinaryDetailsResponse
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
    api_instance = revengai.BinariesApi(api_client)
    binary_id = 56 # int | 

    try:
        # Gets the details of a binary
        api_response = api_instance.get_binary_details(binary_id)
        print("The response of BinariesApi->get_binary_details:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BinariesApi->get_binary_details: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **binary_id** | **int**|  | 

### Return type

[**BaseResponseBinaryDetailsResponse**](BaseResponseBinaryDetailsResponse.md)

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

# **get_binary_die_info**
> BaseResponseListDieMatch get_binary_die_info(binary_id)

Gets the die info of a binary

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_list_die_match import BaseResponseListDieMatch
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
    api_instance = revengai.BinariesApi(api_client)
    binary_id = 56 # int | 

    try:
        # Gets the die info of a binary
        api_response = api_instance.get_binary_die_info(binary_id)
        print("The response of BinariesApi->get_binary_die_info:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BinariesApi->get_binary_die_info: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **binary_id** | **int**|  | 

### Return type

[**BaseResponseListDieMatch**](BaseResponseListDieMatch.md)

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

# **get_binary_externals**
> BaseResponseBinaryExternalsResponse get_binary_externals(binary_id)

Gets the external details of a binary

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_binary_externals_response import BaseResponseBinaryExternalsResponse
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
    api_instance = revengai.BinariesApi(api_client)
    binary_id = 56 # int | 

    try:
        # Gets the external details of a binary
        api_response = api_instance.get_binary_externals(binary_id)
        print("The response of BinariesApi->get_binary_externals:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BinariesApi->get_binary_externals: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **binary_id** | **int**|  | 

### Return type

[**BaseResponseBinaryExternalsResponse**](BaseResponseBinaryExternalsResponse.md)

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

# **get_related_binaries**
> BaseResponseChildBinariesResponse get_related_binaries(binary_id)

Gets the related binaries of a binary.

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_child_binaries_response import BaseResponseChildBinariesResponse
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
    api_instance = revengai.BinariesApi(api_client)
    binary_id = 56 # int | 

    try:
        # Gets the related binaries of a binary.
        api_response = api_instance.get_related_binaries(binary_id)
        print("The response of BinariesApi->get_related_binaries:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BinariesApi->get_related_binaries: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **binary_id** | **int**|  | 

### Return type

[**BaseResponseChildBinariesResponse**](BaseResponseChildBinariesResponse.md)

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
**403** | Forbidden |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

