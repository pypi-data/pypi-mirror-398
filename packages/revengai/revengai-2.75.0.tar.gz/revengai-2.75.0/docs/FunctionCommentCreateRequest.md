# FunctionCommentCreateRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**content** | **str** | Comment text content | 
**context** | [**DecompilationCommentContext**](DecompilationCommentContext.md) | Comment context for a function decompilation | [optional] 

## Example

```python
from revengai.models.function_comment_create_request import FunctionCommentCreateRequest

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionCommentCreateRequest from a JSON string
function_comment_create_request_instance = FunctionCommentCreateRequest.from_json(json)
# print the JSON string representation of the object
print(FunctionCommentCreateRequest.to_json())

# convert the object into a dict
function_comment_create_request_dict = function_comment_create_request_instance.to_dict()
# create an instance of FunctionCommentCreateRequest from a dict
function_comment_create_request_from_dict = FunctionCommentCreateRequest.from_dict(function_comment_create_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


