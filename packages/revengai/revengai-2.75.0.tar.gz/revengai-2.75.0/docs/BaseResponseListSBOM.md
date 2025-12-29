# BaseResponseListSBOM


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**List[SBOM]**](SBOM.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_list_sbom import BaseResponseListSBOM

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseListSBOM from a JSON string
base_response_list_sbom_instance = BaseResponseListSBOM.from_json(json)
# print the JSON string representation of the object
print(BaseResponseListSBOM.to_json())

# convert the object into a dict
base_response_list_sbom_dict = base_response_list_sbom_instance.to_dict()
# create an instance of BaseResponseListSBOM from a dict
base_response_list_sbom_from_dict = BaseResponseListSBOM.from_dict(base_response_list_sbom_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


