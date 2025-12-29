# revengai.FunctionsDecompilationApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_decompilation_comment**](FunctionsDecompilationApi.md#create_decompilation_comment) | **POST** /v2/functions/{function_id}/decompilation/comments | Create a comment for this function
[**delete_decompilation_comment**](FunctionsDecompilationApi.md#delete_decompilation_comment) | **DELETE** /v2/functions/{function_id}/decompilation/comments/{comment_id} | Delete a comment
[**get_decompilation_comments**](FunctionsDecompilationApi.md#get_decompilation_comments) | **GET** /v2/functions/{function_id}/decompilation/comments | Get comments for this function
[**update_decompilation_comment**](FunctionsDecompilationApi.md#update_decompilation_comment) | **PATCH** /v2/functions/{function_id}/decompilation/comments/{comment_id} | Update a comment


# **create_decompilation_comment**
> BaseResponseCommentResponse create_decompilation_comment(function_id, function_comment_create_request)

Create a comment for this function

Creates a comment associated with a specified function).

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_comment_response import BaseResponseCommentResponse
from revengai.models.function_comment_create_request import FunctionCommentCreateRequest
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
    api_instance = revengai.FunctionsDecompilationApi(api_client)
    function_id = 56 # int | 
    function_comment_create_request = revengai.FunctionCommentCreateRequest() # FunctionCommentCreateRequest | 

    try:
        # Create a comment for this function
        api_response = api_instance.create_decompilation_comment(function_id, function_comment_create_request)
        print("The response of FunctionsDecompilationApi->create_decompilation_comment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsDecompilationApi->create_decompilation_comment: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**|  | 
 **function_comment_create_request** | [**FunctionCommentCreateRequest**](FunctionCommentCreateRequest.md)|  | 

### Return type

[**BaseResponseCommentResponse**](BaseResponseCommentResponse.md)

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
**400** | Bad Request |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_decompilation_comment**
> BaseResponseBool delete_decompilation_comment(comment_id, function_id)

Delete a comment

Deletes an existing comment. Users can only delete their own comments.

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_bool import BaseResponseBool
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
    api_instance = revengai.FunctionsDecompilationApi(api_client)
    comment_id = 56 # int | 
    function_id = 56 # int | 

    try:
        # Delete a comment
        api_response = api_instance.delete_decompilation_comment(comment_id, function_id)
        print("The response of FunctionsDecompilationApi->delete_decompilation_comment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsDecompilationApi->delete_decompilation_comment: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **comment_id** | **int**|  | 
 **function_id** | **int**|  | 

### Return type

[**BaseResponseBool**](BaseResponseBool.md)

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
**403** | You can only delete your own comments |  -  |
**400** | Bad Request |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_decompilation_comments**
> BaseResponseListCommentResponse get_decompilation_comments(function_id)

Get comments for this function

Retrieves all comments created for a specific function. Only returns comments for resources the requesting user has access to.

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_list_comment_response import BaseResponseListCommentResponse
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
    api_instance = revengai.FunctionsDecompilationApi(api_client)
    function_id = 56 # int | 

    try:
        # Get comments for this function
        api_response = api_instance.get_decompilation_comments(function_id)
        print("The response of FunctionsDecompilationApi->get_decompilation_comments:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsDecompilationApi->get_decompilation_comments: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**|  | 

### Return type

[**BaseResponseListCommentResponse**](BaseResponseListCommentResponse.md)

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

# **update_decompilation_comment**
> BaseResponseCommentResponse update_decompilation_comment(comment_id, function_id, comment_update_request)

Update a comment

Updates the content of an existing comment. Users can only update their own comments.

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_comment_response import BaseResponseCommentResponse
from revengai.models.comment_update_request import CommentUpdateRequest
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
    api_instance = revengai.FunctionsDecompilationApi(api_client)
    comment_id = 56 # int | 
    function_id = 56 # int | 
    comment_update_request = revengai.CommentUpdateRequest() # CommentUpdateRequest | 

    try:
        # Update a comment
        api_response = api_instance.update_decompilation_comment(comment_id, function_id, comment_update_request)
        print("The response of FunctionsDecompilationApi->update_decompilation_comment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsDecompilationApi->update_decompilation_comment: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **comment_id** | **int**|  | 
 **function_id** | **int**|  | 
 **comment_update_request** | [**CommentUpdateRequest**](CommentUpdateRequest.md)|  | 

### Return type

[**BaseResponseCommentResponse**](BaseResponseCommentResponse.md)

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
**403** | You can only update your own comments |  -  |
**400** | Bad Request |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

