# CodeSignatureModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**signed** | **bool** |  | 
**valid_signature** | **bool** |  | 
**signatures** | [**List[SingleCodeSignatureModel]**](SingleCodeSignatureModel.md) |  | 

## Example

```python
from revengai.models.code_signature_model import CodeSignatureModel

# TODO update the JSON string below
json = "{}"
# create an instance of CodeSignatureModel from a JSON string
code_signature_model_instance = CodeSignatureModel.from_json(json)
# print the JSON string representation of the object
print(CodeSignatureModel.to_json())

# convert the object into a dict
code_signature_model_dict = code_signature_model_instance.to_dict()
# create an instance of CodeSignatureModel from a dict
code_signature_model_from_dict = CodeSignatureModel.from_dict(code_signature_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


