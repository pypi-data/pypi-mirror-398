# revengai.FunctionsCoreApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**ai_unstrip**](FunctionsCoreApi.md#ai_unstrip) | **POST** /v2/analyses/{analysis_id}/functions/ai-unstrip | Performs matching and auto-unstrip for an analysis and its functions
[**analysis_function_matching**](FunctionsCoreApi.md#analysis_function_matching) | **POST** /v2/analyses/{analysis_id}/functions/matches | Perform matching for the functions of an analysis
[**auto_unstrip**](FunctionsCoreApi.md#auto_unstrip) | **POST** /v2/analyses/{analysis_id}/functions/auto-unstrip | Performs matching and auto-unstrip for an analysis and its functions
[**batch_function_matching**](FunctionsCoreApi.md#batch_function_matching) | **POST** /v2/functions/matches | Perform function matching for an arbitrary batch of functions, binaries or collections
[**cancel_ai_unstrip**](FunctionsCoreApi.md#cancel_ai_unstrip) | **DELETE** /v2/analyses/{analysis_id}/functions/ai-unstrip/cancel | Cancels a running ai-unstrip
[**cancel_auto_unstrip**](FunctionsCoreApi.md#cancel_auto_unstrip) | **DELETE** /v2/analyses/{analysis_id}/functions/unstrip/cancel | Cancels a running auto-unstrip
[**get_analysis_strings**](FunctionsCoreApi.md#get_analysis_strings) | **GET** /v2/analyses/{analysis_id}/functions/strings | Get string information found in the Analysis
[**get_function_blocks**](FunctionsCoreApi.md#get_function_blocks) | **GET** /v2/functions/{function_id}/blocks | Get disassembly blocks related to the function
[**get_function_callees_callers**](FunctionsCoreApi.md#get_function_callees_callers) | **GET** /v2/functions/{function_id}/callees_callers | Get list of functions that call or are called by the specified function
[**get_function_capabilities**](FunctionsCoreApi.md#get_function_capabilities) | **GET** /v2/functions/{function_id}/capabilities | Retrieve a functions capabilities
[**get_function_details**](FunctionsCoreApi.md#get_function_details) | **GET** /v2/functions/{function_id} | Get function details
[**get_function_strings**](FunctionsCoreApi.md#get_function_strings) | **GET** /v2/functions/{function_id}/strings | Get string information found in the function


# **ai_unstrip**
> AutoUnstripResponse ai_unstrip(analysis_id, ai_unstrip_request)

Performs matching and auto-unstrip for an analysis and its functions

Takes in the analysis ID, uses the functions ID's from it and settings to find the nearest function groups for each function that's within the system

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.ai_unstrip_request import AiUnstripRequest
from revengai.models.auto_unstrip_response import AutoUnstripResponse
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
    api_instance = revengai.FunctionsCoreApi(api_client)
    analysis_id = 56 # int | 
    ai_unstrip_request = revengai.AiUnstripRequest() # AiUnstripRequest | 

    try:
        # Performs matching and auto-unstrip for an analysis and its functions
        api_response = api_instance.ai_unstrip(analysis_id, ai_unstrip_request)
        print("The response of FunctionsCoreApi->ai_unstrip:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsCoreApi->ai_unstrip: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 
 **ai_unstrip_request** | [**AiUnstripRequest**](AiUnstripRequest.md)|  | 

### Return type

[**AutoUnstripResponse**](AutoUnstripResponse.md)

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

# **analysis_function_matching**
> FunctionMatchingResponse analysis_function_matching(analysis_id, analysis_function_matching_request)

Perform matching for the functions of an analysis

Takes in an analysis id and settings and matches the nearest functions to the ones associated with it. Results can optionally be filtered by collection, binary, debug type or (other) function ids

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.analysis_function_matching_request import AnalysisFunctionMatchingRequest
from revengai.models.function_matching_response import FunctionMatchingResponse
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
    api_instance = revengai.FunctionsCoreApi(api_client)
    analysis_id = 56 # int | 
    analysis_function_matching_request = revengai.AnalysisFunctionMatchingRequest() # AnalysisFunctionMatchingRequest | 

    try:
        # Perform matching for the functions of an analysis
        api_response = api_instance.analysis_function_matching(analysis_id, analysis_function_matching_request)
        print("The response of FunctionsCoreApi->analysis_function_matching:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsCoreApi->analysis_function_matching: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 
 **analysis_function_matching_request** | [**AnalysisFunctionMatchingRequest**](AnalysisFunctionMatchingRequest.md)|  | 

### Return type

[**FunctionMatchingResponse**](FunctionMatchingResponse.md)

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

# **auto_unstrip**
> AutoUnstripResponse auto_unstrip(analysis_id, auto_unstrip_request)

Performs matching and auto-unstrip for an analysis and its functions

Takes in the analysis ID, uses the functions ID's from it and settings to find the nearest function for each function that's within the system

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.auto_unstrip_request import AutoUnstripRequest
from revengai.models.auto_unstrip_response import AutoUnstripResponse
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
    api_instance = revengai.FunctionsCoreApi(api_client)
    analysis_id = 56 # int | 
    auto_unstrip_request = revengai.AutoUnstripRequest() # AutoUnstripRequest | 

    try:
        # Performs matching and auto-unstrip for an analysis and its functions
        api_response = api_instance.auto_unstrip(analysis_id, auto_unstrip_request)
        print("The response of FunctionsCoreApi->auto_unstrip:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsCoreApi->auto_unstrip: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 
 **auto_unstrip_request** | [**AutoUnstripRequest**](AutoUnstripRequest.md)|  | 

### Return type

[**AutoUnstripResponse**](AutoUnstripResponse.md)

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

# **batch_function_matching**
> FunctionMatchingResponse batch_function_matching(function_matching_request)

Perform function matching for an arbitrary batch of functions, binaries or collections

Takes in an input of functions ID's and settings and finds the nearest functions for each function that's within the system

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.function_matching_request import FunctionMatchingRequest
from revengai.models.function_matching_response import FunctionMatchingResponse
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
    api_instance = revengai.FunctionsCoreApi(api_client)
    function_matching_request = revengai.FunctionMatchingRequest() # FunctionMatchingRequest | 

    try:
        # Perform function matching for an arbitrary batch of functions, binaries or collections
        api_response = api_instance.batch_function_matching(function_matching_request)
        print("The response of FunctionsCoreApi->batch_function_matching:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsCoreApi->batch_function_matching: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_matching_request** | [**FunctionMatchingRequest**](FunctionMatchingRequest.md)|  | 

### Return type

[**FunctionMatchingResponse**](FunctionMatchingResponse.md)

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

# **cancel_ai_unstrip**
> AutoUnstripResponse cancel_ai_unstrip(analysis_id)

Cancels a running ai-unstrip

Takes in the analysis ID and cancels a running ai-unstrip operation

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.auto_unstrip_response import AutoUnstripResponse
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
    api_instance = revengai.FunctionsCoreApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Cancels a running ai-unstrip
        api_response = api_instance.cancel_ai_unstrip(analysis_id)
        print("The response of FunctionsCoreApi->cancel_ai_unstrip:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsCoreApi->cancel_ai_unstrip: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

### Return type

[**AutoUnstripResponse**](AutoUnstripResponse.md)

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

# **cancel_auto_unstrip**
> AutoUnstripResponse cancel_auto_unstrip(analysis_id)

Cancels a running auto-unstrip

Takes in the analysis ID and cancels a running auto-unstrip operation

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.auto_unstrip_response import AutoUnstripResponse
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
    api_instance = revengai.FunctionsCoreApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Cancels a running auto-unstrip
        api_response = api_instance.cancel_auto_unstrip(analysis_id)
        print("The response of FunctionsCoreApi->cancel_auto_unstrip:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsCoreApi->cancel_auto_unstrip: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

### Return type

[**AutoUnstripResponse**](AutoUnstripResponse.md)

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

# **get_analysis_strings**
> BaseResponseAnalysisStringsResponse get_analysis_strings(analysis_id, page=page, page_size=page_size, search=search, function_search=function_search)

Get string information found in the Analysis

Get string information found in the analysis

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_analysis_strings_response import BaseResponseAnalysisStringsResponse
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
    api_instance = revengai.FunctionsCoreApi(api_client)
    analysis_id = 56 # int | 
    page = 1 # int | The page number to retrieve. (optional) (default to 1)
    page_size = 100 # int | Number of items per page. (optional) (default to 100)
    search = 'search_example' # str | Search is applied to string value (optional)
    function_search = 'function_search_example' # str | Search is applied to function names (optional)

    try:
        # Get string information found in the Analysis
        api_response = api_instance.get_analysis_strings(analysis_id, page=page, page_size=page_size, search=search, function_search=function_search)
        print("The response of FunctionsCoreApi->get_analysis_strings:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsCoreApi->get_analysis_strings: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 
 **page** | **int**| The page number to retrieve. | [optional] [default to 1]
 **page_size** | **int**| Number of items per page. | [optional] [default to 100]
 **search** | **str**| Search is applied to string value | [optional] 
 **function_search** | **str**| Search is applied to function names | [optional] 

### Return type

[**BaseResponseAnalysisStringsResponse**](BaseResponseAnalysisStringsResponse.md)

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

# **get_function_blocks**
> BaseResponseFunctionBlocksResponse get_function_blocks(function_id)

Get disassembly blocks related to the function

Get disassembly blocks related to the function

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_function_blocks_response import BaseResponseFunctionBlocksResponse
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
    api_instance = revengai.FunctionsCoreApi(api_client)
    function_id = 56 # int | 

    try:
        # Get disassembly blocks related to the function
        api_response = api_instance.get_function_blocks(function_id)
        print("The response of FunctionsCoreApi->get_function_blocks:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsCoreApi->get_function_blocks: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**|  | 

### Return type

[**BaseResponseFunctionBlocksResponse**](BaseResponseFunctionBlocksResponse.md)

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
**404** | Not Found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_function_callees_callers**
> BaseResponseCalleesCallerFunctionsResponse get_function_callees_callers(function_id)

Get list of functions that call or are called by the specified function

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_callees_caller_functions_response import BaseResponseCalleesCallerFunctionsResponse
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
    api_instance = revengai.FunctionsCoreApi(api_client)
    function_id = 56 # int | 

    try:
        # Get list of functions that call or are called by the specified function
        api_response = api_instance.get_function_callees_callers(function_id)
        print("The response of FunctionsCoreApi->get_function_callees_callers:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsCoreApi->get_function_callees_callers: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**|  | 

### Return type

[**BaseResponseCalleesCallerFunctionsResponse**](BaseResponseCalleesCallerFunctionsResponse.md)

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

# **get_function_capabilities**
> BaseResponseFunctionCapabilityResponse get_function_capabilities(function_id)

Retrieve a functions capabilities

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_function_capability_response import BaseResponseFunctionCapabilityResponse
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
    api_instance = revengai.FunctionsCoreApi(api_client)
    function_id = 56 # int | 

    try:
        # Retrieve a functions capabilities
        api_response = api_instance.get_function_capabilities(function_id)
        print("The response of FunctionsCoreApi->get_function_capabilities:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsCoreApi->get_function_capabilities: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**|  | 

### Return type

[**BaseResponseFunctionCapabilityResponse**](BaseResponseFunctionCapabilityResponse.md)

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
**404** | Not Found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_function_details**
> BaseResponseFunctionsDetailResponse get_function_details(function_id)

Get function details

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_functions_detail_response import BaseResponseFunctionsDetailResponse
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
    api_instance = revengai.FunctionsCoreApi(api_client)
    function_id = 56 # int | 

    try:
        # Get function details
        api_response = api_instance.get_function_details(function_id)
        print("The response of FunctionsCoreApi->get_function_details:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsCoreApi->get_function_details: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**|  | 

### Return type

[**BaseResponseFunctionsDetailResponse**](BaseResponseFunctionsDetailResponse.md)

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

# **get_function_strings**
> BaseResponseFunctionStringsResponse get_function_strings(function_id, page=page, page_size=page_size, search=search)

Get string information found in the function

Get string information found in the function

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_function_strings_response import BaseResponseFunctionStringsResponse
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
    api_instance = revengai.FunctionsCoreApi(api_client)
    function_id = 56 # int | 
    page = 1 # int | The page number to retrieve. (optional) (default to 1)
    page_size = 100 # int | Number of items per page. (optional) (default to 100)
    search = 'search_example' # str | Search is applied to string value (optional)

    try:
        # Get string information found in the function
        api_response = api_instance.get_function_strings(function_id, page=page, page_size=page_size, search=search)
        print("The response of FunctionsCoreApi->get_function_strings:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsCoreApi->get_function_strings: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**|  | 
 **page** | **int**| The page number to retrieve. | [optional] [default to 1]
 **page_size** | **int**| Number of items per page. | [optional] [default to 100]
 **search** | **str**| Search is applied to string value | [optional] 

### Return type

[**BaseResponseFunctionStringsResponse**](BaseResponseFunctionStringsResponse.md)

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

