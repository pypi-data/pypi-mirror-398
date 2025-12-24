<a id="types-boto3-connect"></a>

# types-boto3-connect

[![PyPI - types-boto3-connect](https://img.shields.io/pypi/v/types-boto3-connect.svg?color=blue)](https://pypi.org/project/types-boto3-connect/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/types-boto3-connect.svg?color=blue)](https://pypi.org/project/types-boto3-connect/)
[![Docs](https://img.shields.io/readthedocs/boto3-stubs.svg?color=blue)](https://youtype.github.io/types_boto3_docs/)
[![PyPI - Downloads](https://static.pepy.tech/badge/types-boto3-connect)](https://pypistats.org/packages/types-boto3-connect)

![boto3.typed](https://github.com/youtype/mypy_boto3_builder/raw/main/logo.png)

Type annotations for [boto3 Connect 1.42.14](https://pypi.org/project/boto3/)
compatible with [VSCode](https://code.visualstudio.com/),
[PyCharm](https://www.jetbrains.com/pycharm/),
[Emacs](https://www.gnu.org/software/emacs/),
[Sublime Text](https://www.sublimetext.com/),
[mypy](https://github.com/python/mypy),
[pyright](https://github.com/microsoft/pyright) and other tools.

Generated with
[mypy-boto3-builder 8.12.0](https://github.com/youtype/mypy_boto3_builder).

More information can be found on
[types-boto3](https://pypi.org/project/types-boto3/) page and in
[types-boto3-connect docs](https://youtype.github.io/types_boto3_docs/types_boto3_connect/).

See how it helps you find and fix potential bugs:

![types-boto3 demo](https://github.com/youtype/mypy_boto3_builder/raw/main/demo.gif)

- [types-boto3-connect](#types-boto3-connect)
  - [How to install](#how-to-install)
    - [Generate locally (recommended)](<#generate-locally-(recommended)>)
    - [VSCode extension](#vscode-extension)
    - [From PyPI with pip](#from-pypi-with-pip)
  - [How to uninstall](#how-to-uninstall)
  - [Usage](#usage)
    - [VSCode](#vscode)
    - [PyCharm](#pycharm)
    - [Emacs](#emacs)
    - [Sublime Text](#sublime-text)
    - [Other IDEs](#other-ides)
    - [mypy](#mypy)
    - [pyright](#pyright)
    - [Pylint compatibility](#pylint-compatibility)
  - [Explicit type annotations](#explicit-type-annotations)
    - [Client annotations](#client-annotations)
    - [Paginators annotations](#paginators-annotations)
    - [Literals](#literals)
    - [Type definitions](#type-definitions)
  - [How it works](#how-it-works)
  - [What's new](#what's-new)
    - [Implemented features](#implemented-features)
    - [Latest changes](#latest-changes)
  - [Versioning](#versioning)
  - [Thank you](#thank-you)
  - [Documentation](#documentation)
  - [Support and contributing](#support-and-contributing)

<a id="how-to-install"></a>

## How to install

<a id="generate-locally-(recommended)"></a>

### Generate locally (recommended)

You can generate type annotations for `boto3` package locally with
`mypy-boto3-builder`. Use
[uv](https://docs.astral.sh/uv/getting-started/installation/) for build
isolation.

1. Run mypy-boto3-builder in your package root directory:
   `uvx --with 'boto3==1.42.14' mypy-boto3-builder`
2. Select `boto3` AWS SDK.
3. Add `Connect` service.
4. Use provided commands to install generated packages.

<a id="vscode-extension"></a>

### VSCode extension

Add
[AWS Boto3](https://marketplace.visualstudio.com/items?itemName=Boto3typed.boto3-ide)
extension to your VSCode and run `AWS boto3: Quick Start` command.

Click `Modify` and select `boto3 common` and `Connect`.

<a id="from-pypi-with-pip"></a>

### From PyPI with pip

Install `types-boto3` for `Connect` service.

```bash
# install with boto3 type annotations
python -m pip install 'types-boto3[connect]'

# Lite version does not provide session.client/resource overloads
# it is more RAM-friendly, but requires explicit type annotations
python -m pip install 'types-boto3-lite[connect]'

# standalone installation
python -m pip install types-boto3-connect
```

<a id="how-to-uninstall"></a>

## How to uninstall

```bash
python -m pip uninstall -y types-boto3-connect
```

<a id="usage"></a>

## Usage

<a id="vscode"></a>

### VSCode

- Install
  [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- Install
  [Pylance extension](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)
- Set `Pylance` as your Python Language Server
- Install `types-boto3[connect]` in your environment:

```bash
python -m pip install 'types-boto3[connect]'
```

Both type checking and code completion should now work. No explicit type
annotations required, write your `boto3` code as usual.

<a id="pycharm"></a>

### PyCharm

> ⚠️ Due to slow PyCharm performance on `Literal` overloads (issue
> [PY-40997](https://youtrack.jetbrains.com/issue/PY-40997)), it is recommended
> to use [types-boto3-lite](https://pypi.org/project/types-boto3-lite/) until
> the issue is resolved.

> ⚠️ If you experience slow performance and high CPU usage, try to disable
> `PyCharm` type checker and use [mypy](https://github.com/python/mypy) or
> [pyright](https://github.com/microsoft/pyright) instead.

> ⚠️ To continue using `PyCharm` type checker, you can try to replace
> `types-boto3` with
> [types-boto3-lite](https://pypi.org/project/types-boto3-lite/):

```bash
pip uninstall types-boto3
pip install types-boto3-lite
```

Install `types-boto3[connect]` in your environment:

```bash
python -m pip install 'types-boto3[connect]'
```

Both type checking and code completion should now work.

<a id="emacs"></a>

### Emacs

- Install `types-boto3` with services you use in your environment:

```bash
python -m pip install 'types-boto3[connect]'
```

- Install [use-package](https://github.com/jwiegley/use-package),
  [lsp](https://github.com/emacs-lsp/lsp-mode/),
  [company](https://github.com/company-mode/company-mode) and
  [flycheck](https://github.com/flycheck/flycheck) packages
- Install [lsp-pyright](https://github.com/emacs-lsp/lsp-pyright) package

```elisp
(use-package lsp-pyright
  :ensure t
  :hook (python-mode . (lambda ()
                          (require 'lsp-pyright)
                          (lsp)))  ; or lsp-deferred
  :init (when (executable-find "python3")
          (setq lsp-pyright-python-executable-cmd "python3"))
  )
```

- Make sure emacs uses the environment where you have installed `types-boto3`

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="sublime-text"></a>

### Sublime Text

- Install `types-boto3[connect]` with services you use in your environment:

```bash
python -m pip install 'types-boto3[connect]'
```

- Install [LSP-pyright](https://github.com/sublimelsp/LSP-pyright) package

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="other-ides"></a>

### Other IDEs

Not tested, but as long as your IDE supports `mypy` or `pyright`, everything
should work.

<a id="mypy"></a>

### mypy

- Install `mypy`: `python -m pip install mypy`
- Install `types-boto3[connect]` in your environment:

```bash
python -m pip install 'types-boto3[connect]'
```

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pyright"></a>

### pyright

- Install `pyright`: `npm i -g pyright`
- Install `types-boto3[connect]` in your environment:

```bash
python -m pip install 'types-boto3[connect]'
```

Optionally, you can install `types-boto3` to `typings` directory.

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pylint-compatibility"></a>

### Pylint compatibility

It is totally safe to use `TYPE_CHECKING` flag in order to avoid
`types-boto3-connect` dependency in production. However, there is an issue in
`pylint` that it complains about undefined variables. To fix it, set all types
to `object` in non-`TYPE_CHECKING` mode.

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types_boto3_ec2 import EC2Client, EC2ServiceResource
    from types_boto3_ec2.waiters import BundleTaskCompleteWaiter
    from types_boto3_ec2.paginators import DescribeVolumesPaginator
else:
    EC2Client = object
    EC2ServiceResource = object
    BundleTaskCompleteWaiter = object
    DescribeVolumesPaginator = object

...
```

<a id="explicit-type-annotations"></a>

## Explicit type annotations

<a id="client-annotations"></a>

### Client annotations

`ConnectClient` provides annotations for `boto3.client("connect")`.

```python
from boto3.session import Session

from types_boto3_connect import ConnectClient

client: ConnectClient = Session().client("connect")

# now client usage is checked by mypy and IDE should provide code completion
```

<a id="paginators-annotations"></a>

### Paginators annotations

`types_boto3_connect.paginator` module contains type annotations for all
paginators.

```python
from boto3.session import Session

from types_boto3_connect import ConnectClient
from types_boto3_connect.paginator import (
    GetMetricDataPaginator,
    ListAgentStatusesPaginator,
    ListApprovedOriginsPaginator,
    ListAuthenticationProfilesPaginator,
    ListBotsPaginator,
    ListContactEvaluationsPaginator,
    ListContactFlowModuleAliasesPaginator,
    ListContactFlowModuleVersionsPaginator,
    ListContactFlowModulesPaginator,
    ListContactFlowVersionsPaginator,
    ListContactFlowsPaginator,
    ListContactReferencesPaginator,
    ListDataTableAttributesPaginator,
    ListDataTablePrimaryValuesPaginator,
    ListDataTableValuesPaginator,
    ListDataTablesPaginator,
    ListDefaultVocabulariesPaginator,
    ListEvaluationFormVersionsPaginator,
    ListEvaluationFormsPaginator,
    ListFlowAssociationsPaginator,
    ListHoursOfOperationOverridesPaginator,
    ListHoursOfOperationsPaginator,
    ListInstanceAttributesPaginator,
    ListInstanceStorageConfigsPaginator,
    ListInstancesPaginator,
    ListIntegrationAssociationsPaginator,
    ListLambdaFunctionsPaginator,
    ListLexBotsPaginator,
    ListPhoneNumbersPaginator,
    ListPhoneNumbersV2Paginator,
    ListPredefinedAttributesPaginator,
    ListPromptsPaginator,
    ListQueueQuickConnectsPaginator,
    ListQueuesPaginator,
    ListQuickConnectsPaginator,
    ListRoutingProfileManualAssignmentQueuesPaginator,
    ListRoutingProfileQueuesPaginator,
    ListRoutingProfilesPaginator,
    ListRulesPaginator,
    ListSecurityKeysPaginator,
    ListSecurityProfileApplicationsPaginator,
    ListSecurityProfilePermissionsPaginator,
    ListSecurityProfilesPaginator,
    ListTaskTemplatesPaginator,
    ListTrafficDistributionGroupUsersPaginator,
    ListTrafficDistributionGroupsPaginator,
    ListUseCasesPaginator,
    ListUserHierarchyGroupsPaginator,
    ListUserProficienciesPaginator,
    ListUsersPaginator,
    ListViewVersionsPaginator,
    ListViewsPaginator,
    ListWorkspacePagesPaginator,
    ListWorkspacesPaginator,
    SearchAgentStatusesPaginator,
    SearchAvailablePhoneNumbersPaginator,
    SearchContactFlowModulesPaginator,
    SearchContactFlowsPaginator,
    SearchContactsPaginator,
    SearchDataTablesPaginator,
    SearchHoursOfOperationOverridesPaginator,
    SearchHoursOfOperationsPaginator,
    SearchPredefinedAttributesPaginator,
    SearchPromptsPaginator,
    SearchQueuesPaginator,
    SearchQuickConnectsPaginator,
    SearchResourceTagsPaginator,
    SearchRoutingProfilesPaginator,
    SearchSecurityProfilesPaginator,
    SearchUserHierarchyGroupsPaginator,
    SearchUsersPaginator,
    SearchViewsPaginator,
    SearchVocabulariesPaginator,
    SearchWorkspaceAssociationsPaginator,
    SearchWorkspacesPaginator,
)

client: ConnectClient = Session().client("connect")

# Explicit type annotations are optional here
# Types should be correctly discovered by mypy and IDEs
get_metric_data_paginator: GetMetricDataPaginator = client.get_paginator("get_metric_data")
list_agent_statuses_paginator: ListAgentStatusesPaginator = client.get_paginator(
    "list_agent_statuses"
)
list_approved_origins_paginator: ListApprovedOriginsPaginator = client.get_paginator(
    "list_approved_origins"
)
list_authentication_profiles_paginator: ListAuthenticationProfilesPaginator = client.get_paginator(
    "list_authentication_profiles"
)
list_bots_paginator: ListBotsPaginator = client.get_paginator("list_bots")
list_contact_evaluations_paginator: ListContactEvaluationsPaginator = client.get_paginator(
    "list_contact_evaluations"
)
list_contact_flow_module_aliases_paginator: ListContactFlowModuleAliasesPaginator = (
    client.get_paginator("list_contact_flow_module_aliases")
)
list_contact_flow_module_versions_paginator: ListContactFlowModuleVersionsPaginator = (
    client.get_paginator("list_contact_flow_module_versions")
)
list_contact_flow_modules_paginator: ListContactFlowModulesPaginator = client.get_paginator(
    "list_contact_flow_modules"
)
list_contact_flow_versions_paginator: ListContactFlowVersionsPaginator = client.get_paginator(
    "list_contact_flow_versions"
)
list_contact_flows_paginator: ListContactFlowsPaginator = client.get_paginator("list_contact_flows")
list_contact_references_paginator: ListContactReferencesPaginator = client.get_paginator(
    "list_contact_references"
)
list_data_table_attributes_paginator: ListDataTableAttributesPaginator = client.get_paginator(
    "list_data_table_attributes"
)
list_data_table_primary_values_paginator: ListDataTablePrimaryValuesPaginator = (
    client.get_paginator("list_data_table_primary_values")
)
list_data_table_values_paginator: ListDataTableValuesPaginator = client.get_paginator(
    "list_data_table_values"
)
list_data_tables_paginator: ListDataTablesPaginator = client.get_paginator("list_data_tables")
list_default_vocabularies_paginator: ListDefaultVocabulariesPaginator = client.get_paginator(
    "list_default_vocabularies"
)
list_evaluation_form_versions_paginator: ListEvaluationFormVersionsPaginator = client.get_paginator(
    "list_evaluation_form_versions"
)
list_evaluation_forms_paginator: ListEvaluationFormsPaginator = client.get_paginator(
    "list_evaluation_forms"
)
list_flow_associations_paginator: ListFlowAssociationsPaginator = client.get_paginator(
    "list_flow_associations"
)
list_hours_of_operation_overrides_paginator: ListHoursOfOperationOverridesPaginator = (
    client.get_paginator("list_hours_of_operation_overrides")
)
list_hours_of_operations_paginator: ListHoursOfOperationsPaginator = client.get_paginator(
    "list_hours_of_operations"
)
list_instance_attributes_paginator: ListInstanceAttributesPaginator = client.get_paginator(
    "list_instance_attributes"
)
list_instance_storage_configs_paginator: ListInstanceStorageConfigsPaginator = client.get_paginator(
    "list_instance_storage_configs"
)
list_instances_paginator: ListInstancesPaginator = client.get_paginator("list_instances")
list_integration_associations_paginator: ListIntegrationAssociationsPaginator = (
    client.get_paginator("list_integration_associations")
)
list_lambda_functions_paginator: ListLambdaFunctionsPaginator = client.get_paginator(
    "list_lambda_functions"
)
list_lex_bots_paginator: ListLexBotsPaginator = client.get_paginator("list_lex_bots")
list_phone_numbers_paginator: ListPhoneNumbersPaginator = client.get_paginator("list_phone_numbers")
list_phone_numbers_v2_paginator: ListPhoneNumbersV2Paginator = client.get_paginator(
    "list_phone_numbers_v2"
)
list_predefined_attributes_paginator: ListPredefinedAttributesPaginator = client.get_paginator(
    "list_predefined_attributes"
)
list_prompts_paginator: ListPromptsPaginator = client.get_paginator("list_prompts")
list_queue_quick_connects_paginator: ListQueueQuickConnectsPaginator = client.get_paginator(
    "list_queue_quick_connects"
)
list_queues_paginator: ListQueuesPaginator = client.get_paginator("list_queues")
list_quick_connects_paginator: ListQuickConnectsPaginator = client.get_paginator(
    "list_quick_connects"
)
list_routing_profile_manual_assignment_queues_paginator: ListRoutingProfileManualAssignmentQueuesPaginator = client.get_paginator(
    "list_routing_profile_manual_assignment_queues"
)
list_routing_profile_queues_paginator: ListRoutingProfileQueuesPaginator = client.get_paginator(
    "list_routing_profile_queues"
)
list_routing_profiles_paginator: ListRoutingProfilesPaginator = client.get_paginator(
    "list_routing_profiles"
)
list_rules_paginator: ListRulesPaginator = client.get_paginator("list_rules")
list_security_keys_paginator: ListSecurityKeysPaginator = client.get_paginator("list_security_keys")
list_security_profile_applications_paginator: ListSecurityProfileApplicationsPaginator = (
    client.get_paginator("list_security_profile_applications")
)
list_security_profile_permissions_paginator: ListSecurityProfilePermissionsPaginator = (
    client.get_paginator("list_security_profile_permissions")
)
list_security_profiles_paginator: ListSecurityProfilesPaginator = client.get_paginator(
    "list_security_profiles"
)
list_task_templates_paginator: ListTaskTemplatesPaginator = client.get_paginator(
    "list_task_templates"
)
list_traffic_distribution_group_users_paginator: ListTrafficDistributionGroupUsersPaginator = (
    client.get_paginator("list_traffic_distribution_group_users")
)
list_traffic_distribution_groups_paginator: ListTrafficDistributionGroupsPaginator = (
    client.get_paginator("list_traffic_distribution_groups")
)
list_use_cases_paginator: ListUseCasesPaginator = client.get_paginator("list_use_cases")
list_user_hierarchy_groups_paginator: ListUserHierarchyGroupsPaginator = client.get_paginator(
    "list_user_hierarchy_groups"
)
list_user_proficiencies_paginator: ListUserProficienciesPaginator = client.get_paginator(
    "list_user_proficiencies"
)
list_users_paginator: ListUsersPaginator = client.get_paginator("list_users")
list_view_versions_paginator: ListViewVersionsPaginator = client.get_paginator("list_view_versions")
list_views_paginator: ListViewsPaginator = client.get_paginator("list_views")
list_workspace_pages_paginator: ListWorkspacePagesPaginator = client.get_paginator(
    "list_workspace_pages"
)
list_workspaces_paginator: ListWorkspacesPaginator = client.get_paginator("list_workspaces")
search_agent_statuses_paginator: SearchAgentStatusesPaginator = client.get_paginator(
    "search_agent_statuses"
)
search_available_phone_numbers_paginator: SearchAvailablePhoneNumbersPaginator = (
    client.get_paginator("search_available_phone_numbers")
)
search_contact_flow_modules_paginator: SearchContactFlowModulesPaginator = client.get_paginator(
    "search_contact_flow_modules"
)
search_contact_flows_paginator: SearchContactFlowsPaginator = client.get_paginator(
    "search_contact_flows"
)
search_contacts_paginator: SearchContactsPaginator = client.get_paginator("search_contacts")
search_data_tables_paginator: SearchDataTablesPaginator = client.get_paginator("search_data_tables")
search_hours_of_operation_overrides_paginator: SearchHoursOfOperationOverridesPaginator = (
    client.get_paginator("search_hours_of_operation_overrides")
)
search_hours_of_operations_paginator: SearchHoursOfOperationsPaginator = client.get_paginator(
    "search_hours_of_operations"
)
search_predefined_attributes_paginator: SearchPredefinedAttributesPaginator = client.get_paginator(
    "search_predefined_attributes"
)
search_prompts_paginator: SearchPromptsPaginator = client.get_paginator("search_prompts")
search_queues_paginator: SearchQueuesPaginator = client.get_paginator("search_queues")
search_quick_connects_paginator: SearchQuickConnectsPaginator = client.get_paginator(
    "search_quick_connects"
)
search_resource_tags_paginator: SearchResourceTagsPaginator = client.get_paginator(
    "search_resource_tags"
)
search_routing_profiles_paginator: SearchRoutingProfilesPaginator = client.get_paginator(
    "search_routing_profiles"
)
search_security_profiles_paginator: SearchSecurityProfilesPaginator = client.get_paginator(
    "search_security_profiles"
)
search_user_hierarchy_groups_paginator: SearchUserHierarchyGroupsPaginator = client.get_paginator(
    "search_user_hierarchy_groups"
)
search_users_paginator: SearchUsersPaginator = client.get_paginator("search_users")
search_views_paginator: SearchViewsPaginator = client.get_paginator("search_views")
search_vocabularies_paginator: SearchVocabulariesPaginator = client.get_paginator(
    "search_vocabularies"
)
search_workspace_associations_paginator: SearchWorkspaceAssociationsPaginator = (
    client.get_paginator("search_workspace_associations")
)
search_workspaces_paginator: SearchWorkspacesPaginator = client.get_paginator("search_workspaces")
```

<a id="literals"></a>

### Literals

`types_boto3_connect.literals` module contains literals extracted from shapes
that can be used in user code for type checking.

Full list of `Connect` Literals can be found in
[docs](https://youtype.github.io/types_boto3_docs/types_boto3_connect/literals/).

```python
from types_boto3_connect.literals import AccessTypeType


def check_value(value: AccessTypeType) -> bool: ...
```

<a id="type-definitions"></a>

### Type definitions

`types_boto3_connect.type_defs` module contains structures and shapes assembled
to typed dictionaries and unions for additional type checking.

Full list of `Connect` TypeDefs can be found in
[docs](https://youtype.github.io/types_boto3_docs/types_boto3_connect/type_defs/).

```python
# TypedDict usage example
from types_boto3_connect.type_defs import ActionSummaryTypeDef


def get_value() -> ActionSummaryTypeDef:
    return {
        "ActionType": ...,
    }
```

<a id="how-it-works"></a>

## How it works

Fully automated
[mypy-boto3-builder](https://github.com/youtype/mypy_boto3_builder) carefully
generates type annotations for each service, patiently waiting for `boto3`
updates. It delivers drop-in type annotations for you and makes sure that:

- All available `boto3` services are covered.
- Each public class and method of every `boto3` service gets valid type
  annotations extracted from `botocore` schemas.
- Type annotations include up-to-date documentation.
- Link to documentation is provided for every method.
- Code is processed by [ruff](https://docs.astral.sh/ruff/) for readability.

<a id="what's-new"></a>

## What's new

<a id="implemented-features"></a>

### Implemented features

- Fully type annotated `boto3`, `botocore`, `aiobotocore` and `aioboto3`
  libraries
- `mypy`, `pyright`, `VSCode`, `PyCharm`, `Sublime Text` and `Emacs`
  compatibility
- `Client`, `ServiceResource`, `Resource`, `Waiter` `Paginator` type
  annotations for each service
- Generated `TypeDefs` for each service
- Generated `Literals` for each service
- Auto discovery of types for `boto3.client` and `boto3.resource` calls
- Auto discovery of types for `session.client` and `session.resource` calls
- Auto discovery of types for `client.get_waiter` and `client.get_paginator`
  calls
- Auto discovery of types for `ServiceResource` and `Resource` collections
- Auto discovery of types for `aiobotocore.Session.create_client` calls

<a id="latest-changes"></a>

### Latest changes

Builder changelog can be found in
[Releases](https://github.com/youtype/mypy_boto3_builder/releases).

<a id="versioning"></a>

## Versioning

`types-boto3-connect` version is the same as related `boto3` version and
follows
[Python Packaging version specifiers](https://packaging.python.org/en/latest/specifications/version-specifiers/).

<a id="thank-you"></a>

## Thank you

- [Allie Fitter](https://github.com/alliefitter) for
  [boto3-type-annotations](https://pypi.org/project/boto3-type-annotations/),
  this package is based on top of his work
- [black](https://github.com/psf/black) developers for an awesome formatting
  tool
- [Timothy Edmund Crosley](https://github.com/timothycrosley) for
  [isort](https://github.com/PyCQA/isort) and how flexible it is
- [mypy](https://github.com/python/mypy) developers for doing all dirty work
  for us
- [pyright](https://github.com/microsoft/pyright) team for the new era of typed
  Python

<a id="documentation"></a>

## Documentation

All services type annotations can be found in
[boto3 docs](https://youtype.github.io/types_boto3_docs/types_boto3_connect/)

<a id="support-and-contributing"></a>

## Support and contributing

This package is auto-generated. Please reports any bugs or request new features
in [mypy-boto3-builder](https://github.com/youtype/mypy_boto3_builder/issues/)
repository.
