# revengai.ModelsApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_models**](ModelsApi.md#get_models) | **GET** /v2/models | Gets models


# **get_models**
> BaseResponseModelsResponse get_models()

Gets models

Gets active models available for analysis.

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_models_response import BaseResponseModelsResponse
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
    api_instance = revengai.ModelsApi(api_client)

    try:
        # Gets models
        api_response = api_instance.get_models()
        print("The response of ModelsApi->get_models:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ModelsApi->get_models: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**BaseResponseModelsResponse**](BaseResponseModelsResponse.md)

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

