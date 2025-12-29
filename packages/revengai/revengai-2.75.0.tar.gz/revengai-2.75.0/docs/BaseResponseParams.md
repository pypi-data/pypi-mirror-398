# BaseResponseParams


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**Params**](Params.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_params import BaseResponseParams

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseParams from a JSON string
base_response_params_instance = BaseResponseParams.from_json(json)
# print the JSON string representation of the object
print(BaseResponseParams.to_json())

# convert the object into a dict
base_response_params_dict = base_response_params_instance.to_dict()
# create an instance of BaseResponseParams from a dict
base_response_params_from_dict = BaseResponseParams.from_dict(base_response_params_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


