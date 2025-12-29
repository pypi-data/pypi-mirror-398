# BaseResponseGenerationStatusList


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**GenerationStatusList**](GenerationStatusList.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_generation_status_list import BaseResponseGenerationStatusList

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseGenerationStatusList from a JSON string
base_response_generation_status_list_instance = BaseResponseGenerationStatusList.from_json(json)
# print the JSON string representation of the object
print(BaseResponseGenerationStatusList.to_json())

# convert the object into a dict
base_response_generation_status_list_dict = base_response_generation_status_list_instance.to_dict()
# create an instance of BaseResponseGenerationStatusList from a dict
base_response_generation_status_list_from_dict = BaseResponseGenerationStatusList.from_dict(base_response_generation_status_list_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


