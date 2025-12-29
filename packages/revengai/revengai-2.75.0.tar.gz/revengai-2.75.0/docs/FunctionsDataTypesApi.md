# revengai.FunctionsDataTypesApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**generate_function_data_types_for_analysis**](FunctionsDataTypesApi.md#generate_function_data_types_for_analysis) | **POST** /v2/analyses/{analysis_id}/functions/data_types | Generate Function Data Types
[**generate_function_data_types_for_functions**](FunctionsDataTypesApi.md#generate_function_data_types_for_functions) | **POST** /v2/functions/data_types | Generate Function Data Types for an arbitrary list of functions
[**get_function_data_types**](FunctionsDataTypesApi.md#get_function_data_types) | **GET** /v2/analyses/{analysis_id}/functions/{function_id}/data_types | Get Function Data Types
[**list_function_data_types_for_analysis**](FunctionsDataTypesApi.md#list_function_data_types_for_analysis) | **GET** /v2/analyses/{analysis_id}/functions/data_types | List Function Data Types
[**list_function_data_types_for_functions**](FunctionsDataTypesApi.md#list_function_data_types_for_functions) | **GET** /v2/functions/data_types | List Function Data Types
[**update_function_data_types**](FunctionsDataTypesApi.md#update_function_data_types) | **PUT** /v2/analyses/{analysis_id}/functions/{function_id}/data_types | Update Function Data Types


# **generate_function_data_types_for_analysis**
> BaseResponseGenerateFunctionDataTypes generate_function_data_types_for_analysis(analysis_id, function_data_types_params)

Generate Function Data Types

Submits a request to generate the function data types

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_generate_function_data_types import BaseResponseGenerateFunctionDataTypes
from revengai.models.function_data_types_params import FunctionDataTypesParams
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
    api_instance = revengai.FunctionsDataTypesApi(api_client)
    analysis_id = 56 # int | 
    function_data_types_params = revengai.FunctionDataTypesParams() # FunctionDataTypesParams | 

    try:
        # Generate Function Data Types
        api_response = api_instance.generate_function_data_types_for_analysis(analysis_id, function_data_types_params)
        print("The response of FunctionsDataTypesApi->generate_function_data_types_for_analysis:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsDataTypesApi->generate_function_data_types_for_analysis: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 
 **function_data_types_params** | [**FunctionDataTypesParams**](FunctionDataTypesParams.md)|  | 

### Return type

[**BaseResponseGenerateFunctionDataTypes**](BaseResponseGenerateFunctionDataTypes.md)

### Authorization

[APIKey](../README.md#APIKey)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Successful Response |  -  |
**422** | Invalid request parameters |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **generate_function_data_types_for_functions**
> BaseResponseGenerationStatusList generate_function_data_types_for_functions(function_data_types_params)

Generate Function Data Types for an arbitrary list of functions

Submits a request to generate the function data types

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_generation_status_list import BaseResponseGenerationStatusList
from revengai.models.function_data_types_params import FunctionDataTypesParams
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
    api_instance = revengai.FunctionsDataTypesApi(api_client)
    function_data_types_params = revengai.FunctionDataTypesParams() # FunctionDataTypesParams | 

    try:
        # Generate Function Data Types for an arbitrary list of functions
        api_response = api_instance.generate_function_data_types_for_functions(function_data_types_params)
        print("The response of FunctionsDataTypesApi->generate_function_data_types_for_functions:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsDataTypesApi->generate_function_data_types_for_functions: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_data_types_params** | [**FunctionDataTypesParams**](FunctionDataTypesParams.md)|  | 

### Return type

[**BaseResponseGenerationStatusList**](BaseResponseGenerationStatusList.md)

### Authorization

[APIKey](../README.md#APIKey)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Successful Response |  -  |
**422** | Invalid request parameters |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_function_data_types**
> BaseResponseFunctionDataTypes get_function_data_types(analysis_id, function_id)

Get Function Data Types

Polling endpoint which returns the current status of function generation and once completed the data type information

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_function_data_types import BaseResponseFunctionDataTypes
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
    api_instance = revengai.FunctionsDataTypesApi(api_client)
    analysis_id = 56 # int | 
    function_id = 56 # int | 

    try:
        # Get Function Data Types
        api_response = api_instance.get_function_data_types(analysis_id, function_id)
        print("The response of FunctionsDataTypesApi->get_function_data_types:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsDataTypesApi->get_function_data_types: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 
 **function_id** | **int**|  | 

### Return type

[**BaseResponseFunctionDataTypes**](BaseResponseFunctionDataTypes.md)

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

# **list_function_data_types_for_analysis**
> BaseResponseFunctionDataTypesList list_function_data_types_for_analysis(analysis_id, function_ids=function_ids)

List Function Data Types

Returns data types for multiple functions with optional function ID filtering

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_function_data_types_list import BaseResponseFunctionDataTypesList
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
    api_instance = revengai.FunctionsDataTypesApi(api_client)
    analysis_id = 56 # int | 
    function_ids = [56] # List[Optional[int]] |  (optional)

    try:
        # List Function Data Types
        api_response = api_instance.list_function_data_types_for_analysis(analysis_id, function_ids=function_ids)
        print("The response of FunctionsDataTypesApi->list_function_data_types_for_analysis:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsDataTypesApi->list_function_data_types_for_analysis: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 
 **function_ids** | [**List[Optional[int]]**](int.md)|  | [optional] 

### Return type

[**BaseResponseFunctionDataTypesList**](BaseResponseFunctionDataTypesList.md)

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

# **list_function_data_types_for_functions**
> BaseResponseFunctionDataTypesList list_function_data_types_for_functions(function_ids=function_ids)

List Function Data Types

Returns data types for multiple function IDs

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_function_data_types_list import BaseResponseFunctionDataTypesList
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
    api_instance = revengai.FunctionsDataTypesApi(api_client)
    function_ids = [56] # List[Optional[int]] |  (optional)

    try:
        # List Function Data Types
        api_response = api_instance.list_function_data_types_for_functions(function_ids=function_ids)
        print("The response of FunctionsDataTypesApi->list_function_data_types_for_functions:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsDataTypesApi->list_function_data_types_for_functions: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_ids** | [**List[Optional[int]]**](int.md)|  | [optional] 

### Return type

[**BaseResponseFunctionDataTypesList**](BaseResponseFunctionDataTypesList.md)

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

# **update_function_data_types**
> BaseResponseFunctionDataTypes update_function_data_types(analysis_id, function_id, update_function_data_types)

Update Function Data Types

Updates the function data types for a given function

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_function_data_types import BaseResponseFunctionDataTypes
from revengai.models.update_function_data_types import UpdateFunctionDataTypes
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
    api_instance = revengai.FunctionsDataTypesApi(api_client)
    analysis_id = 56 # int | 
    function_id = 56 # int | 
    update_function_data_types = revengai.UpdateFunctionDataTypes() # UpdateFunctionDataTypes | 

    try:
        # Update Function Data Types
        api_response = api_instance.update_function_data_types(analysis_id, function_id, update_function_data_types)
        print("The response of FunctionsDataTypesApi->update_function_data_types:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsDataTypesApi->update_function_data_types: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 
 **function_id** | **int**|  | 
 **update_function_data_types** | [**UpdateFunctionDataTypes**](UpdateFunctionDataTypes.md)|  | 

### Return type

[**BaseResponseFunctionDataTypes**](BaseResponseFunctionDataTypes.md)

### Authorization

[APIKey](../README.md#APIKey)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Invalid request parameters |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

