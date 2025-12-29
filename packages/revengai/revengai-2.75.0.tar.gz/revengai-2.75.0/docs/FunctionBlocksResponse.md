# FunctionBlocksResponse

Response for returning disassembly of a function.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**blocks** | [**List[FunctionBlockResponse]**](FunctionBlockResponse.md) | Disassembly is broken into control flow blocks | 
**local_variables** | [**List[FunctionLocalVariableResponse]**](FunctionLocalVariableResponse.md) | Local variables associated with this function | 
**params** | [**List[FunctionParamResponse]**](FunctionParamResponse.md) | Params associated with this function | 
**overview_comment** | **str** |  | 

## Example

```python
from revengai.models.function_blocks_response import FunctionBlocksResponse

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionBlocksResponse from a JSON string
function_blocks_response_instance = FunctionBlocksResponse.from_json(json)
# print the JSON string representation of the object
print(FunctionBlocksResponse.to_json())

# convert the object into a dict
function_blocks_response_dict = function_blocks_response_instance.to_dict()
# create an instance of FunctionBlocksResponse from a dict
function_blocks_response_from_dict = FunctionBlocksResponse.from_dict(function_blocks_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


