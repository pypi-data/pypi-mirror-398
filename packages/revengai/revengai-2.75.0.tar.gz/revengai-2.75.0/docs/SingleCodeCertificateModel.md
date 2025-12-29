# SingleCodeCertificateModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**version** | **int** |  | 
**issued_on** | **str** |  | 
**expires_on** | **str** |  | 
**issuer_name** | **str** |  | 
**serial_number** | **str** |  | 
**subject_name** | **str** |  | 

## Example

```python
from revengai.models.single_code_certificate_model import SingleCodeCertificateModel

# TODO update the JSON string below
json = "{}"
# create an instance of SingleCodeCertificateModel from a JSON string
single_code_certificate_model_instance = SingleCodeCertificateModel.from_json(json)
# print the JSON string representation of the object
print(SingleCodeCertificateModel.to_json())

# convert the object into a dict
single_code_certificate_model_dict = single_code_certificate_model_instance.to_dict()
# create an instance of SingleCodeCertificateModel from a dict
single_code_certificate_model_from_dict = SingleCodeCertificateModel.from_dict(single_code_certificate_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


