# TTPSElement


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**attack** | [**List[TTPSAttack]**](TTPSAttack.md) |  | 
**occurrences** | [**List[TTPSOccurance]**](TTPSOccurance.md) |  | 
**score** | **int** |  | 

## Example

```python
from revengai.models.ttps_element import TTPSElement

# TODO update the JSON string below
json = "{}"
# create an instance of TTPSElement from a JSON string
ttps_element_instance = TTPSElement.from_json(json)
# print the JSON string representation of the object
print(TTPSElement.to_json())

# convert the object into a dict
ttps_element_dict = ttps_element_instance.to_dict()
# create an instance of TTPSElement from a dict
ttps_element_from_dict = TTPSElement.from_dict(ttps_element_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


