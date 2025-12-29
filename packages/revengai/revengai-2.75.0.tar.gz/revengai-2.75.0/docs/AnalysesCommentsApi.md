# revengai.AnalysesCommentsApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_analysis_comment**](AnalysesCommentsApi.md#create_analysis_comment) | **POST** /v2/analyses/{analysis_id}/comments | Create a comment for this analysis
[**delete_analysis_comment**](AnalysesCommentsApi.md#delete_analysis_comment) | **DELETE** /v2/analyses/{analysis_id}/comments/{comment_id} | Delete a comment
[**get_analysis_comments**](AnalysesCommentsApi.md#get_analysis_comments) | **GET** /v2/analyses/{analysis_id}/comments | Get comments for this analysis
[**update_analysis_comment**](AnalysesCommentsApi.md#update_analysis_comment) | **PATCH** /v2/analyses/{analysis_id}/comments/{comment_id} | Update a comment


# **create_analysis_comment**
> BaseResponseCommentResponse create_analysis_comment(analysis_id, comment_base)

Create a comment for this analysis

Creates a comment associated with a specified analysis).

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_comment_response import BaseResponseCommentResponse
from revengai.models.comment_base import CommentBase
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
    api_instance = revengai.AnalysesCommentsApi(api_client)
    analysis_id = 56 # int | 
    comment_base = revengai.CommentBase() # CommentBase | 

    try:
        # Create a comment for this analysis
        api_response = api_instance.create_analysis_comment(analysis_id, comment_base)
        print("The response of AnalysesCommentsApi->create_analysis_comment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesCommentsApi->create_analysis_comment: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 
 **comment_base** | [**CommentBase**](CommentBase.md)|  | 

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

# **delete_analysis_comment**
> BaseResponseBool delete_analysis_comment(comment_id, analysis_id)

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
    api_instance = revengai.AnalysesCommentsApi(api_client)
    comment_id = 56 # int | 
    analysis_id = 56 # int | 

    try:
        # Delete a comment
        api_response = api_instance.delete_analysis_comment(comment_id, analysis_id)
        print("The response of AnalysesCommentsApi->delete_analysis_comment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesCommentsApi->delete_analysis_comment: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **comment_id** | **int**|  | 
 **analysis_id** | **int**|  | 

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

# **get_analysis_comments**
> BaseResponseListCommentResponse get_analysis_comments(analysis_id)

Get comments for this analysis

Retrieves all comments created for a specific analysis. Only returns comments for resources the requesting user has access to.

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
    api_instance = revengai.AnalysesCommentsApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Get comments for this analysis
        api_response = api_instance.get_analysis_comments(analysis_id)
        print("The response of AnalysesCommentsApi->get_analysis_comments:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesCommentsApi->get_analysis_comments: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

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

# **update_analysis_comment**
> BaseResponseCommentResponse update_analysis_comment(comment_id, analysis_id, comment_update_request)

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
    api_instance = revengai.AnalysesCommentsApi(api_client)
    comment_id = 56 # int | 
    analysis_id = 56 # int | 
    comment_update_request = revengai.CommentUpdateRequest() # CommentUpdateRequest | 

    try:
        # Update a comment
        api_response = api_instance.update_analysis_comment(comment_id, analysis_id, comment_update_request)
        print("The response of AnalysesCommentsApi->update_analysis_comment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesCommentsApi->update_analysis_comment: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **comment_id** | **int**|  | 
 **analysis_id** | **int**|  | 
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

