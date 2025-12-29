# SandboxOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**enabled** | **bool** |  | [optional] [default to False]
**command_line_args** | **str** | The command line parameters to pass to the dynamic execution sandbox. Requires &#x60;sandbox&#x60; to be True. | [optional] [default to '']

## Example

```python
from revengai.models.sandbox_options import SandboxOptions

# TODO update the JSON string below
json = "{}"
# create an instance of SandboxOptions from a JSON string
sandbox_options_instance = SandboxOptions.from_json(json)
# print the JSON string representation of the object
print(SandboxOptions.to_json())

# convert the object into a dict
sandbox_options_dict = sandbox_options_instance.to_dict()
# create an instance of SandboxOptions from a dict
sandbox_options_from_dict = SandboxOptions.from_dict(sandbox_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


