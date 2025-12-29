# SingleCodeSignatureModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**certificates** | [**List[SingleCodeCertificateModel]**](SingleCodeCertificateModel.md) |  | 
**authenticode_digest** | **str** |  | 

## Example

```python
from revengai.models.single_code_signature_model import SingleCodeSignatureModel

# TODO update the JSON string below
json = "{}"
# create an instance of SingleCodeSignatureModel from a JSON string
single_code_signature_model_instance = SingleCodeSignatureModel.from_json(json)
# print the JSON string representation of the object
print(SingleCodeSignatureModel.to_json())

# convert the object into a dict
single_code_signature_model_dict = single_code_signature_model_instance.to_dict()
# create an instance of SingleCodeSignatureModel from a dict
single_code_signature_model_from_dict = SingleCodeSignatureModel.from_dict(single_code_signature_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


