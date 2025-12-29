# BaseResponseTTPS


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**TTPS**](TTPS.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_ttps import BaseResponseTTPS

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseTTPS from a JSON string
base_response_ttps_instance = BaseResponseTTPS.from_json(json)
# print the JSON string representation of the object
print(BaseResponseTTPS.to_json())

# convert the object into a dict
base_response_ttps_dict = base_response_ttps_instance.to_dict()
# create an instance of BaseResponseTTPS from a dict
base_response_ttps_from_dict = BaseResponseTTPS.from_dict(base_response_ttps_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


