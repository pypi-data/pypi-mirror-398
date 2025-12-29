# SBOMPackage


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | The name of the package | 
**version** | **str** | The version of the package | 

## Example

```python
from revengai.models.sbom_package import SBOMPackage

# TODO update the JSON string below
json = "{}"
# create an instance of SBOMPackage from a JSON string
sbom_package_instance = SBOMPackage.from_json(json)
# print the JSON string representation of the object
print(SBOMPackage.to_json())

# convert the object into a dict
sbom_package_dict = sbom_package_instance.to_dict()
# create an instance of SBOMPackage from a dict
sbom_package_from_dict = SBOMPackage.from_dict(sbom_package_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


