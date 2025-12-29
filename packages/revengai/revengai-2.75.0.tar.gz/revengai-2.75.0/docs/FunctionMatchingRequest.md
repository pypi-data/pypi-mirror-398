# FunctionMatchingRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**model_id** | **int** | ID of the model used for function matching, used to determine the embedding model | 
**function_ids** | **List[int]** | ID&#39;s of functions to find matches for, must be at least one function ID | 
**min_similarity** | **float** | Minimum similarity expected for a match as a percentage, default is 90 | [optional] [default to 90.0]
**filters** | [**FunctionMatchingFilters**](FunctionMatchingFilters.md) |  | [optional] 
**results_per_function** | **int** | Maximum number of matches to return per function, default is 1, max is 50 | [optional] [default to 1]
**page** | **int** | Page number for paginated results, default is 1 (first page) | [optional] [default to 1]
**page_size** | **int** | Number of functions to return per page, default is 0 (all functions), max is 1000 | [optional] [default to 0]
**status_only** | **bool** | If set to true, only returns the status of the matching operation without the actual results | [optional] [default to False]
**no_cache** | **bool** | If set to true, forces the system to bypass any cached results and perform a fresh computation | [optional] [default to False]
**use_canonical_names** | **bool** | Whether to use canonical function names during function matching for confidence results, default is False | [optional] [default to False]

## Example

```python
from revengai.models.function_matching_request import FunctionMatchingRequest

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionMatchingRequest from a JSON string
function_matching_request_instance = FunctionMatchingRequest.from_json(json)
# print the JSON string representation of the object
print(FunctionMatchingRequest.to_json())

# convert the object into a dict
function_matching_request_dict = function_matching_request_instance.to_dict()
# create an instance of FunctionMatchingRequest from a dict
function_matching_request_from_dict = FunctionMatchingRequest.from_dict(function_matching_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


