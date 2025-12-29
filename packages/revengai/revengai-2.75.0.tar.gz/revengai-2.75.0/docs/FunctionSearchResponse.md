# FunctionSearchResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**results** | [**List[FunctionSearchResult]**](FunctionSearchResult.md) | The results of the search | 

## Example

```python
from revengai.models.function_search_response import FunctionSearchResponse

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionSearchResponse from a JSON string
function_search_response_instance = FunctionSearchResponse.from_json(json)
# print the JSON string representation of the object
print(FunctionSearchResponse.to_json())

# convert the object into a dict
function_search_response_dict = function_search_response_instance.to_dict()
# create an instance of FunctionSearchResponse from a dict
function_search_response_from_dict = FunctionSearchResponse.from_dict(function_search_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


