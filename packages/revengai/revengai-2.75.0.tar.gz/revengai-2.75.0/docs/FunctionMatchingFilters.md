# FunctionMatchingFilters


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**binary_ids** | **List[int]** | ID&#39;s of binaries to limit the search to, if empty, search all scoped binaries | [optional] [default to []]
**collection_ids** | **List[int]** | ID&#39;s of collections to limit the search to, if empty, search all scoped collections | [optional] [default to []]
**function_ids** | **List[int]** | ID&#39;s of functions to limit the search to, if empty, search all scoped functions | [optional] [default to []]
**debug_types** | **List[str]** | Limit the search to specific debug types, if empty, search all scoped debug &amp; non-debug functions | [optional] [default to []]

## Example

```python
from revengai.models.function_matching_filters import FunctionMatchingFilters

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionMatchingFilters from a JSON string
function_matching_filters_instance = FunctionMatchingFilters.from_json(json)
# print the JSON string representation of the object
print(FunctionMatchingFilters.to_json())

# convert the object into a dict
function_matching_filters_dict = function_matching_filters_instance.to_dict()
# create an instance of FunctionMatchingFilters from a dict
function_matching_filters_from_dict = FunctionMatchingFilters.from_dict(function_matching_filters_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


