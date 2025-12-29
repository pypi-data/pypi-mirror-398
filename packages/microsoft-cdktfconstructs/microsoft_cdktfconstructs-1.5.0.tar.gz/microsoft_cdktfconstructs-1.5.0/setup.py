import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "microsoft-cdktfconstructs",
    "version": "1.5.0",
    "description": "Azure CDK constructs using AZAPI provider for direct Azure REST API access. Version 1.0.0 - Major breaking change migration from AzureRM to AZAPI.",
    "license": "MIT",
    "url": "https://github.com/azure/terraform-cdk-constructs.git",
    "long_description_content_type": "text/markdown",
    "author": "Microsoft",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/azure/terraform-cdk-constructs.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "microsoft_cdktfconstructs",
        "microsoft_cdktfconstructs._jsii",
        "microsoft_cdktfconstructs.azure_actiongroup",
        "microsoft_cdktfconstructs.azure_activitylogalert",
        "microsoft_cdktfconstructs.azure_aks",
        "microsoft_cdktfconstructs.azure_diagnosticsettings",
        "microsoft_cdktfconstructs.azure_dnsforwardingruleset",
        "microsoft_cdktfconstructs.azure_dnsresolver",
        "microsoft_cdktfconstructs.azure_dnszone",
        "microsoft_cdktfconstructs.azure_metricalert",
        "microsoft_cdktfconstructs.azure_networkinterface",
        "microsoft_cdktfconstructs.azure_networksecuritygroup",
        "microsoft_cdktfconstructs.azure_policyassignment",
        "microsoft_cdktfconstructs.azure_policydefinition",
        "microsoft_cdktfconstructs.azure_privatednszone",
        "microsoft_cdktfconstructs.azure_publicipaddress",
        "microsoft_cdktfconstructs.azure_resourcegroup",
        "microsoft_cdktfconstructs.azure_roleassignment",
        "microsoft_cdktfconstructs.azure_roledefinition",
        "microsoft_cdktfconstructs.azure_storageaccount",
        "microsoft_cdktfconstructs.azure_subnet",
        "microsoft_cdktfconstructs.azure_virtualmachine",
        "microsoft_cdktfconstructs.azure_virtualnetwork",
        "microsoft_cdktfconstructs.azure_virtualnetworkgateway",
        "microsoft_cdktfconstructs.azure_virtualnetworkmanager",
        "microsoft_cdktfconstructs.azure_vmss",
        "microsoft_cdktfconstructs.core_azure",
        "microsoft_cdktfconstructs.testing"
    ],
    "package_data": {
        "microsoft_cdktfconstructs._jsii": [
            "terraform-cdk-constructs@1.5.0.jsii.tgz"
        ],
        "microsoft_cdktfconstructs": [
            "py.typed"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "cdktf==0.20.8",
        "constructs>=10.3.0, <11.0.0",
        "jsii>=1.117.0, <2.0.0",
        "publication>=0.0.3",
        "typeguard>=2.13.3,<4.3.0"
    ],
    "classifiers": [
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Typing :: Typed",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved"
    ],
    "scripts": []
}
"""
)

with open("README.md", encoding="utf8") as fp:
    kwargs["long_description"] = fp.read()


setuptools.setup(**kwargs)
