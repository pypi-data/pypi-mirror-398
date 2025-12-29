# Created


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**analysis_id** | **int** | The ID corresponding to the newly created analysis | 
**binary_id** | **int** | The ID corresponding to the binary that was created | 
**reference** | **str** | Deprecated will always be empty string | 

## Example

```python
from revengai.models.created import Created

# TODO update the JSON string below
json = "{}"
# create an instance of Created from a JSON string
created_instance = Created.from_json(json)
# print the JSON string representation of the object
print(Created.to_json())

# convert the object into a dict
created_dict = created_instance.to_dict()
# create an instance of Created from a dict
created_from_dict = Created.from_dict(created_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


