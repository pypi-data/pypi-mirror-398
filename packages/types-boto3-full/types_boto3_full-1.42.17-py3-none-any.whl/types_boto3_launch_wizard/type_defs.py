"""
Type annotations for launch-wizard service type definitions.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_launch_wizard/type_defs/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from types_boto3_launch_wizard.type_defs import CreateDeploymentInputTypeDef

    data: CreateDeploymentInputTypeDef = ...
    ```
"""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from datetime import datetime

from .literals import (
    DeploymentFilterKeyType,
    DeploymentStatusType,
    EventStatusType,
    WorkloadDeploymentPatternStatusType,
    WorkloadStatusType,
)

if sys.version_info >= (3, 12):
    from typing import NotRequired, TypedDict
else:
    from typing_extensions import NotRequired, TypedDict


__all__ = (
    "CreateDeploymentInputTypeDef",
    "CreateDeploymentOutputTypeDef",
    "DeleteDeploymentInputTypeDef",
    "DeleteDeploymentOutputTypeDef",
    "DeploymentConditionalFieldTypeDef",
    "DeploymentDataSummaryTypeDef",
    "DeploymentDataTypeDef",
    "DeploymentEventDataSummaryTypeDef",
    "DeploymentFilterTypeDef",
    "DeploymentSpecificationsFieldTypeDef",
    "GetDeploymentInputTypeDef",
    "GetDeploymentOutputTypeDef",
    "GetWorkloadDeploymentPatternInputTypeDef",
    "GetWorkloadDeploymentPatternOutputTypeDef",
    "GetWorkloadInputTypeDef",
    "GetWorkloadOutputTypeDef",
    "ListDeploymentEventsInputPaginateTypeDef",
    "ListDeploymentEventsInputTypeDef",
    "ListDeploymentEventsOutputTypeDef",
    "ListDeploymentsInputPaginateTypeDef",
    "ListDeploymentsInputTypeDef",
    "ListDeploymentsOutputTypeDef",
    "ListTagsForResourceInputTypeDef",
    "ListTagsForResourceOutputTypeDef",
    "ListWorkloadDeploymentPatternsInputPaginateTypeDef",
    "ListWorkloadDeploymentPatternsInputTypeDef",
    "ListWorkloadDeploymentPatternsOutputTypeDef",
    "ListWorkloadsInputPaginateTypeDef",
    "ListWorkloadsInputTypeDef",
    "ListWorkloadsOutputTypeDef",
    "PaginatorConfigTypeDef",
    "ResponseMetadataTypeDef",
    "TagResourceInputTypeDef",
    "UntagResourceInputTypeDef",
    "WorkloadDataSummaryTypeDef",
    "WorkloadDataTypeDef",
    "WorkloadDeploymentPatternDataSummaryTypeDef",
    "WorkloadDeploymentPatternDataTypeDef",
)


class CreateDeploymentInputTypeDef(TypedDict):
    deploymentPatternName: str
    name: str
    specifications: Mapping[str, str]
    workloadName: str
    dryRun: NotRequired[bool]
    tags: NotRequired[Mapping[str, str]]


class ResponseMetadataTypeDef(TypedDict):
    RequestId: str
    HTTPStatusCode: int
    HTTPHeaders: dict[str, str]
    RetryAttempts: int
    HostId: NotRequired[str]


class DeleteDeploymentInputTypeDef(TypedDict):
    deploymentId: str


class DeploymentConditionalFieldTypeDef(TypedDict):
    comparator: NotRequired[str]
    name: NotRequired[str]
    value: NotRequired[str]


DeploymentDataSummaryTypeDef = TypedDict(
    "DeploymentDataSummaryTypeDef",
    {
        "createdAt": NotRequired[datetime],
        "id": NotRequired[str],
        "name": NotRequired[str],
        "patternName": NotRequired[str],
        "status": NotRequired[DeploymentStatusType],
        "workloadName": NotRequired[str],
    },
)
DeploymentDataTypeDef = TypedDict(
    "DeploymentDataTypeDef",
    {
        "createdAt": NotRequired[datetime],
        "deletedAt": NotRequired[datetime],
        "deploymentArn": NotRequired[str],
        "id": NotRequired[str],
        "name": NotRequired[str],
        "patternName": NotRequired[str],
        "resourceGroup": NotRequired[str],
        "specifications": NotRequired[dict[str, str]],
        "status": NotRequired[DeploymentStatusType],
        "tags": NotRequired[dict[str, str]],
        "workloadName": NotRequired[str],
    },
)


class DeploymentEventDataSummaryTypeDef(TypedDict):
    description: NotRequired[str]
    name: NotRequired[str]
    status: NotRequired[EventStatusType]
    statusReason: NotRequired[str]
    timestamp: NotRequired[datetime]


class DeploymentFilterTypeDef(TypedDict):
    name: NotRequired[DeploymentFilterKeyType]
    values: NotRequired[Sequence[str]]


class GetDeploymentInputTypeDef(TypedDict):
    deploymentId: str


