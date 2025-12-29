# AnalysisConfig


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**scrape_third_party_config** | [**ScrapeThirdPartyConfig**](ScrapeThirdPartyConfig.md) | Settings to scrape third party sources | [optional] 
**generate_cves** | **bool** | A configuration option for fetching CVEs data. | [optional] [default to False]
**generate_sbom** | **bool** | A configuration option for generating software bill of materials data. | [optional] [default to False]
**generate_capabilities** | **bool** | A configuration option for generating capabilities of a binary | [optional] [default to False]
**no_cache** | **bool** | When enabled, skips using cached data within the processing. | [optional] [default to False]
**advanced_analysis** | **bool** | Enables an advanced security analysis. | [optional] [default to False]
**sandbox_config** | [**SandboxOptions**](SandboxOptions.md) | Including a sandbox config enables the dynamic execution sandbox | [optional] 

## Example

```python
from revengai.models.analysis_config import AnalysisConfig

# TODO update the JSON string below
json = "{}"
# create an instance of AnalysisConfig from a JSON string
analysis_config_instance = AnalysisConfig.from_json(json)
# print the JSON string representation of the object
print(AnalysisConfig.to_json())

# convert the object into a dict
analysis_config_dict = analysis_config_instance.to_dict()
# create an instance of AnalysisConfig from a dict
analysis_config_from_dict = AnalysisConfig.from_dict(analysis_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


