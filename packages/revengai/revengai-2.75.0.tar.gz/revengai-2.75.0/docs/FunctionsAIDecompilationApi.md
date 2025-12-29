# revengai.FunctionsAIDecompilationApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_ai_decompilation_comment**](FunctionsAIDecompilationApi.md#create_ai_decompilation_comment) | **POST** /v2/functions/{function_id}/ai-decompilation/comments | Create a comment for this function
[**create_ai_decompilation_task**](FunctionsAIDecompilationApi.md#create_ai_decompilation_task) | **POST** /v2/functions/{function_id}/ai-decompilation | Begins AI Decompilation Process
[**delete_ai_decompilation_comment**](FunctionsAIDecompilationApi.md#delete_ai_decompilation_comment) | **DELETE** /v2/functions/{function_id}/ai-decompilation/comments/{comment_id} | Delete a comment
[**get_ai_decompilation_comments**](FunctionsAIDecompilationApi.md#get_ai_decompilation_comments) | **GET** /v2/functions/{function_id}/ai-decompilation/comments | Get comments for this function
[**get_ai_decompilation_rating**](FunctionsAIDecompilationApi.md#get_ai_decompilation_rating) | **GET** /v2/functions/{function_id}/ai-decompilation/rating | Get rating for AI decompilation
[**get_ai_decompilation_task_result**](FunctionsAIDecompilationApi.md#get_ai_decompilation_task_result) | **GET** /v2/functions/{function_id}/ai-decompilation | Polls AI Decompilation Process
[**get_ai_decompilation_task_status**](FunctionsAIDecompilationApi.md#get_ai_decompilation_task_status) | **GET** /v2/functions/{function_id}/ai-decompilation/status | Check the status of a function ai decompilation
[**update_ai_decompilation_comment**](FunctionsAIDecompilationApi.md#update_ai_decompilation_comment) | **PATCH** /v2/functions/{function_id}/ai-decompilation/comments/{comment_id} | Update a comment
[**upsert_ai_decompilation_rating**](FunctionsAIDecompilationApi.md#upsert_ai_decompilation_rating) | **PATCH** /v2/functions/{function_id}/ai-decompilation/rating | Upsert rating for AI decompilation


# **create_ai_decompilation_comment**
> BaseResponseCommentResponse create_ai_decompilation_comment(function_id, function_comment_create_request)

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
    api_instance = revengai.FunctionsAIDecompilationApi(api_client)
    function_id = 56 # int | 
    function_comment_create_request = revengai.FunctionCommentCreateRequest() # FunctionCommentCreateRequest | 

    try:
        # Create a comment for this function
        api_response = api_instance.create_ai_decompilation_comment(function_id, function_comment_create_request)
        print("The response of FunctionsAIDecompilationApi->create_ai_decompilation_comment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsAIDecompilationApi->create_ai_decompilation_comment: %s\n" % e)
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

# **create_ai_decompilation_task**
> BaseResponse create_ai_decompilation_task(function_id)

Begins AI Decompilation Process

Begins the AI Decompilation Process

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
    api_instance = revengai.FunctionsAIDecompilationApi(api_client)
    function_id = 56 # int | The ID of the function for which we are creating the decompilation task

    try:
        # Begins AI Decompilation Process
        api_response = api_instance.create_ai_decompilation_task(function_id)
        print("The response of FunctionsAIDecompilationApi->create_ai_decompilation_task:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsAIDecompilationApi->create_ai_decompilation_task: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**| The ID of the function for which we are creating the decompilation task | 

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
**201** | Successful Response |  -  |
**422** | Invalid request parameters |  -  |
**403** | Forbidden |  -  |
**402** | Payment Required |  -  |
**409** | Conflict |  -  |
**400** | Bad Request |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_ai_decompilation_comment**
> BaseResponseBool delete_ai_decompilation_comment(comment_id, function_id)

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
    api_instance = revengai.FunctionsAIDecompilationApi(api_client)
    comment_id = 56 # int | 
    function_id = 56 # int | 

    try:
        # Delete a comment
        api_response = api_instance.delete_ai_decompilation_comment(comment_id, function_id)
        print("The response of FunctionsAIDecompilationApi->delete_ai_decompilation_comment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsAIDecompilationApi->delete_ai_decompilation_comment: %s\n" % e)
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

# **get_ai_decompilation_comments**
> BaseResponseListCommentResponse get_ai_decompilation_comments(function_id)

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
    api_instance = revengai.FunctionsAIDecompilationApi(api_client)
    function_id = 56 # int | 

    try:
        # Get comments for this function
        api_response = api_instance.get_ai_decompilation_comments(function_id)
        print("The response of FunctionsAIDecompilationApi->get_ai_decompilation_comments:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsAIDecompilationApi->get_ai_decompilation_comments: %s\n" % e)
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

# **get_ai_decompilation_rating**
> BaseResponseGetAiDecompilationRatingResponse get_ai_decompilation_rating(function_id)

Get rating for AI decompilation

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_get_ai_decompilation_rating_response import BaseResponseGetAiDecompilationRatingResponse
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
    api_instance = revengai.FunctionsAIDecompilationApi(api_client)
    function_id = 56 # int | The ID of the function for which to get the rating

    try:
        # Get rating for AI decompilation
        api_response = api_instance.get_ai_decompilation_rating(function_id)
        print("The response of FunctionsAIDecompilationApi->get_ai_decompilation_rating:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsAIDecompilationApi->get_ai_decompilation_rating: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**| The ID of the function for which to get the rating | 

### Return type

[**BaseResponseGetAiDecompilationRatingResponse**](BaseResponseGetAiDecompilationRatingResponse.md)

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

# **get_ai_decompilation_task_result**
> BaseResponseGetAiDecompilationTask get_ai_decompilation_task_result(function_id, summarise=summarise, generate_inline_comments=generate_inline_comments)

Polls AI Decompilation Process

Polls the AI Decompilation Process

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_get_ai_decompilation_task import BaseResponseGetAiDecompilationTask
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
    api_instance = revengai.FunctionsAIDecompilationApi(api_client)
    function_id = 56 # int | The ID of the function being decompiled
    summarise = True # bool | Generate a summary for the decompilation (optional) (default to True)
    generate_inline_comments = True # bool | Generate inline comments for the decompilation (only works if summarise is enabled) (optional) (default to True)

    try:
        # Polls AI Decompilation Process
        api_response = api_instance.get_ai_decompilation_task_result(function_id, summarise=summarise, generate_inline_comments=generate_inline_comments)
        print("The response of FunctionsAIDecompilationApi->get_ai_decompilation_task_result:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsAIDecompilationApi->get_ai_decompilation_task_result: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**| The ID of the function being decompiled | 
 **summarise** | **bool**| Generate a summary for the decompilation | [optional] [default to True]
 **generate_inline_comments** | **bool**| Generate inline comments for the decompilation (only works if summarise is enabled) | [optional] [default to True]

### Return type

[**BaseResponseGetAiDecompilationTask**](BaseResponseGetAiDecompilationTask.md)

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

# **get_ai_decompilation_task_status**
> BaseResponseFunctionTaskResponse get_ai_decompilation_task_status(function_id)

Check the status of a function ai decompilation

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_function_task_response import BaseResponseFunctionTaskResponse
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
    api_instance = revengai.FunctionsAIDecompilationApi(api_client)
    function_id = 56 # int | The ID of the function being checked

    try:
        # Check the status of a function ai decompilation
        api_response = api_instance.get_ai_decompilation_task_status(function_id)
        print("The response of FunctionsAIDecompilationApi->get_ai_decompilation_task_status:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsAIDecompilationApi->get_ai_decompilation_task_status: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**| The ID of the function being checked | 

### Return type

[**BaseResponseFunctionTaskResponse**](BaseResponseFunctionTaskResponse.md)

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

# **update_ai_decompilation_comment**
> BaseResponseCommentResponse update_ai_decompilation_comment(comment_id, function_id, comment_update_request)

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
    api_instance = revengai.FunctionsAIDecompilationApi(api_client)
    comment_id = 56 # int | 
    function_id = 56 # int | 
    comment_update_request = revengai.CommentUpdateRequest() # CommentUpdateRequest | 

    try:
        # Update a comment
        api_response = api_instance.update_ai_decompilation_comment(comment_id, function_id, comment_update_request)
        print("The response of FunctionsAIDecompilationApi->update_ai_decompilation_comment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsAIDecompilationApi->update_ai_decompilation_comment: %s\n" % e)
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

# **upsert_ai_decompilation_rating**
> BaseResponse upsert_ai_decompilation_rating(function_id, upsert_ai_decomplation_rating_request)

Upsert rating for AI decompilation

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response import BaseResponse
from revengai.models.upsert_ai_decomplation_rating_request import UpsertAiDecomplationRatingRequest
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
    api_instance = revengai.FunctionsAIDecompilationApi(api_client)
    function_id = 56 # int | The ID of the function being rated
    upsert_ai_decomplation_rating_request = revengai.UpsertAiDecomplationRatingRequest() # UpsertAiDecomplationRatingRequest | 

    try:
        # Upsert rating for AI decompilation
        api_response = api_instance.upsert_ai_decompilation_rating(function_id, upsert_ai_decomplation_rating_request)
        print("The response of FunctionsAIDecompilationApi->upsert_ai_decompilation_rating:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsAIDecompilationApi->upsert_ai_decompilation_rating: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_id** | **int**| The ID of the function being rated | 
 **upsert_ai_decomplation_rating_request** | [**UpsertAiDecomplationRatingRequest**](UpsertAiDecomplationRatingRequest.md)|  | 

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
**201** | Successful Response |  -  |
**422** | Invalid request parameters |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

