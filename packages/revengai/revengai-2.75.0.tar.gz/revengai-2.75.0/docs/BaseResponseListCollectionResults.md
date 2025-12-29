# BaseResponseListCollectionResults


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**ListCollectionResults**](ListCollectionResults.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_list_collection_results import BaseResponseListCollectionResults

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseListCollectionResults from a JSON string
base_response_list_collection_results_instance = BaseResponseListCollectionResults.from_json(json)
# print the JSON string representation of the object
print(BaseResponseListCollectionResults.to_json())

# convert the object into a dict
base_response_list_collection_results_dict = base_response_list_collection_results_instance.to_dict()
# create an instance of BaseResponseListCollectionResults from a dict
base_response_list_collection_results_from_dict = BaseResponseListCollectionResults.from_dict(base_response_list_collection_results_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


