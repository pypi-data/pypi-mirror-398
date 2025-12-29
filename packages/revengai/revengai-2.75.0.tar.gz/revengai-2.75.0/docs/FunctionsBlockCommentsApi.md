# revengai.FunctionsBlockCommentsApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**generate_block_comments_for_block_in_function**](FunctionsBlockCommentsApi.md#generate_block_comments_for_block_in_function) | **POST** /v2/functions/{function_id}/block-comments/single | Generate block comments for a specific block in a function
[**generate_block_comments_for_function**](FunctionsBlockCommentsApi.md#generate_block_comments_for_function) | **POST** /v2/functions/{function_id}/block-comments | Generate block comments for a function
[**generate_overview_comment_for_function**](FunctionsBlockCommentsApi.md#generate_overview_comment_for_function) | **POST** /v2/functions/{function_id}/block-comments/overview | Generate overview comment for a function


# **generate_block_comments_for_block_in_function**
> BaseResponseBlockCommentsGenerationForFunctionResponse generate_block_comments_for_block_in_function(function_id, block)

Generate block comments for a specific block in a function

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_block_comments_generation_for_function_response import BaseResponseBlockCommentsGenerationForFunctionResponse
from revengai.models.block import Block
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
    api_instance = revengai.FunctionsBlockCommentsApi(api_client)
    function_id = 56 # int | 
    block = revengai.Block() # Block | 

    try:
        # Generate block comments for a specific block in a function
        api_response = api_instance.generate_block_comments_for_block_in_function(function_id, block)
        print("The response of FunctionsBlockCommentsApi->generate_block_comments_for_block_in_function:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsBlockCommentsApi->generate_block_comments_for_block_in_function: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**|  | 
 **block** | [**Block**](Block.md)|  | 

### Return type

[**BaseResponseBlockCommentsGenerationForFunctionResponse**](BaseResponseBlockCommentsGenerationForFunctionResponse.md)

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

# **generate_block_comments_for_function**
> BaseResponseBlockCommentsGenerationForFunctionResponse generate_block_comments_for_function(function_id)

Generate block comments for a function

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_block_comments_generation_for_function_response import BaseResponseBlockCommentsGenerationForFunctionResponse
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
    api_instance = revengai.FunctionsBlockCommentsApi(api_client)
    function_id = 56 # int | 

    try:
        # Generate block comments for a function
        api_response = api_instance.generate_block_comments_for_function(function_id)
        print("The response of FunctionsBlockCommentsApi->generate_block_comments_for_function:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsBlockCommentsApi->generate_block_comments_for_function: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**|  | 

### Return type

[**BaseResponseBlockCommentsGenerationForFunctionResponse**](BaseResponseBlockCommentsGenerationForFunctionResponse.md)

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

# **generate_overview_comment_for_function**
> BaseResponseBlockCommentsOverviewGenerationResponse generate_overview_comment_for_function(function_id)

Generate overview comment for a function

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_block_comments_overview_generation_response import BaseResponseBlockCommentsOverviewGenerationResponse
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
    api_instance = revengai.FunctionsBlockCommentsApi(api_client)
    function_id = 56 # int | 

    try:
        # Generate overview comment for a function
        api_response = api_instance.generate_overview_comment_for_function(function_id)
        print("The response of FunctionsBlockCommentsApi->generate_overview_comment_for_function:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsBlockCommentsApi->generate_overview_comment_for_function: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**|  | 

### Return type

[**BaseResponseBlockCommentsOverviewGenerationResponse**](BaseResponseBlockCommentsOverviewGenerationResponse.md)

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

