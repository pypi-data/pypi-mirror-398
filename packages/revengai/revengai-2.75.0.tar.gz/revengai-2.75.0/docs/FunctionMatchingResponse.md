# FunctionMatchingResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**progress** | **int** | Progress of the matching operation, represented as a percentage | [optional] [default to 0]
**status** | **str** |  | [optional] 
**total_time** | **int** |  | [optional] 
**error_message** | **str** |  | [optional] 
**current_page** | **int** |  | [optional] 
**total_pages** | **int** |  | [optional] 
**matches** | [**List[FunctionMatch]**](FunctionMatch.md) |  | [optional] 
**num_matches** | **int** |  | [optional] 
**num_debug_matches** | **int** |  | [optional] 
**updated_at** | **str** |  | [optional] 

## Example

```python
from revengai.models.function_matching_response import FunctionMatchingResponse

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionMatchingResponse from a JSON string
function_matching_response_instance = FunctionMatchingResponse.from_json(json)
# print the JSON string representation of the object
print(FunctionMatchingResponse.to_json())

# convert the object into a dict
function_matching_response_dict = function_matching_response_instance.to_dict()
# create an instance of FunctionMatchingResponse from a dict
function_matching_response_from_dict = FunctionMatchingResponse.from_dict(function_matching_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


