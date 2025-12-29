# revengai.SearchApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**search_binaries**](SearchApi.md#search_binaries) | **GET** /v2/search/binaries | Binaries search
[**search_collections**](SearchApi.md#search_collections) | **GET** /v2/search/collections | Collections search
[**search_functions**](SearchApi.md#search_functions) | **GET** /v2/search/functions | Functions search
[**search_tags**](SearchApi.md#search_tags) | **GET** /v2/search/tags | Tags search


# **search_binaries**
> BaseResponseBinarySearchResponse search_binaries(page=page, page_size=page_size, partial_name=partial_name, partial_sha256=partial_sha256, tags=tags, model_name=model_name, user_files_only=user_files_only)

Binaries search

Searches for a specific binary

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_binary_search_response import BaseResponseBinarySearchResponse
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
    api_instance = revengai.SearchApi(api_client)
    page = 1 # int | The page number to retrieve. (optional) (default to 1)
    page_size = 10 # int | Number of items per page. (optional) (default to 10)
    partial_name = 'partial_name_example' # str | The partial or full name of the binary being searched (optional)
    partial_sha256 = 'partial_sha256_example' # str | The partial or full sha256 of the binary being searched (optional)
    tags = ['tags_example'] # List[str] | The tags to be searched for (optional)
    model_name = 'model_name_example' # str | The name of the model used to analyze the binary the function belongs to (optional)
    user_files_only = False # bool | Whether to only search user's uploaded files (optional) (default to False)

    try:
        # Binaries search
        api_response = api_instance.search_binaries(page=page, page_size=page_size, partial_name=partial_name, partial_sha256=partial_sha256, tags=tags, model_name=model_name, user_files_only=user_files_only)
        print("The response of SearchApi->search_binaries:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SearchApi->search_binaries: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**| The page number to retrieve. | [optional] [default to 1]
 **page_size** | **int**| Number of items per page. | [optional] [default to 10]
 **partial_name** | **str**| The partial or full name of the binary being searched | [optional] 
 **partial_sha256** | **str**| The partial or full sha256 of the binary being searched | [optional] 
 **tags** | [**List[str]**](str.md)| The tags to be searched for | [optional] 
 **model_name** | **str**| The name of the model used to analyze the binary the function belongs to | [optional] 
 **user_files_only** | **bool**| Whether to only search user&#39;s uploaded files | [optional] [default to False]

### Return type

[**BaseResponseBinarySearchResponse**](BaseResponseBinarySearchResponse.md)

### Authorization

[APIKey](../README.md#APIKey)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | You must provide at least one of the filters; partial_name, partial_sha256, tags or model_name to search |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **search_collections**
> BaseResponseCollectionSearchResponse search_collections(page=page, page_size=page_size, partial_collection_name=partial_collection_name, partial_binary_name=partial_binary_name, partial_binary_sha256=partial_binary_sha256, tags=tags, model_name=model_name, filters=filters, order_by=order_by, order_by_direction=order_by_direction)

Collections search

Searches for a specific collection

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.app_api_rest_v2_collections_enums_order_by import AppApiRestV2CollectionsEnumsOrderBy
from revengai.models.base_response_collection_search_response import BaseResponseCollectionSearchResponse
from revengai.models.filters import Filters
from revengai.models.order import Order
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
    api_instance = revengai.SearchApi(api_client)
    page = 1 # int | The page number to retrieve. (optional) (default to 1)
    page_size = 10 # int | Number of items per page. (optional) (default to 10)
    partial_collection_name = 'partial_collection_name_example' # str | The partial or full name of the collection being searched (optional)
    partial_binary_name = 'partial_binary_name_example' # str | The partial or full name of the binary belonging to the collection (optional)
    partial_binary_sha256 = 'partial_binary_sha256_example' # str | The partial or full sha256 of the binary belonging to the collection (optional)
    tags = ['tags_example'] # List[str] | The tags to be searched for (optional)
    model_name = 'model_name_example' # str | The name of the model used to analyze the binary the function belongs to (optional)
    filters = [revengai.Filters()] # List[Filters] | The filters to be used for the search (optional)
    order_by = revengai.AppApiRestV2CollectionsEnumsOrderBy() # AppApiRestV2CollectionsEnumsOrderBy | The field to sort the order by in the results (optional)
    order_by_direction = revengai.Order() # Order | The order direction in which to return results (optional)

    try:
        # Collections search
        api_response = api_instance.search_collections(page=page, page_size=page_size, partial_collection_name=partial_collection_name, partial_binary_name=partial_binary_name, partial_binary_sha256=partial_binary_sha256, tags=tags, model_name=model_name, filters=filters, order_by=order_by, order_by_direction=order_by_direction)
        print("The response of SearchApi->search_collections:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SearchApi->search_collections: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**| The page number to retrieve. | [optional] [default to 1]
 **page_size** | **int**| Number of items per page. | [optional] [default to 10]
 **partial_collection_name** | **str**| The partial or full name of the collection being searched | [optional] 
 **partial_binary_name** | **str**| The partial or full name of the binary belonging to the collection | [optional] 
 **partial_binary_sha256** | **str**| The partial or full sha256 of the binary belonging to the collection | [optional] 
 **tags** | [**List[str]**](str.md)| The tags to be searched for | [optional] 
 **model_name** | **str**| The name of the model used to analyze the binary the function belongs to | [optional] 
 **filters** | [**List[Filters]**](Filters.md)| The filters to be used for the search | [optional] 
 **order_by** | [**AppApiRestV2CollectionsEnumsOrderBy**](.md)| The field to sort the order by in the results | [optional] 
 **order_by_direction** | [**Order**](.md)| The order direction in which to return results | [optional] 

### Return type

[**BaseResponseCollectionSearchResponse**](BaseResponseCollectionSearchResponse.md)

### Authorization

[APIKey](../README.md#APIKey)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | You must provide at least one of the filters; partial_collection_name, partial_binary_name, partial_binary_sha256, tags or model_name to search |  -  |
**404** | The model name provided does not exist |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **search_functions**
> BaseResponseFunctionSearchResponse search_functions(page=page, page_size=page_size, partial_name=partial_name, model_name=model_name)

Functions search

Searches for a specific function

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_function_search_response import BaseResponseFunctionSearchResponse
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
    api_instance = revengai.SearchApi(api_client)
    page = 1 # int | The page number to retrieve. (optional) (default to 1)
    page_size = 10 # int | Number of items per page. (optional) (default to 10)
    partial_name = 'partial_name_example' # str | The partial or full name of the function being searched (optional)
    model_name = 'model_name_example' # str | The name of the model used to analyze the binary the function belongs to (optional)

    try:
        # Functions search
        api_response = api_instance.search_functions(page=page, page_size=page_size, partial_name=partial_name, model_name=model_name)
        print("The response of SearchApi->search_functions:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SearchApi->search_functions: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**| The page number to retrieve. | [optional] [default to 1]
 **page_size** | **int**| Number of items per page. | [optional] [default to 10]
 **partial_name** | **str**| The partial or full name of the function being searched | [optional] 
 **model_name** | **str**| The name of the model used to analyze the binary the function belongs to | [optional] 

### Return type

[**BaseResponseFunctionSearchResponse**](BaseResponseFunctionSearchResponse.md)

### Authorization

[APIKey](../README.md#APIKey)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | You must provide at least one of the filters; partial_name, or model_name to search |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **search_tags**
> BaseResponseTagSearchResponse search_tags(partial_name, page=page, page_size=page_size)

Tags search

Searches for tags by there name

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_tag_search_response import BaseResponseTagSearchResponse
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
    api_instance = revengai.SearchApi(api_client)
    partial_name = 'partial_name_example' # str | The partial or full name of the tag to search for
    page = 1 # int | The page number to retrieve. (optional) (default to 1)
    page_size = 10 # int | Number of items per page. (optional) (default to 10)

    try:
        # Tags search
        api_response = api_instance.search_tags(partial_name, page=page, page_size=page_size)
        print("The response of SearchApi->search_tags:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SearchApi->search_tags: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **partial_name** | **str**| The partial or full name of the tag to search for | 
 **page** | **int**| The page number to retrieve. | [optional] [default to 1]
 **page_size** | **int**| Number of items per page. | [optional] [default to 10]

### Return type

[**BaseResponseTagSearchResponse**](BaseResponseTagSearchResponse.md)

### Authorization

[APIKey](../README.md#APIKey)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | You must provide a partial_name to search and it must be greater than 3 characters |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

