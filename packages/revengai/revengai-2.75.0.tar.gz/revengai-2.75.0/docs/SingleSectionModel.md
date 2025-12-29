# SingleSectionModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**virtual_address** | **int** |  | 
**virtual_size** | **int** |  | 
**characteristics** | **str** |  | 
**raw_size** | **int** |  | 
**entropy** | **float** |  | 
**sha3_256** | **str** |  | 

## Example

```python
from revengai.models.single_section_model import SingleSectionModel

# TODO update the JSON string below
json = "{}"
# create an instance of SingleSectionModel from a JSON string
single_section_model_instance = SingleSectionModel.from_json(json)
# print the JSON string representation of the object
print(SingleSectionModel.to_json())

# convert the object into a dict
single_section_model_dict = single_section_model_instance.to_dict()
# create an instance of SingleSectionModel from a dict
single_section_model_from_dict = SingleSectionModel.from_dict(single_section_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


