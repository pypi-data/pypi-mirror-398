# StatusOutput


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**analysis_id** | **int** | The ID corresponding to the checked status | 
**analysis_status** | **str** | The status of the checked analysis | 

## Example

```python
from revengai.models.status_output import StatusOutput

# TODO update the JSON string below
json = "{}"
# create an instance of StatusOutput from a JSON string
status_output_instance = StatusOutput.from_json(json)
# print the JSON string representation of the object
print(StatusOutput.to_json())

# convert the object into a dict
status_output_dict = status_output_instance.to_dict()
# create an instance of StatusOutput from a dict
status_output_from_dict = StatusOutput.from_dict(status_output_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


