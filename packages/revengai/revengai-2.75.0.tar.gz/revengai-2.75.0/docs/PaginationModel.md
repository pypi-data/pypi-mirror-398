# PaginationModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**page_size** | **int** |  | 
**page_number** | **int** |  | 
**has_next_page** | **bool** |  | 

## Example

```python
from revengai.models.pagination_model import PaginationModel

# TODO update the JSON string below
json = "{}"
# create an instance of PaginationModel from a JSON string
pagination_model_instance = PaginationModel.from_json(json)
# print the JSON string representation of the object
print(PaginationModel.to_json())

# convert the object into a dict
pagination_model_dict = pagination_model_instance.to_dict()
# create an instance of PaginationModel from a dict
pagination_model_from_dict = PaginationModel.from_dict(pagination_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


