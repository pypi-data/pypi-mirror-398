# FunctionBlockDestinationResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**destination_block_id** | **int** |  | 
**flowtype** | **str** | The type of execution flow between chunks | 
**vaddr** | **str** | The vaddr of the destination where the execution flow continues from | 

## Example

```python
from revengai.models.function_block_destination_response import FunctionBlockDestinationResponse

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionBlockDestinationResponse from a JSON string
function_block_destination_response_instance = FunctionBlockDestinationResponse.from_json(json)
# print the JSON string representation of the object
print(FunctionBlockDestinationResponse.to_json())

# convert the object into a dict
function_block_destination_response_dict = function_block_destination_response_instance.to_dict()
# create an instance of FunctionBlockDestinationResponse from a dict
function_block_destination_response_from_dict = FunctionBlockDestinationResponse.from_dict(function_block_destination_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


