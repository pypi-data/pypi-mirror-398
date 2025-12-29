# revengai.AuthenticationUsersApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_requester_user_info**](AuthenticationUsersApi.md#get_requester_user_info) | **GET** /v2/users/me | Get the requesters user information
[**get_user**](AuthenticationUsersApi.md#get_user) | **GET** /v2/users/{user_id} | Get a user&#39;s public information
[**get_user_activity**](AuthenticationUsersApi.md#get_user_activity) | **GET** /v2/users/activity | Get auth user activity
[**get_user_comments**](AuthenticationUsersApi.md#get_user_comments) | **GET** /v2/users/me/comments | Get comments by user
[**login_user**](AuthenticationUsersApi.md#login_user) | **POST** /v2/auth/login | Authenticate a user


# **get_requester_user_info**
> BaseResponseGetMeResponse get_requester_user_info()

Get the requesters user information

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_get_me_response import BaseResponseGetMeResponse
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
    api_instance = revengai.AuthenticationUsersApi(api_client)

    try:
        # Get the requesters user information
        api_response = api_instance.get_requester_user_info()
        print("The response of AuthenticationUsersApi->get_requester_user_info:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AuthenticationUsersApi->get_requester_user_info: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**BaseResponseGetMeResponse**](BaseResponseGetMeResponse.md)

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

# **get_user**
> BaseResponseGetPublicUserResponse get_user(user_id)

Get a user's public information

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_get_public_user_response import BaseResponseGetPublicUserResponse
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
    api_instance = revengai.AuthenticationUsersApi(api_client)
    user_id = 56 # int | 

    try:
        # Get a user's public information
        api_response = api_instance.get_user(user_id)
        print("The response of AuthenticationUsersApi->get_user:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AuthenticationUsersApi->get_user: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **user_id** | **int**|  | 

### Return type

[**BaseResponseGetPublicUserResponse**](BaseResponseGetPublicUserResponse.md)

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

# **get_user_activity**
> BaseResponseListUserActivityResponse get_user_activity()

Get auth user activity

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_list_user_activity_response import BaseResponseListUserActivityResponse
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
    api_instance = revengai.AuthenticationUsersApi(api_client)

    try:
        # Get auth user activity
        api_response = api_instance.get_user_activity()
        print("The response of AuthenticationUsersApi->get_user_activity:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AuthenticationUsersApi->get_user_activity: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**BaseResponseListUserActivityResponse**](BaseResponseListUserActivityResponse.md)

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

# **get_user_comments**
> BaseResponseListCommentResponse get_user_comments()

Get comments by user

Retrieves all comments created by a specific user. Only returns comments for resources the requesting user has access to.

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
    api_instance = revengai.AuthenticationUsersApi(api_client)

    try:
        # Get comments by user
        api_response = api_instance.get_user_comments()
        print("The response of AuthenticationUsersApi->get_user_comments:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AuthenticationUsersApi->get_user_comments: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

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

# **login_user**
> BaseResponseLoginResponse login_user(login_request)

Authenticate a user

Authenticates a user and returns a token.

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_login_response import BaseResponseLoginResponse
from revengai.models.login_request import LoginRequest
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
    api_instance = revengai.AuthenticationUsersApi(api_client)
    login_request = revengai.LoginRequest() # LoginRequest | 

    try:
        # Authenticate a user
        api_response = api_instance.login_user(login_request)
        print("The response of AuthenticationUsersApi->login_user:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AuthenticationUsersApi->login_user: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **login_request** | [**LoginRequest**](LoginRequest.md)|  | 

### Return type

[**BaseResponseLoginResponse**](BaseResponseLoginResponse.md)

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
**401** | Invalid credentials |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

