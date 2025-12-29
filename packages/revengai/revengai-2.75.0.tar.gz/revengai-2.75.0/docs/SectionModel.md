# SectionModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**number_of_sections** | **int** |  | 
**sections** | [**List[SingleSectionModel]**](SingleSectionModel.md) |  | 

## Example

```python
from revengai.models.section_model import SectionModel

# TODO update the JSON string below
json = "{}"
# create an instance of SectionModel from a JSON string
section_model_instance = SectionModel.from_json(json)
# print the JSON string representation of the object
print(SectionModel.to_json())

# convert the object into a dict
section_model_dict = section_model_instance.to_dict()
# create an instance of SectionModel from a dict
section_model_from_dict = SectionModel.from_dict(section_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


