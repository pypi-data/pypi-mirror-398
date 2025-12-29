# revengai.FunctionsRenamingHistoryApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**batch_rename_function**](FunctionsRenamingHistoryApi.md#batch_rename_function) | **POST** /v2/functions/rename/batch | Batch Rename Functions
[**get_function_name_history**](FunctionsRenamingHistoryApi.md#get_function_name_history) | **GET** /v2/functions/history/{function_id} | Get Function Name History
[**rename_function_id**](FunctionsRenamingHistoryApi.md#rename_function_id) | **POST** /v2/functions/rename/{function_id} | Rename Function
[**revert_function_name**](FunctionsRenamingHistoryApi.md#revert_function_name) | **POST** /v2/functions/history/{function_id}/{history_id} | Revert the function name


# **batch_rename_function**
> BaseResponse batch_rename_function(functions_list_rename)

Batch Rename Functions

Renames a list of functions using the function IDs 
 Will record name changes in history

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response import BaseResponse
from revengai.models.functions_list_rename import FunctionsListRename
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
    api_instance = revengai.FunctionsRenamingHistoryApi(api_client)
    functions_list_rename = revengai.FunctionsListRename() # FunctionsListRename | 

    try:
        # Batch Rename Functions
        api_response = api_instance.batch_rename_function(functions_list_rename)
        print("The response of FunctionsRenamingHistoryApi->batch_rename_function:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsRenamingHistoryApi->batch_rename_function: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **functions_list_rename** | [**FunctionsListRename**](FunctionsListRename.md)|  | 

### Return type

[**BaseResponse**](BaseResponse.md)

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

# **get_function_name_history**
> BaseResponseListFunctionNameHistory get_function_name_history(function_id)

Get Function Name History

Gets the name history of a function using the function ID

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_list_function_name_history import BaseResponseListFunctionNameHistory
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
    api_instance = revengai.FunctionsRenamingHistoryApi(api_client)
    function_id = 56 # int | 

    try:
        # Get Function Name History
        api_response = api_instance.get_function_name_history(function_id)
        print("The response of FunctionsRenamingHistoryApi->get_function_name_history:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsRenamingHistoryApi->get_function_name_history: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**|  | 

### Return type

[**BaseResponseListFunctionNameHistory**](BaseResponseListFunctionNameHistory.md)

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

# **rename_function_id**
> BaseResponse rename_function_id(function_id, function_rename)

Rename Function

Renames a function using the function ID 
 Will record name change history

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response import BaseResponse
from revengai.models.function_rename import FunctionRename
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
    api_instance = revengai.FunctionsRenamingHistoryApi(api_client)
    function_id = 56 # int | 
    function_rename = revengai.FunctionRename() # FunctionRename | 

    try:
        # Rename Function
        api_response = api_instance.rename_function_id(function_id, function_rename)
        print("The response of FunctionsRenamingHistoryApi->rename_function_id:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsRenamingHistoryApi->rename_function_id: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**|  | 
 **function_rename** | [**FunctionRename**](FunctionRename.md)|  | 

### Return type

[**BaseResponse**](BaseResponse.md)

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

# **revert_function_name**
> BaseResponse revert_function_name(function_id, history_id)

Revert the function name

Reverts the function name to a previous name using the function ID and history ID

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response import BaseResponse
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
    api_instance = revengai.FunctionsRenamingHistoryApi(api_client)
    function_id = 56 # int | 
    history_id = 56 # int | 

    try:
        # Revert the function name
        api_response = api_instance.revert_function_name(function_id, history_id)
        print("The response of FunctionsRenamingHistoryApi->revert_function_name:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsRenamingHistoryApi->revert_function_name: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**|  | 
 **history_id** | **int**|  | 

### Return type

[**BaseResponse**](BaseResponse.md)

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

