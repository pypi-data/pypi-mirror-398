# revengai.AnalysesResultsMetadataApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_analysis_functions_paginated**](AnalysesResultsMetadataApi.md#get_analysis_functions_paginated) | **GET** /v2/analyses/{analysis_id}/functions | Get functions from analysis
[**get_capabilities**](AnalysesResultsMetadataApi.md#get_capabilities) | **GET** /v2/analyses/{analysis_id}/capabilities | Gets the capabilities from the analysis
[**get_communities**](AnalysesResultsMetadataApi.md#get_communities) | **GET** /v2/analyses/{analysis_id}/communities | Gets the communities found in the analysis
[**get_functions_list**](AnalysesResultsMetadataApi.md#get_functions_list) | **GET** /v2/analyses/{analysis_id}/functions/list | Gets functions from analysis
[**get_pdf**](AnalysesResultsMetadataApi.md#get_pdf) | **GET** /v2/analyses/{analysis_id}/pdf | Gets the PDF found in the analysis
[**get_sbom**](AnalysesResultsMetadataApi.md#get_sbom) | **GET** /v2/analyses/{analysis_id}/sbom | Gets the software-bill-of-materials (SBOM) found in the analysis
[**get_tags**](AnalysesResultsMetadataApi.md#get_tags) | **GET** /v2/analyses/{analysis_id}/tags | Get function tags with maliciousness score
[**get_vulnerabilities**](AnalysesResultsMetadataApi.md#get_vulnerabilities) | **GET** /v2/analyses/{analysis_id}/vulnerabilities | Gets the vulnerabilities found in the analysis


# **get_analysis_functions_paginated**
> BaseResponseAnalysisFunctionsList get_analysis_functions_paginated(analysis_id, page=page, page_size=page_size)

Get functions from analysis

Returns a paginated list of functions identified during analysis

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_analysis_functions_list import BaseResponseAnalysisFunctionsList
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
    api_instance = revengai.AnalysesResultsMetadataApi(api_client)
    analysis_id = 56 # int | 
    page = 1 # int | The page number to retrieve. (optional) (default to 1)
    page_size = 1000 # int | Number of items per page. (optional) (default to 1000)

    try:
        # Get functions from analysis
        api_response = api_instance.get_analysis_functions_paginated(analysis_id, page=page, page_size=page_size)
        print("The response of AnalysesResultsMetadataApi->get_analysis_functions_paginated:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesResultsMetadataApi->get_analysis_functions_paginated: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 
 **page** | **int**| The page number to retrieve. | [optional] [default to 1]
 **page_size** | **int**| Number of items per page. | [optional] [default to 1000]

### Return type

[**BaseResponseAnalysisFunctionsList**](BaseResponseAnalysisFunctionsList.md)

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

# **get_capabilities**
> BaseResponseCapabilities get_capabilities(analysis_id)

Gets the capabilities from the analysis

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_capabilities import BaseResponseCapabilities
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
    api_instance = revengai.AnalysesResultsMetadataApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Gets the capabilities from the analysis
        api_response = api_instance.get_capabilities(analysis_id)
        print("The response of AnalysesResultsMetadataApi->get_capabilities:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesResultsMetadataApi->get_capabilities: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

### Return type

[**BaseResponseCapabilities**](BaseResponseCapabilities.md)

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

# **get_communities**
> BaseResponseCommunities get_communities(analysis_id, user_name=user_name)

Gets the communities found in the analysis

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_communities import BaseResponseCommunities
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
    api_instance = revengai.AnalysesResultsMetadataApi(api_client)
    analysis_id = 56 # int | 
    user_name = 'user_name_example' # str | The user name to limit communities to (optional)

    try:
        # Gets the communities found in the analysis
        api_response = api_instance.get_communities(analysis_id, user_name=user_name)
        print("The response of AnalysesResultsMetadataApi->get_communities:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesResultsMetadataApi->get_communities: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 
 **user_name** | **str**| The user name to limit communities to | [optional] 

### Return type

[**BaseResponseCommunities**](BaseResponseCommunities.md)

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

# **get_functions_list**
> BaseResponseAnalysisFunctions get_functions_list(analysis_id, search_term=search_term, min_v_addr=min_v_addr, max_v_addr=max_v_addr)

Gets functions from analysis

Gets the functions identified during analysis

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_analysis_functions import BaseResponseAnalysisFunctions
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
    api_instance = revengai.AnalysesResultsMetadataApi(api_client)
    analysis_id = 56 # int | 
    search_term = 'search_term_example' # str |  (optional)
    min_v_addr = 56 # int |  (optional)
    max_v_addr = 56 # int |  (optional)

    try:
        # Gets functions from analysis
        api_response = api_instance.get_functions_list(analysis_id, search_term=search_term, min_v_addr=min_v_addr, max_v_addr=max_v_addr)
        print("The response of AnalysesResultsMetadataApi->get_functions_list:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesResultsMetadataApi->get_functions_list: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 
 **search_term** | **str**|  | [optional] 
 **min_v_addr** | **int**|  | [optional] 
 **max_v_addr** | **int**|  | [optional] 

### Return type

[**BaseResponseAnalysisFunctions**](BaseResponseAnalysisFunctions.md)

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

# **get_pdf**
> object get_pdf(analysis_id)

Gets the PDF found in the analysis

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
    api_instance = revengai.AnalysesResultsMetadataApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Gets the PDF found in the analysis
        api_response = api_instance.get_pdf(analysis_id)
        print("The response of AnalysesResultsMetadataApi->get_pdf:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesResultsMetadataApi->get_pdf: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

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

# **get_sbom**
> BaseResponseListSBOM get_sbom(analysis_id)

Gets the software-bill-of-materials (SBOM) found in the analysis

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_list_sbom import BaseResponseListSBOM
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
    api_instance = revengai.AnalysesResultsMetadataApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Gets the software-bill-of-materials (SBOM) found in the analysis
        api_response = api_instance.get_sbom(analysis_id)
        print("The response of AnalysesResultsMetadataApi->get_sbom:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesResultsMetadataApi->get_sbom: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

### Return type

[**BaseResponseListSBOM**](BaseResponseListSBOM.md)

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

# **get_tags**
> BaseResponseAnalysisTags get_tags(analysis_id)

Get function tags with maliciousness score

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_analysis_tags import BaseResponseAnalysisTags
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
    api_instance = revengai.AnalysesResultsMetadataApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Get function tags with maliciousness score
        api_response = api_instance.get_tags(analysis_id)
        print("The response of AnalysesResultsMetadataApi->get_tags:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesResultsMetadataApi->get_tags: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

### Return type

[**BaseResponseAnalysisTags**](BaseResponseAnalysisTags.md)

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

# **get_vulnerabilities**
> BaseResponseVulnerabilities get_vulnerabilities(analysis_id)

Gets the vulnerabilities found in the analysis

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_vulnerabilities import BaseResponseVulnerabilities
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
    api_instance = revengai.AnalysesResultsMetadataApi(api_client)
    analysis_id = 56 # int | 

    try:
        # Gets the vulnerabilities found in the analysis
        api_response = api_instance.get_vulnerabilities(analysis_id)
        print("The response of AnalysesResultsMetadataApi->get_vulnerabilities:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalysesResultsMetadataApi->get_vulnerabilities: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**|  | 

### Return type

[**BaseResponseVulnerabilities**](BaseResponseVulnerabilities.md)

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