class GetWorkloadDeploymentPatternInputTypeDef(TypedDict):
    deploymentPatternName: str
    workloadName: str


class GetWorkloadInputTypeDef(TypedDict):
    workloadName: str


class WorkloadDataTypeDef(TypedDict):
    description: NotRequired[str]
    displayName: NotRequired[str]
    documentationUrl: NotRequired[str]
    iconUrl: NotRequired[str]
    status: NotRequired[WorkloadStatusType]
    statusMessage: NotRequired[str]
    workloadName: NotRequired[str]


class PaginatorConfigTypeDef(TypedDict):
    MaxItems: NotRequired[int]
    PageSize: NotRequired[int]
    StartingToken: NotRequired[str]


class ListDeploymentEventsInputTypeDef(TypedDict):
    deploymentId: str
    maxResults: NotRequired[int]
    nextToken: NotRequired[str]


class ListTagsForResourceInputTypeDef(TypedDict):
    resourceArn: str


class ListWorkloadDeploymentPatternsInputTypeDef(TypedDict):
    workloadName: str
    maxResults: NotRequired[int]
    nextToken: NotRequired[str]


class WorkloadDeploymentPatternDataSummaryTypeDef(TypedDict):
    deploymentPatternName: NotRequired[str]
    description: NotRequired[str]
    displayName: NotRequired[str]
    status: NotRequired[WorkloadDeploymentPatternStatusType]
    statusMessage: NotRequired[str]
    workloadName: NotRequired[str]
    workloadVersionName: NotRequired[str]


class ListWorkloadsInputTypeDef(TypedDict):
    maxResults: NotRequired[int]
    nextToken: NotRequired[str]


class WorkloadDataSummaryTypeDef(TypedDict):
    displayName: NotRequired[str]
    workloadName: NotRequired[str]


class TagResourceInputTypeDef(TypedDict):
    resourceArn: str
    tags: Mapping[str, str]


class UntagResourceInputTypeDef(TypedDict):
    resourceArn: str
    tagKeys: Sequence[str]


class CreateDeploymentOutputTypeDef(TypedDict):
    deploymentId: str
    ResponseMetadata: ResponseMetadataTypeDef


class DeleteDeploymentOutputTypeDef(TypedDict):
    status: DeploymentStatusType
    statusReason: str
    ResponseMetadata: ResponseMetadataTypeDef


class ListTagsForResourceOutputTypeDef(TypedDict):
    tags: dict[str, str]
    ResponseMetadata: ResponseMetadataTypeDef


class DeploymentSpecificationsFieldTypeDef(TypedDict):
    allowedValues: NotRequired[list[str]]
    conditionals: NotRequired[list[DeploymentConditionalFieldTypeDef]]
    description: NotRequired[str]
    name: NotRequired[str]
    required: NotRequired[str]


class ListDeploymentsOutputTypeDef(TypedDict):
    deployments: list[DeploymentDataSummaryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]


class GetDeploymentOutputTypeDef(TypedDict):
    deployment: DeploymentDataTypeDef
    ResponseMetadata: ResponseMetadataTypeDef


class ListDeploymentEventsOutputTypeDef(TypedDict):
    deploymentEvents: list[DeploymentEventDataSummaryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]


class ListDeploymentsInputTypeDef(TypedDict):
    filters: NotRequired[Sequence[DeploymentFilterTypeDef]]
    maxResults: NotRequired[int]
    nextToken: NotRequired[str]


class GetWorkloadOutputTypeDef(TypedDict):
    workload: WorkloadDataTypeDef
    ResponseMetadata: ResponseMetadataTypeDef


class ListDeploymentEventsInputPaginateTypeDef(TypedDict):
    deploymentId: str
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]


class ListDeploymentsInputPaginateTypeDef(TypedDict):
    filters: NotRequired[Sequence[DeploymentFilterTypeDef]]
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]


class ListWorkloadDeploymentPatternsInputPaginateTypeDef(TypedDict):
    workloadName: str
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]


class ListWorkloadsInputPaginateTypeDef(TypedDict):
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]


class ListWorkloadDeploymentPatternsOutputTypeDef(TypedDict):
    workloadDeploymentPatterns: list[WorkloadDeploymentPatternDataSummaryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]


class ListWorkloadsOutputTypeDef(TypedDict):
    workloads: list[WorkloadDataSummaryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]


class WorkloadDeploymentPatternDataTypeDef(TypedDict):
    deploymentPatternName: NotRequired[str]
    description: NotRequired[str]
    displayName: NotRequired[str]
    specifications: NotRequired[list[DeploymentSpecificationsFieldTypeDef]]
    status: NotRequired[WorkloadDeploymentPatternStatusType]
    statusMessage: NotRequired[str]
    workloadName: NotRequired[str]
    workloadVersionName: NotRequired[str]


class GetWorkloadDeploymentPatternOutputTypeDef(TypedDict):
    workloadDeploymentPattern: WorkloadDeploymentPatternDataTypeDef
    ResponseMetadata: ResponseMetadataTypeDef
