# revengai.AnalysesDynamicExecutionApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_dynamic_execution_status**](AnalysesDynamicExecutionApi.md#get_dynamic_execution_status) | **GET** /v2/analyses/{analysis_id}/dynamic-execution/status | Get the status of a dynamic execution task
[**get_network_overview**](AnalysesDynamicExecutionApi.md#get_network_overview) | **GET** /v2/analyses/{analysis_id}/dynamic-execution/network-overview | Get the dynamic execution results for network overview
[**get_process_dump**](AnalysesDynamicExecutionApi.md#get_process_dump) | **GET** /v2/analyses/{analysis_id}/dynamic-execution/process-dumps/{dump_name} | Get the dynamic execution results for a specific process dump
[**get_process_dumps**](AnalysesDynamicExecutionApi.md#get_process_dumps) | **GET** /v2/analyses/{analysis_id}/dynamic-execution/process-dumps | Get the dynamic execution results for process dumps
[**get_process_registry**](AnalysesDynamicExecutionApi.md#get_process_registry) | **GET** /v2/analyses/{analysis_id}/dynamic-execution/process-registry | Get the dynamic execution results for process registry
[**get_process_tree**](AnalysesDynamicExecutionApi.md#get_process_tree) | **GET** /v2/analyses/{analysis_id}/dynamic-execution/process-tree | Get the dynamic execution results for process tree
[**get_ttps**](AnalysesDynamicExecutionApi.md#get_ttps) | **GET** /v2/analyses/{analysis_id}/dynamic-execution/ttps | Get the dynamic execution results for ttps


# **get_dynamic_execution_status**
> BaseResponseDynamicExecutionStatus get_dynamic_execution_status(analysis_id)

Get the status of a dynamic execution task

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_dynamic_execution_status import BaseResponseDynamicExecutionStatus
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
    api_instance = revengai.AnalysesDynamicExecutionApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Get the status of a dynamic execution task
        api_response = api_instance.get_dynamic_execution_status(analysis_id)
        print("The response of AnalysesDynamicExecutionApi->get_dynamic_execution_status:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesDynamicExecutionApi->get_dynamic_execution_status: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

### Return type

[**BaseResponseDynamicExecutionStatus**](BaseResponseDynamicExecutionStatus.md)

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

# **get_network_overview**
> BaseResponseNetworkOverviewResponse get_network_overview(analysis_id)

Get the dynamic execution results for network overview

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_network_overview_response import BaseResponseNetworkOverviewResponse
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
    api_instance = revengai.AnalysesDynamicExecutionApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Get the dynamic execution results for network overview
        api_response = api_instance.get_network_overview(analysis_id)
        print("The response of AnalysesDynamicExecutionApi->get_network_overview:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesDynamicExecutionApi->get_network_overview: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

### Return type

[**BaseResponseNetworkOverviewResponse**](BaseResponseNetworkOverviewResponse.md)

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

# **get_process_dump**
> object get_process_dump(analysis_id, dump_name)

Get the dynamic execution results for a specific process dump

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
    api_instance = revengai.AnalysesDynamicExecutionApi(api_client)
    analysis_id = 56 # int | 
    dump_name = 'dump_name_example' # str | 

    try:
        # Get the dynamic execution results for a specific process dump
        api_response = api_instance.get_process_dump(analysis_id, dump_name)
        print("The response of AnalysesDynamicExecutionApi->get_process_dump:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesDynamicExecutionApi->get_process_dump: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 
 **dump_name** | **str**|  | 

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

# **get_process_dumps**
> BaseResponseProcessDumps get_process_dumps(analysis_id)

Get the dynamic execution results for process dumps

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_process_dumps import BaseResponseProcessDumps
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
    api_instance = revengai.AnalysesDynamicExecutionApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Get the dynamic execution results for process dumps
        api_response = api_instance.get_process_dumps(analysis_id)
        print("The response of AnalysesDynamicExecutionApi->get_process_dumps:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesDynamicExecutionApi->get_process_dumps: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

### Return type

[**BaseResponseProcessDumps**](BaseResponseProcessDumps.md)

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

# **get_process_registry**
> BaseResponseProcessRegistry get_process_registry(analysis_id)

Get the dynamic execution results for process registry

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_process_registry import BaseResponseProcessRegistry
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
    api_instance = revengai.AnalysesDynamicExecutionApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Get the dynamic execution results for process registry
        api_response = api_instance.get_process_registry(analysis_id)
        print("The response of AnalysesDynamicExecutionApi->get_process_registry:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesDynamicExecutionApi->get_process_registry: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

### Return type

[**BaseResponseProcessRegistry**](BaseResponseProcessRegistry.md)

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

# **get_process_tree**
> BaseResponseProcessTree get_process_tree(analysis_id)

Get the dynamic execution results for process tree

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_process_tree import BaseResponseProcessTree
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
    api_instance = revengai.AnalysesDynamicExecutionApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Get the dynamic execution results for process tree
        api_response = api_instance.get_process_tree(analysis_id)
        print("The response of AnalysesDynamicExecutionApi->get_process_tree:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesDynamicExecutionApi->get_process_tree: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

### Return type

[**BaseResponseProcessTree**](BaseResponseProcessTree.md)

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

# **get_ttps**
> BaseResponseTTPS get_ttps(analysis_id)

Get the dynamic execution results for ttps

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_ttps import BaseResponseTTPS
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
    api_instance = revengai.AnalysesDynamicExecutionApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Get the dynamic execution results for ttps
        api_response = api_instance.get_ttps(analysis_id)
        print("The response of AnalysesDynamicExecutionApi->get_ttps:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesDynamicExecutionApi->get_ttps: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

### Return type

[**BaseResponseTTPS**](BaseResponseTTPS.md)

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

