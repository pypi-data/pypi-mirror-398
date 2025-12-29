# revengai.AnalysesSecurityChecksApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_scurity_checks_task**](AnalysesSecurityChecksApi.md#create_scurity_checks_task) | **POST** /v2/analyses/{analysis_id}/security-checks | Queues a security check process
[**get_security_checks**](AnalysesSecurityChecksApi.md#get_security_checks) | **GET** /v2/analyses/{analysis_id}/security-checks | Get Security Checks
[**get_security_checks_task_status**](AnalysesSecurityChecksApi.md#get_security_checks_task_status) | **GET** /v2/analyses/{analysis_id}/security-checks/status | Check the status of a security check process


# **create_scurity_checks_task**
> QueuedSecurityChecksTaskResponse create_scurity_checks_task(analysis_id)

Queues a security check process

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.queued_security_checks_task_response import QueuedSecurityChecksTaskResponse
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
    api_instance = revengai.AnalysesSecurityChecksApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Queues a security check process
        api_response = api_instance.create_scurity_checks_task(analysis_id)
        print("The response of AnalysesSecurityChecksApi->create_scurity_checks_task:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesSecurityChecksApi->create_scurity_checks_task: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

### Return type

[**QueuedSecurityChecksTaskResponse**](QueuedSecurityChecksTaskResponse.md)

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
**409** | Security checks already extracted or queued |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_security_checks**
> BaseResponseSecurityChecksResponse get_security_checks(analysis_id, page, page_size)

Get Security Checks

Retrieve security checks results with pagination.

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_security_checks_response import BaseResponseSecurityChecksResponse
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
    api_instance = revengai.AnalysesSecurityChecksApi(api_client)
    analysis_id = 56 # int | 
    page = 56 # int | The page number to retrieve.
    page_size = 56 # int | Number of items per page.

    try:
        # Get Security Checks
        api_response = api_instance.get_security_checks(analysis_id, page, page_size)
        print("The response of AnalysesSecurityChecksApi->get_security_checks:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesSecurityChecksApi->get_security_checks: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 
 **page** | **int**| The page number to retrieve. | 
 **page_size** | **int**| Number of items per page. | 

### Return type

[**BaseResponseSecurityChecksResponse**](BaseResponseSecurityChecksResponse.md)

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

# **get_security_checks_task_status**
> CheckSecurityChecksTaskResponse get_security_checks_task_status(analysis_id)

Check the status of a security check process

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.check_security_checks_task_response import CheckSecurityChecksTaskResponse
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
    api_instance = revengai.AnalysesSecurityChecksApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Check the status of a security check process
        api_response = api_instance.get_security_checks_task_status(analysis_id)
        print("The response of AnalysesSecurityChecksApi->get_security_checks_task_status:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesSecurityChecksApi->get_security_checks_task_status: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

### Return type

[**CheckSecurityChecksTaskResponse**](CheckSecurityChecksTaskResponse.md)

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

