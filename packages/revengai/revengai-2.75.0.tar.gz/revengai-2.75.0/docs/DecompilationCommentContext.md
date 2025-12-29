# DecompilationCommentContext


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**start_line** | **int** |  | 
**end_line** | **int** |  | 

## Example

```python
from revengai.models.decompilation_comment_context import DecompilationCommentContext

# TODO update the JSON string below
json = "{}"
# create an instance of DecompilationCommentContext from a JSON string
decompilation_comment_context_instance = DecompilationCommentContext.from_json(json)
# print the JSON string representation of the object
print(DecompilationCommentContext.to_json())

# convert the object into a dict
decompilation_comment_context_dict = decompilation_comment_context_instance.to_dict()
# create an instance of DecompilationCommentContext from a dict
decompilation_comment_context_from_dict = DecompilationCommentContext.from_dict(decompilation_comment_context_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


