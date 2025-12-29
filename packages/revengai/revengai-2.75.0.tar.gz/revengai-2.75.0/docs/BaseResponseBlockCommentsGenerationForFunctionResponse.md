# BaseResponseBlockCommentsGenerationForFunctionResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**BlockCommentsGenerationForFunctionResponse**](BlockCommentsGenerationForFunctionResponse.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_block_comments_generation_for_function_response import BaseResponseBlockCommentsGenerationForFunctionResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseBlockCommentsGenerationForFunctionResponse from a JSON string
base_response_block_comments_generation_for_function_response_instance = BaseResponseBlockCommentsGenerationForFunctionResponse.from_json(json)
# print the JSON string representation of the object
print(BaseResponseBlockCommentsGenerationForFunctionResponse.to_json())

# convert the object into a dict
base_response_block_comments_generation_for_function_response_dict = base_response_block_comments_generation_for_function_response_instance.to_dict()
# create an instance of BaseResponseBlockCommentsGenerationForFunctionResponse from a dict
base_response_block_comments_generation_for_function_response_from_dict = BaseResponseBlockCommentsGenerationForFunctionResponse.from_dict(base_response_block_comments_generation_for_function_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


