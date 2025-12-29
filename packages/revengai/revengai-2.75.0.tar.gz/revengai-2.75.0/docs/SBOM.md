# SBOM


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**packages** | [**List[SBOMPackage]**](SBOMPackage.md) | The packages found | 
**imported_libs** | **List[str]** | The import libraries found | 

## Example

```python
from revengai.models.sbom import SBOM

# TODO update the JSON string below
json = "{}"
# create an instance of SBOM from a JSON string
sbom_instance = SBOM.from_json(json)
# print the JSON string representation of the object
print(SBOM.to_json())

# convert the object into a dict
sbom_dict = sbom_instance.to_dict()
# create an instance of SBOM from a dict
sbom_from_dict = SBOM.from_dict(sbom_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


