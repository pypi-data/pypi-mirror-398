# revengai.CollectionsApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_collection**](CollectionsApi.md#create_collection) | **POST** /v2/collections | Creates new collection information
[**delete_collection**](CollectionsApi.md#delete_collection) | **DELETE** /v2/collections/{collection_id} | Deletes a collection
[**get_collection**](CollectionsApi.md#get_collection) | **GET** /v2/collections/{collection_id} | Returns a collection
[**list_collections**](CollectionsApi.md#list_collections) | **GET** /v2/collections | Gets basic collections information
[**update_collection**](CollectionsApi.md#update_collection) | **PATCH** /v2/collections/{collection_id} | Updates a collection
[**update_collection_binaries**](CollectionsApi.md#update_collection_binaries) | **PATCH** /v2/collections/{collection_id}/binaries | Updates a collection binaries
[**update_collection_tags**](CollectionsApi.md#update_collection_tags) | **PATCH** /v2/collections/{collection_id}/tags | Updates a collection tags


# **create_collection**
> BaseResponseCollectionResponse create_collection(collection_create_request)

Creates new collection information

A collection is a group of binaries that are related in some way. This endpoint creates a new collection and allows you to add tags and binaries to it. If you add tags or binaries to the collection, they will be returned in the response.

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_collection_response import BaseResponseCollectionResponse
from revengai.models.collection_create_request import CollectionCreateRequest
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
    api_instance = revengai.CollectionsApi(api_client)
    collection_create_request = revengai.CollectionCreateRequest() # CollectionCreateRequest | 

    try:
        # Creates new collection information
        api_response = api_instance.create_collection(collection_create_request)
        print("The response of CollectionsApi->create_collection:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CollectionsApi->create_collection: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **collection_create_request** | [**CollectionCreateRequest**](CollectionCreateRequest.md)|  | 

### Return type

[**BaseResponseCollectionResponse**](BaseResponseCollectionResponse.md)

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

# **delete_collection**
> BaseResponseBool delete_collection(collection_id)

Deletes a collection

Deletes a collection

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
    api_instance = revengai.CollectionsApi(api_client)
    collection_id = 56 # int | 

    try:
        # Deletes a collection
        api_response = api_instance.delete_collection(collection_id)
        print("The response of CollectionsApi->delete_collection:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CollectionsApi->delete_collection: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **collection_id** | **int**|  | 

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

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_collection**
> BaseResponseCollectionResponse get_collection(collection_id, include_tags=include_tags, include_binaries=include_binaries, page_size=page_size, page_number=page_number, binary_search_str=binary_search_str)

Returns a collection

Gets a single collection. The collection can include binaries and tags if requested. You can specify whether to include tags and binaries in the response by using the query string parameters defined.

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_collection_response import BaseResponseCollectionResponse
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
    api_instance = revengai.CollectionsApi(api_client)
    collection_id = 56 # int | 
    include_tags = False # bool |  (optional) (default to False)
    include_binaries = False # bool |  (optional) (default to False)
    page_size = 10 # int |  (optional) (default to 10)
    page_number = 1 # int |  (optional) (default to 1)
    binary_search_str = 'binary_search_str_example' # str |  (optional)

    try:
        # Returns a collection
        api_response = api_instance.get_collection(collection_id, include_tags=include_tags, include_binaries=include_binaries, page_size=page_size, page_number=page_number, binary_search_str=binary_search_str)
        print("The response of CollectionsApi->get_collection:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CollectionsApi->get_collection: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **collection_id** | **int**|  | 
 **include_tags** | **bool**|  | [optional] [default to False]
 **include_binaries** | **bool**|  | [optional] [default to False]
 **page_size** | **int**|  | [optional] [default to 10]
 **page_number** | **int**|  | [optional] [default to 1]
 **binary_search_str** | **str**|  | [optional] 

### Return type

[**BaseResponseCollectionResponse**](BaseResponseCollectionResponse.md)

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

# **list_collections**
> BaseResponseListCollectionResults list_collections(search_term=search_term, filters=filters, limit=limit, offset=offset, order_by=order_by, order=order)

Gets basic collections information

Returns a list of collections

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.app_api_rest_v2_collections_enums_order_by import AppApiRestV2CollectionsEnumsOrderBy
from revengai.models.base_response_list_collection_results import BaseResponseListCollectionResults
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
    api_instance = revengai.CollectionsApi(api_client)
    search_term = '' # str |  (optional) (default to '')
    filters = [] # List[Filters] |  (optional) (default to [])
    limit = 20 # int |  (optional) (default to 20)
    offset = 0 # int |  (optional) (default to 0)
    order_by = revengai.AppApiRestV2CollectionsEnumsOrderBy() # AppApiRestV2CollectionsEnumsOrderBy |  (optional)
    order = revengai.Order() # Order |  (optional)

    try:
        # Gets basic collections information
        api_response = api_instance.list_collections(search_term=search_term, filters=filters, limit=limit, offset=offset, order_by=order_by, order=order)
        print("The response of CollectionsApi->list_collections:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CollectionsApi->list_collections: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **search_term** | **str**|  | [optional] [default to &#39;&#39;]
 **filters** | [**List[Filters]**](Filters.md)|  | [optional] [default to []]
 **limit** | **int**|  | [optional] [default to 20]
 **offset** | **int**|  | [optional] [default to 0]
 **order_by** | [**AppApiRestV2CollectionsEnumsOrderBy**](.md)|  | [optional] 
 **order** | [**Order**](.md)|  | [optional] 

### Return type

[**BaseResponseListCollectionResults**](BaseResponseListCollectionResults.md)

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

# **update_collection**
> BaseResponseCollectionResponse update_collection(collection_id, collection_update_request)

Updates a collection

Updates a collection, you can update the collection name, description, and scope

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_collection_response import BaseResponseCollectionResponse
from revengai.models.collection_update_request import CollectionUpdateRequest
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
    api_instance = revengai.CollectionsApi(api_client)
    collection_id = 56 # int | 
    collection_update_request = revengai.CollectionUpdateRequest() # CollectionUpdateRequest | 

    try:
        # Updates a collection
        api_response = api_instance.update_collection(collection_id, collection_update_request)
        print("The response of CollectionsApi->update_collection:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CollectionsApi->update_collection: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **collection_id** | **int**|  | 
 **collection_update_request** | [**CollectionUpdateRequest**](CollectionUpdateRequest.md)|  | 

### Return type

[**BaseResponseCollectionResponse**](BaseResponseCollectionResponse.md)

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

# **update_collection_binaries**
> BaseResponseCollectionBinariesUpdateResponse update_collection_binaries(collection_id, collection_binaries_update_request)

Updates a collection binaries

Updates/changes a collection binaries to whatever is provided in the request. After this update the collection will only contain the binaries provided in the request.

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_collection_binaries_update_response import BaseResponseCollectionBinariesUpdateResponse
from revengai.models.collection_binaries_update_request import CollectionBinariesUpdateRequest
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
    api_instance = revengai.CollectionsApi(api_client)
    collection_id = 56 # int | 
    collection_binaries_update_request = revengai.CollectionBinariesUpdateRequest() # CollectionBinariesUpdateRequest | 

    try:
        # Updates a collection binaries
        api_response = api_instance.update_collection_binaries(collection_id, collection_binaries_update_request)
        print("The response of CollectionsApi->update_collection_binaries:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CollectionsApi->update_collection_binaries: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **collection_id** | **int**|  | 
 **collection_binaries_update_request** | [**CollectionBinariesUpdateRequest**](CollectionBinariesUpdateRequest.md)|  | 

### Return type

[**BaseResponseCollectionBinariesUpdateResponse**](BaseResponseCollectionBinariesUpdateResponse.md)

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

# **update_collection_tags**
> BaseResponseCollectionTagsUpdateResponse update_collection_tags(collection_id, collection_tags_update_request)

Updates a collection tags

Updates/changes a collection tags to whatever is provided in the request. After this update the collection will only contain the tags provided in the request.

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_collection_tags_update_response import BaseResponseCollectionTagsUpdateResponse
from revengai.models.collection_tags_update_request import CollectionTagsUpdateRequest
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
    api_instance = revengai.CollectionsApi(api_client)
    collection_id = 56 # int | 
    collection_tags_update_request = revengai.CollectionTagsUpdateRequest() # CollectionTagsUpdateRequest | 

    try:
        # Updates a collection tags
        api_response = api_instance.update_collection_tags(collection_id, collection_tags_update_request)
        print("The response of CollectionsApi->update_collection_tags:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CollectionsApi->update_collection_tags: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **collection_id** | **int**|  | 
 **collection_tags_update_request** | [**CollectionTagsUpdateRequest**](CollectionTagsUpdateRequest.md)|  | 

### Return type

[**BaseResponseCollectionTagsUpdateResponse**](BaseResponseCollectionTagsUpdateResponse.md)

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

