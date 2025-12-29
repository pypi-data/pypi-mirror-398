# FunctionBlockResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**asm** | **List[str]** | The ordered assembly strings for this chunk | 
**id** | **int** | ID of the block | 
**min_addr** | **int** | The minimum vaddr of the block | 
**max_addr** | **int** | The maximum vaddr of the block | 
**destinations** | [**List[FunctionBlockDestinationResponse]**](FunctionBlockDestinationResponse.md) | The potential execution flow destinations from this block | 
**comment** | **str** |  | [optional] 

## Example

```python
from revengai.models.function_block_response import FunctionBlockResponse

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionBlockResponse from a JSON string
function_block_response_instance = FunctionBlockResponse.from_json(json)
# print the JSON string representation of the object
print(FunctionBlockResponse.to_json())

# convert the object into a dict
function_block_response_dict = function_block_response_instance.to_dict()
# create an instance of FunctionBlockResponse from a dict
function_block_response_from_dict = FunctionBlockResponse.from_dict(function_block_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


