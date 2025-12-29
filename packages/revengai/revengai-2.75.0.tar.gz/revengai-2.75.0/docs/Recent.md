# Recent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**results** | [**List[AnalysisRecord]**](AnalysisRecord.md) | 2D List containing the results of the analysis | 

## Example

```python
from revengai.models.recent import Recent

# TODO update the JSON string below
json = "{}"
# create an instance of Recent from a JSON string
recent_instance = Recent.from_json(json)
# print the JSON string representation of the object
print(Recent.to_json())

# convert the object into a dict
recent_dict = recent_instance.to_dict()
# create an instance of Recent from a dict
recent_from_dict = Recent.from_dict(recent_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


