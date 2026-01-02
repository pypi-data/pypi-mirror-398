from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EdgeDirection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OUTGOING: _ClassVar[EdgeDirection]
    INCOMING: _ClassVar[EdgeDirection]
    BOTH: _ClassVar[EdgeDirection]
OUTGOING: EdgeDirection
INCOMING: EdgeDirection
BOTH: EdgeDirection

class Kref(_message.Message):
    __slots__ = ("uri",)
    URI_FIELD_NUMBER: _ClassVar[int]
    uri: str
    def __init__(self, uri: _Optional[str] = ...) -> None: ...

class Edge(_message.Message):
    __slots__ = ("source_kref", "target_kref", "edge_type", "metadata", "created_at", "author", "username")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    SOURCE_KREF_FIELD_NUMBER: _ClassVar[int]
    TARGET_KREF_FIELD_NUMBER: _ClassVar[int]
    EDGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    source_kref: Kref
    target_kref: Kref
    edge_type: str
    metadata: _containers.ScalarMap[str, str]
    created_at: str
    author: str
    username: str
    def __init__(self, source_kref: _Optional[_Union[Kref, _Mapping]] = ..., target_kref: _Optional[_Union[Kref, _Mapping]] = ..., edge_type: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., created_at: _Optional[str] = ..., author: _Optional[str] = ..., username: _Optional[str] = ...) -> None: ...

class StatusResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class PaginationRequest(_message.Message):
    __slots__ = ("page_size", "cursor")
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    page_size: int
    cursor: str
    def __init__(self, page_size: _Optional[int] = ..., cursor: _Optional[str] = ...) -> None: ...

class PaginationResponse(_message.Message):
    __slots__ = ("next_cursor", "has_more", "total_count")
    NEXT_CURSOR_FIELD_NUMBER: _ClassVar[int]
    HAS_MORE_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    next_cursor: str
    has_more: bool
    total_count: int
    def __init__(self, next_cursor: _Optional[str] = ..., has_more: bool = ..., total_count: _Optional[int] = ...) -> None: ...

class KrefRequest(_message.Message):
    __slots__ = ("kref",)
    KREF_FIELD_NUMBER: _ClassVar[int]
    kref: Kref
    def __init__(self, kref: _Optional[_Union[Kref, _Mapping]] = ...) -> None: ...

class ResolveKrefRequest(_message.Message):
    __slots__ = ("kref", "tag", "time")
    KREF_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    kref: str
    tag: str
    time: str
    def __init__(self, kref: _Optional[str] = ..., tag: _Optional[str] = ..., time: _Optional[str] = ...) -> None: ...

class ResolveLocationRequest(_message.Message):
    __slots__ = ("kref", "tag", "time")
    KREF_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    kref: str
    tag: str
    time: str
    def __init__(self, kref: _Optional[str] = ..., tag: _Optional[str] = ..., time: _Optional[str] = ...) -> None: ...

class ResolveLocationResponse(_message.Message):
    __slots__ = ("location", "resolved_kref", "artifact_name")
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    RESOLVED_KREF_FIELD_NUMBER: _ClassVar[int]
    ARTIFACT_NAME_FIELD_NUMBER: _ClassVar[int]
    location: str
    resolved_kref: Kref
    artifact_name: str
    def __init__(self, location: _Optional[str] = ..., resolved_kref: _Optional[_Union[Kref, _Mapping]] = ..., artifact_name: _Optional[str] = ...) -> None: ...

class CreateSpaceRequest(_message.Message):
    __slots__ = ("parent_path", "space_name", "exists_error")
    PARENT_PATH_FIELD_NUMBER: _ClassVar[int]
    SPACE_NAME_FIELD_NUMBER: _ClassVar[int]
    EXISTS_ERROR_FIELD_NUMBER: _ClassVar[int]
    parent_path: str
    space_name: str
    exists_error: bool
    def __init__(self, parent_path: _Optional[str] = ..., space_name: _Optional[str] = ..., exists_error: bool = ...) -> None: ...

class SpaceResponse(_message.Message):
    __slots__ = ("path", "created_at", "modified_at", "author", "metadata", "username", "name", "type")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PATH_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    MODIFIED_AT_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    path: str
    created_at: str
    modified_at: str
    author: str
    metadata: _containers.ScalarMap[str, str]
    username: str
    name: str
    type: str
    def __init__(self, path: _Optional[str] = ..., created_at: _Optional[str] = ..., modified_at: _Optional[str] = ..., author: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., username: _Optional[str] = ..., name: _Optional[str] = ..., type: _Optional[str] = ...) -> None: ...

class GetSpaceRequest(_message.Message):
    __slots__ = ("path_or_kref",)
    PATH_OR_KREF_FIELD_NUMBER: _ClassVar[int]
    path_or_kref: str
    def __init__(self, path_or_kref: _Optional[str] = ...) -> None: ...

class DeleteSpaceRequest(_message.Message):
    __slots__ = ("path", "force")
    PATH_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    path: str
    force: bool
    def __init__(self, path: _Optional[str] = ..., force: bool = ...) -> None: ...

class GetChildSpacesRequest(_message.Message):
    __slots__ = ("parent_path", "recursive", "pagination")
    PARENT_PATH_FIELD_NUMBER: _ClassVar[int]
    RECURSIVE_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    parent_path: str
    recursive: bool
    pagination: PaginationRequest
    def __init__(self, parent_path: _Optional[str] = ..., recursive: bool = ..., pagination: _Optional[_Union[PaginationRequest, _Mapping]] = ...) -> None: ...

class GetChildSpacesResponse(_message.Message):
    __slots__ = ("spaces", "pagination")
    SPACES_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    spaces: _containers.RepeatedCompositeFieldContainer[SpaceResponse]
    pagination: PaginationResponse
    def __init__(self, spaces: _Optional[_Iterable[_Union[SpaceResponse, _Mapping]]] = ..., pagination: _Optional[_Union[PaginationResponse, _Mapping]] = ...) -> None: ...

class CreateItemRequest(_message.Message):
    __slots__ = ("parent_path", "item_name", "kind", "exists_error")
    PARENT_PATH_FIELD_NUMBER: _ClassVar[int]
    ITEM_NAME_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    EXISTS_ERROR_FIELD_NUMBER: _ClassVar[int]
    parent_path: str
    item_name: str
    kind: str
    exists_error: bool
    def __init__(self, parent_path: _Optional[str] = ..., item_name: _Optional[str] = ..., kind: _Optional[str] = ..., exists_error: bool = ...) -> None: ...

class GetItemRequest(_message.Message):
    __slots__ = ("parent_path", "item_name", "kind")
    PARENT_PATH_FIELD_NUMBER: _ClassVar[int]
    ITEM_NAME_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    parent_path: str
    item_name: str
    kind: str
    def __init__(self, parent_path: _Optional[str] = ..., item_name: _Optional[str] = ..., kind: _Optional[str] = ...) -> None: ...

class ItemResponse(_message.Message):
    __slots__ = ("kref", "name", "item_name", "kind", "created_at", "modified_at", "author", "metadata", "deprecated", "username")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    KREF_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ITEM_NAME_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    MODIFIED_AT_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    DEPRECATED_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    kref: Kref
    name: str
    item_name: str
    kind: str
    created_at: str
    modified_at: str
    author: str
    metadata: _containers.ScalarMap[str, str]
    deprecated: bool
    username: str
    def __init__(self, kref: _Optional[_Union[Kref, _Mapping]] = ..., name: _Optional[str] = ..., item_name: _Optional[str] = ..., kind: _Optional[str] = ..., created_at: _Optional[str] = ..., modified_at: _Optional[str] = ..., author: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., deprecated: bool = ..., username: _Optional[str] = ...) -> None: ...

class DeleteItemRequest(_message.Message):
    __slots__ = ("kref", "force")
    KREF_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    kref: Kref
    force: bool
    def __init__(self, kref: _Optional[_Union[Kref, _Mapping]] = ..., force: bool = ...) -> None: ...

class GetItemsRequest(_message.Message):
    __slots__ = ("parent_path", "item_name_filter", "kind_filter", "pagination", "include_deprecated")
    PARENT_PATH_FIELD_NUMBER: _ClassVar[int]
    ITEM_NAME_FILTER_FIELD_NUMBER: _ClassVar[int]
    KIND_FILTER_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_DEPRECATED_FIELD_NUMBER: _ClassVar[int]
    parent_path: str
    item_name_filter: str
    kind_filter: str
    pagination: PaginationRequest
    include_deprecated: bool
    def __init__(self, parent_path: _Optional[str] = ..., item_name_filter: _Optional[str] = ..., kind_filter: _Optional[str] = ..., pagination: _Optional[_Union[PaginationRequest, _Mapping]] = ..., include_deprecated: bool = ...) -> None: ...

class GetItemsResponse(_message.Message):
    __slots__ = ("items", "pagination")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[ItemResponse]
    pagination: PaginationResponse
    def __init__(self, items: _Optional[_Iterable[_Union[ItemResponse, _Mapping]]] = ..., pagination: _Optional[_Union[PaginationResponse, _Mapping]] = ...) -> None: ...

class ItemSearchRequest(_message.Message):
    __slots__ = ("context_filter", "item_name_filter", "kind_filter", "pagination", "include_deprecated")
    CONTEXT_FILTER_FIELD_NUMBER: _ClassVar[int]
    ITEM_NAME_FILTER_FIELD_NUMBER: _ClassVar[int]
    KIND_FILTER_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_DEPRECATED_FIELD_NUMBER: _ClassVar[int]
    context_filter: str
    item_name_filter: str
    kind_filter: str
    pagination: PaginationRequest
    include_deprecated: bool
    def __init__(self, context_filter: _Optional[str] = ..., item_name_filter: _Optional[str] = ..., kind_filter: _Optional[str] = ..., pagination: _Optional[_Union[PaginationRequest, _Mapping]] = ..., include_deprecated: bool = ...) -> None: ...

class CreateRevisionRequest(_message.Message):
    __slots__ = ("item_kref", "metadata", "number", "exists_error")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ITEM_KREF_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    NUMBER_FIELD_NUMBER: _ClassVar[int]
    EXISTS_ERROR_FIELD_NUMBER: _ClassVar[int]
    item_kref: Kref
    metadata: _containers.ScalarMap[str, str]
    number: int
    exists_error: bool
    def __init__(self, item_kref: _Optional[_Union[Kref, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ..., number: _Optional[int] = ..., exists_error: bool = ...) -> None: ...

class RevisionResponse(_message.Message):
    __slots__ = ("kref", "item_kref", "number", "tags", "metadata", "created_at", "modified_at", "author", "deprecated", "published", "latest", "username", "default_artifact", "name")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    KREF_FIELD_NUMBER: _ClassVar[int]
    ITEM_KREF_FIELD_NUMBER: _ClassVar[int]
    NUMBER_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    MODIFIED_AT_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    DEPRECATED_FIELD_NUMBER: _ClassVar[int]
    PUBLISHED_FIELD_NUMBER: _ClassVar[int]
    LATEST_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    kref: Kref
    item_kref: Kref
    number: int
    tags: _containers.RepeatedScalarFieldContainer[str]
    metadata: _containers.ScalarMap[str, str]
    created_at: str
    modified_at: str
    author: str
    deprecated: bool
    published: bool
    latest: bool
    username: str
    default_artifact: str
    name: str
    def __init__(self, kref: _Optional[_Union[Kref, _Mapping]] = ..., item_kref: _Optional[_Union[Kref, _Mapping]] = ..., number: _Optional[int] = ..., tags: _Optional[_Iterable[str]] = ..., metadata: _Optional[_Mapping[str, str]] = ..., created_at: _Optional[str] = ..., modified_at: _Optional[str] = ..., author: _Optional[str] = ..., deprecated: bool = ..., published: bool = ..., latest: bool = ..., username: _Optional[str] = ..., default_artifact: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...

class DeleteRevisionRequest(_message.Message):
    __slots__ = ("kref", "force")
    KREF_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    kref: Kref
    force: bool
    def __init__(self, kref: _Optional[_Union[Kref, _Mapping]] = ..., force: bool = ...) -> None: ...

class GetRevisionsRequest(_message.Message):
    __slots__ = ("item_kref", "pagination")
    ITEM_KREF_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    item_kref: Kref
    pagination: PaginationRequest
    def __init__(self, item_kref: _Optional[_Union[Kref, _Mapping]] = ..., pagination: _Optional[_Union[PaginationRequest, _Mapping]] = ...) -> None: ...

class GetRevisionsResponse(_message.Message):
    __slots__ = ("revisions", "pagination")
    REVISIONS_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    revisions: _containers.RepeatedCompositeFieldContainer[RevisionResponse]
    pagination: PaginationResponse
    def __init__(self, revisions: _Optional[_Iterable[_Union[RevisionResponse, _Mapping]]] = ..., pagination: _Optional[_Union[PaginationResponse, _Mapping]] = ...) -> None: ...

class CreateArtifactRequest(_message.Message):
    __slots__ = ("revision_kref", "name", "location", "exists_error", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    REVISION_KREF_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    EXISTS_ERROR_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    revision_kref: Kref
    name: str
    location: str
    exists_error: bool
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, revision_kref: _Optional[_Union[Kref, _Mapping]] = ..., name: _Optional[str] = ..., location: _Optional[str] = ..., exists_error: bool = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ArtifactResponse(_message.Message):
    __slots__ = ("kref", "location", "revision_kref", "item_kref", "created_at", "modified_at", "author", "metadata", "deprecated", "username", "name")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    KREF_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    REVISION_KREF_FIELD_NUMBER: _ClassVar[int]
    ITEM_KREF_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    MODIFIED_AT_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    DEPRECATED_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    kref: Kref
    location: str
    revision_kref: Kref
    item_kref: Kref
    created_at: str
    modified_at: str
    author: str
    metadata: _containers.ScalarMap[str, str]
    deprecated: bool
    username: str
    name: str
    def __init__(self, kref: _Optional[_Union[Kref, _Mapping]] = ..., location: _Optional[str] = ..., revision_kref: _Optional[_Union[Kref, _Mapping]] = ..., item_kref: _Optional[_Union[Kref, _Mapping]] = ..., created_at: _Optional[str] = ..., modified_at: _Optional[str] = ..., author: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., deprecated: bool = ..., username: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...

class GetArtifactRequest(_message.Message):
    __slots__ = ("revision_kref", "name")
    REVISION_KREF_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    revision_kref: Kref
    name: str
    def __init__(self, revision_kref: _Optional[_Union[Kref, _Mapping]] = ..., name: _Optional[str] = ...) -> None: ...

class GetArtifactsRequest(_message.Message):
    __slots__ = ("revision_kref",)
    REVISION_KREF_FIELD_NUMBER: _ClassVar[int]
    revision_kref: Kref
    def __init__(self, revision_kref: _Optional[_Union[Kref, _Mapping]] = ...) -> None: ...

class GetArtifactsResponse(_message.Message):
    __slots__ = ("artifacts",)
    ARTIFACTS_FIELD_NUMBER: _ClassVar[int]
    artifacts: _containers.RepeatedCompositeFieldContainer[ArtifactResponse]
    def __init__(self, artifacts: _Optional[_Iterable[_Union[ArtifactResponse, _Mapping]]] = ...) -> None: ...

class DeleteArtifactRequest(_message.Message):
    __slots__ = ("kref", "force")
    KREF_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    kref: Kref
    force: bool
    def __init__(self, kref: _Optional[_Union[Kref, _Mapping]] = ..., force: bool = ...) -> None: ...

class GetArtifactsByLocationRequest(_message.Message):
    __slots__ = ("location",)
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    location: str
    def __init__(self, location: _Optional[str] = ...) -> None: ...

class GetArtifactsByLocationResponse(_message.Message):
    __slots__ = ("artifacts",)
    ARTIFACTS_FIELD_NUMBER: _ClassVar[int]
    artifacts: _containers.RepeatedCompositeFieldContainer[ArtifactResponse]
    def __init__(self, artifacts: _Optional[_Iterable[_Union[ArtifactResponse, _Mapping]]] = ...) -> None: ...

class TagRevisionRequest(_message.Message):
    __slots__ = ("kref", "tag")
    KREF_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    kref: Kref
    tag: str
    def __init__(self, kref: _Optional[_Union[Kref, _Mapping]] = ..., tag: _Optional[str] = ...) -> None: ...

class UnTagRevisionRequest(_message.Message):
    __slots__ = ("kref", "tag")
    KREF_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    kref: Kref
    tag: str
    def __init__(self, kref: _Optional[_Union[Kref, _Mapping]] = ..., tag: _Optional[str] = ...) -> None: ...

class HasTagRequest(_message.Message):
    __slots__ = ("kref", "tag")
    KREF_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    kref: Kref
    tag: str
    def __init__(self, kref: _Optional[_Union[Kref, _Mapping]] = ..., tag: _Optional[str] = ...) -> None: ...

class HasTagResponse(_message.Message):
    __slots__ = ("has_tag",)
    HAS_TAG_FIELD_NUMBER: _ClassVar[int]
    has_tag: bool
    def __init__(self, has_tag: bool = ...) -> None: ...

class WasTaggedRequest(_message.Message):
    __slots__ = ("kref", "tag")
    KREF_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    kref: Kref
    tag: str
    def __init__(self, kref: _Optional[_Union[Kref, _Mapping]] = ..., tag: _Optional[str] = ...) -> None: ...

class WasTaggedResponse(_message.Message):
    __slots__ = ("was_tagged",)
    WAS_TAGGED_FIELD_NUMBER: _ClassVar[int]
    was_tagged: bool
    def __init__(self, was_tagged: bool = ...) -> None: ...

class SetDefaultArtifactRequest(_message.Message):
    __slots__ = ("revision_kref", "artifact_name")
    REVISION_KREF_FIELD_NUMBER: _ClassVar[int]
    ARTIFACT_NAME_FIELD_NUMBER: _ClassVar[int]
    revision_kref: Kref
    artifact_name: str
    def __init__(self, revision_kref: _Optional[_Union[Kref, _Mapping]] = ..., artifact_name: _Optional[str] = ...) -> None: ...

class CreateEdgeRequest(_message.Message):
    __slots__ = ("source_revision_kref", "target_revision_kref", "edge_type", "metadata", "exists_error")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    SOURCE_REVISION_KREF_FIELD_NUMBER: _ClassVar[int]
    TARGET_REVISION_KREF_FIELD_NUMBER: _ClassVar[int]
    EDGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    EXISTS_ERROR_FIELD_NUMBER: _ClassVar[int]
    source_revision_kref: Kref
    target_revision_kref: Kref
    edge_type: str
    metadata: _containers.ScalarMap[str, str]
    exists_error: bool
    def __init__(self, source_revision_kref: _Optional[_Union[Kref, _Mapping]] = ..., target_revision_kref: _Optional[_Union[Kref, _Mapping]] = ..., edge_type: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., exists_error: bool = ...) -> None: ...

class UpdateMetadataRequest(_message.Message):
    __slots__ = ("kref", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    KREF_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    kref: Kref
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, kref: _Optional[_Union[Kref, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class SetAttributeRequest(_message.Message):
    __slots__ = ("kref", "key", "value")
    KREF_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    kref: Kref
    key: str
    value: str
    def __init__(self, kref: _Optional[_Union[Kref, _Mapping]] = ..., key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class GetAttributeRequest(_message.Message):
    __slots__ = ("kref", "key")
    KREF_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    kref: Kref
    key: str
    def __init__(self, kref: _Optional[_Union[Kref, _Mapping]] = ..., key: _Optional[str] = ...) -> None: ...

class GetAttributeResponse(_message.Message):
    __slots__ = ("key", "value", "exists")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    EXISTS_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: str
    exists: bool
    def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ..., exists: bool = ...) -> None: ...

class DeleteAttributeRequest(_message.Message):
    __slots__ = ("kref", "key")
    KREF_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    kref: Kref
    key: str
    def __init__(self, kref: _Optional[_Union[Kref, _Mapping]] = ..., key: _Optional[str] = ...) -> None: ...

class PeekNextRevisionRequest(_message.Message):
    __slots__ = ("item_kref",)
    ITEM_KREF_FIELD_NUMBER: _ClassVar[int]
    item_kref: Kref
    def __init__(self, item_kref: _Optional[_Union[Kref, _Mapping]] = ...) -> None: ...

class PeekNextRevisionResponse(_message.Message):
    __slots__ = ("number",)
    NUMBER_FIELD_NUMBER: _ClassVar[int]
    number: int
    def __init__(self, number: _Optional[int] = ...) -> None: ...

class GetEdgesRequest(_message.Message):
    __slots__ = ("kref", "edge_type_filter", "direction", "pagination")
    KREF_FIELD_NUMBER: _ClassVar[int]
    EDGE_TYPE_FILTER_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    kref: Kref
    edge_type_filter: str
    direction: EdgeDirection
    pagination: PaginationRequest
    def __init__(self, kref: _Optional[_Union[Kref, _Mapping]] = ..., edge_type_filter: _Optional[str] = ..., direction: _Optional[_Union[EdgeDirection, str]] = ..., pagination: _Optional[_Union[PaginationRequest, _Mapping]] = ...) -> None: ...

class GetEdgesResponse(_message.Message):
    __slots__ = ("edges", "revision_krefs", "pagination")
    EDGES_FIELD_NUMBER: _ClassVar[int]
    REVISION_KREFS_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    edges: _containers.RepeatedCompositeFieldContainer[Edge]
    revision_krefs: _containers.RepeatedCompositeFieldContainer[Kref]
    pagination: PaginationResponse
    def __init__(self, edges: _Optional[_Iterable[_Union[Edge, _Mapping]]] = ..., revision_krefs: _Optional[_Iterable[_Union[Kref, _Mapping]]] = ..., pagination: _Optional[_Union[PaginationResponse, _Mapping]] = ...) -> None: ...

class DeleteEdgeRequest(_message.Message):
    __slots__ = ("source_kref", "target_kref", "edge_type")
    SOURCE_KREF_FIELD_NUMBER: _ClassVar[int]
    TARGET_KREF_FIELD_NUMBER: _ClassVar[int]
    EDGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    source_kref: Kref
    target_kref: Kref
    edge_type: str
    def __init__(self, source_kref: _Optional[_Union[Kref, _Mapping]] = ..., target_kref: _Optional[_Union[Kref, _Mapping]] = ..., edge_type: _Optional[str] = ...) -> None: ...

class PathStep(_message.Message):
    __slots__ = ("revision_kref", "edge_type", "depth")
    REVISION_KREF_FIELD_NUMBER: _ClassVar[int]
    EDGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    DEPTH_FIELD_NUMBER: _ClassVar[int]
    revision_kref: Kref
    edge_type: str
    depth: int
    def __init__(self, revision_kref: _Optional[_Union[Kref, _Mapping]] = ..., edge_type: _Optional[str] = ..., depth: _Optional[int] = ...) -> None: ...

class RevisionPath(_message.Message):
    __slots__ = ("steps", "total_depth")
    STEPS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_DEPTH_FIELD_NUMBER: _ClassVar[int]
    steps: _containers.RepeatedCompositeFieldContainer[PathStep]
    total_depth: int
    def __init__(self, steps: _Optional[_Iterable[_Union[PathStep, _Mapping]]] = ..., total_depth: _Optional[int] = ...) -> None: ...

class TraverseEdgesRequest(_message.Message):
    __slots__ = ("origin_kref", "direction", "edge_type_filter", "max_depth", "limit", "include_path")
    ORIGIN_KREF_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    EDGE_TYPE_FILTER_FIELD_NUMBER: _ClassVar[int]
    MAX_DEPTH_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_PATH_FIELD_NUMBER: _ClassVar[int]
    origin_kref: Kref
    direction: EdgeDirection
    edge_type_filter: _containers.RepeatedScalarFieldContainer[str]
    max_depth: int
    limit: int
    include_path: bool
    def __init__(self, origin_kref: _Optional[_Union[Kref, _Mapping]] = ..., direction: _Optional[_Union[EdgeDirection, str]] = ..., edge_type_filter: _Optional[_Iterable[str]] = ..., max_depth: _Optional[int] = ..., limit: _Optional[int] = ..., include_path: bool = ...) -> None: ...

class TraverseEdgesResponse(_message.Message):
    __slots__ = ("paths", "revision_krefs", "edges", "total_count", "truncated")
    PATHS_FIELD_NUMBER: _ClassVar[int]
    REVISION_KREFS_FIELD_NUMBER: _ClassVar[int]
    EDGES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    paths: _containers.RepeatedCompositeFieldContainer[RevisionPath]
    revision_krefs: _containers.RepeatedCompositeFieldContainer[Kref]
    edges: _containers.RepeatedCompositeFieldContainer[Edge]
    total_count: int
    truncated: bool
    def __init__(self, paths: _Optional[_Iterable[_Union[RevisionPath, _Mapping]]] = ..., revision_krefs: _Optional[_Iterable[_Union[Kref, _Mapping]]] = ..., edges: _Optional[_Iterable[_Union[Edge, _Mapping]]] = ..., total_count: _Optional[int] = ..., truncated: bool = ...) -> None: ...

class ShortestPathRequest(_message.Message):
    __slots__ = ("source_kref", "target_kref", "edge_type_filter", "max_depth", "all_shortest")
    SOURCE_KREF_FIELD_NUMBER: _ClassVar[int]
    TARGET_KREF_FIELD_NUMBER: _ClassVar[int]
    EDGE_TYPE_FILTER_FIELD_NUMBER: _ClassVar[int]
    MAX_DEPTH_FIELD_NUMBER: _ClassVar[int]
    ALL_SHORTEST_FIELD_NUMBER: _ClassVar[int]
    source_kref: Kref
    target_kref: Kref
    edge_type_filter: _containers.RepeatedScalarFieldContainer[str]
    max_depth: int
    all_shortest: bool
    def __init__(self, source_kref: _Optional[_Union[Kref, _Mapping]] = ..., target_kref: _Optional[_Union[Kref, _Mapping]] = ..., edge_type_filter: _Optional[_Iterable[str]] = ..., max_depth: _Optional[int] = ..., all_shortest: bool = ...) -> None: ...

class ShortestPathResponse(_message.Message):
    __slots__ = ("paths", "path_exists", "path_length")
    PATHS_FIELD_NUMBER: _ClassVar[int]
    PATH_EXISTS_FIELD_NUMBER: _ClassVar[int]
    PATH_LENGTH_FIELD_NUMBER: _ClassVar[int]
    paths: _containers.RepeatedCompositeFieldContainer[RevisionPath]
    path_exists: bool
    path_length: int
    def __init__(self, paths: _Optional[_Iterable[_Union[RevisionPath, _Mapping]]] = ..., path_exists: bool = ..., path_length: _Optional[int] = ...) -> None: ...

class ImpactAnalysisRequest(_message.Message):
    __slots__ = ("revision_kref", "edge_type_filter", "max_depth", "limit")
    REVISION_KREF_FIELD_NUMBER: _ClassVar[int]
    EDGE_TYPE_FILTER_FIELD_NUMBER: _ClassVar[int]
    MAX_DEPTH_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    revision_kref: Kref
    edge_type_filter: _containers.RepeatedScalarFieldContainer[str]
    max_depth: int
    limit: int
    def __init__(self, revision_kref: _Optional[_Union[Kref, _Mapping]] = ..., edge_type_filter: _Optional[_Iterable[str]] = ..., max_depth: _Optional[int] = ..., limit: _Optional[int] = ...) -> None: ...

class ImpactedRevision(_message.Message):
    __slots__ = ("revision_kref", "item_kref", "impact_depth", "impact_path_types")
    REVISION_KREF_FIELD_NUMBER: _ClassVar[int]
    ITEM_KREF_FIELD_NUMBER: _ClassVar[int]
    IMPACT_DEPTH_FIELD_NUMBER: _ClassVar[int]
    IMPACT_PATH_TYPES_FIELD_NUMBER: _ClassVar[int]
    revision_kref: Kref
    item_kref: Kref
    impact_depth: int
    impact_path_types: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, revision_kref: _Optional[_Union[Kref, _Mapping]] = ..., item_kref: _Optional[_Union[Kref, _Mapping]] = ..., impact_depth: _Optional[int] = ..., impact_path_types: _Optional[_Iterable[str]] = ...) -> None: ...

class ImpactAnalysisResponse(_message.Message):
    __slots__ = ("impacted_revisions", "total_impacted", "truncated")
    IMPACTED_REVISIONS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_IMPACTED_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    impacted_revisions: _containers.RepeatedCompositeFieldContainer[ImpactedRevision]
    total_impacted: int
    truncated: bool
    def __init__(self, impacted_revisions: _Optional[_Iterable[_Union[ImpactedRevision, _Mapping]]] = ..., total_impacted: _Optional[int] = ..., truncated: bool = ...) -> None: ...

class CreateBundleRequest(_message.Message):
    __slots__ = ("parent_path", "bundle_name", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PARENT_PATH_FIELD_NUMBER: _ClassVar[int]
    BUNDLE_NAME_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    parent_path: str
    bundle_name: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, parent_path: _Optional[str] = ..., bundle_name: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class BundleMember(_message.Message):
    __slots__ = ("item_kref", "added_at", "added_by", "added_by_username", "added_in_revision")
    ITEM_KREF_FIELD_NUMBER: _ClassVar[int]
    ADDED_AT_FIELD_NUMBER: _ClassVar[int]
    ADDED_BY_FIELD_NUMBER: _ClassVar[int]
    ADDED_BY_USERNAME_FIELD_NUMBER: _ClassVar[int]
    ADDED_IN_REVISION_FIELD_NUMBER: _ClassVar[int]
    item_kref: Kref
    added_at: str
    added_by: str
    added_by_username: str
    added_in_revision: int
    def __init__(self, item_kref: _Optional[_Union[Kref, _Mapping]] = ..., added_at: _Optional[str] = ..., added_by: _Optional[str] = ..., added_by_username: _Optional[str] = ..., added_in_revision: _Optional[int] = ...) -> None: ...

class AddBundleMemberRequest(_message.Message):
    __slots__ = ("bundle_kref", "member_item_kref", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    BUNDLE_KREF_FIELD_NUMBER: _ClassVar[int]
    MEMBER_ITEM_KREF_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    bundle_kref: Kref
    member_item_kref: Kref
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, bundle_kref: _Optional[_Union[Kref, _Mapping]] = ..., member_item_kref: _Optional[_Union[Kref, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class AddBundleMemberResponse(_message.Message):
    __slots__ = ("success", "message", "new_revision")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    NEW_REVISION_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    new_revision: RevisionResponse
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., new_revision: _Optional[_Union[RevisionResponse, _Mapping]] = ...) -> None: ...

class RemoveBundleMemberRequest(_message.Message):
    __slots__ = ("bundle_kref", "member_item_kref", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    BUNDLE_KREF_FIELD_NUMBER: _ClassVar[int]
    MEMBER_ITEM_KREF_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    bundle_kref: Kref
    member_item_kref: Kref
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, bundle_kref: _Optional[_Union[Kref, _Mapping]] = ..., member_item_kref: _Optional[_Union[Kref, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class RemoveBundleMemberResponse(_message.Message):
    __slots__ = ("success", "message", "new_revision")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    NEW_REVISION_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    new_revision: RevisionResponse
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., new_revision: _Optional[_Union[RevisionResponse, _Mapping]] = ...) -> None: ...

class GetBundleMembersRequest(_message.Message):
    __slots__ = ("bundle_kref", "revision_number")
    BUNDLE_KREF_FIELD_NUMBER: _ClassVar[int]
    REVISION_NUMBER_FIELD_NUMBER: _ClassVar[int]
    bundle_kref: Kref
    revision_number: int
    def __init__(self, bundle_kref: _Optional[_Union[Kref, _Mapping]] = ..., revision_number: _Optional[int] = ...) -> None: ...

class GetBundleMembersResponse(_message.Message):
    __slots__ = ("members", "revision_number", "total_count")
    MEMBERS_FIELD_NUMBER: _ClassVar[int]
    REVISION_NUMBER_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    members: _containers.RepeatedCompositeFieldContainer[BundleMember]
    revision_number: int
    total_count: int
    def __init__(self, members: _Optional[_Iterable[_Union[BundleMember, _Mapping]]] = ..., revision_number: _Optional[int] = ..., total_count: _Optional[int] = ...) -> None: ...

class BundleRevisionHistory(_message.Message):
    __slots__ = ("revision_number", "action", "member_item_kref", "author", "username", "created_at", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    REVISION_NUMBER_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    MEMBER_ITEM_KREF_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    revision_number: int
    action: str
    member_item_kref: Kref
    author: str
    username: str
    created_at: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, revision_number: _Optional[int] = ..., action: _Optional[str] = ..., member_item_kref: _Optional[_Union[Kref, _Mapping]] = ..., author: _Optional[str] = ..., username: _Optional[str] = ..., created_at: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class GetBundleHistoryRequest(_message.Message):
    __slots__ = ("bundle_kref",)
    BUNDLE_KREF_FIELD_NUMBER: _ClassVar[int]
    bundle_kref: Kref
    def __init__(self, bundle_kref: _Optional[_Union[Kref, _Mapping]] = ...) -> None: ...

class GetBundleHistoryResponse(_message.Message):
    __slots__ = ("history",)
    HISTORY_FIELD_NUMBER: _ClassVar[int]
    history: _containers.RepeatedCompositeFieldContainer[BundleRevisionHistory]
    def __init__(self, history: _Optional[_Iterable[_Union[BundleRevisionHistory, _Mapping]]] = ...) -> None: ...

class EventStreamRequest(_message.Message):
    __slots__ = ("routing_key_filter", "kref_filter", "cursor", "consumer_group", "from_latest", "from_cursor", "from_timestamp", "from_beginning")
    ROUTING_KEY_FILTER_FIELD_NUMBER: _ClassVar[int]
    KREF_FILTER_FIELD_NUMBER: _ClassVar[int]
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    CONSUMER_GROUP_FIELD_NUMBER: _ClassVar[int]
    FROM_LATEST_FIELD_NUMBER: _ClassVar[int]
    FROM_CURSOR_FIELD_NUMBER: _ClassVar[int]
    FROM_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    FROM_BEGINNING_FIELD_NUMBER: _ClassVar[int]
    routing_key_filter: str
    kref_filter: str
    cursor: str
    consumer_group: str
    from_latest: bool
    from_cursor: str
    from_timestamp: str
    from_beginning: bool
    def __init__(self, routing_key_filter: _Optional[str] = ..., kref_filter: _Optional[str] = ..., cursor: _Optional[str] = ..., consumer_group: _Optional[str] = ..., from_latest: bool = ..., from_cursor: _Optional[str] = ..., from_timestamp: _Optional[str] = ..., from_beginning: bool = ...) -> None: ...

class Event(_message.Message):
    __slots__ = ("routing_key", "kref", "timestamp", "author", "tenant_id", "details", "username", "cursor")
    class DetailsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ROUTING_KEY_FIELD_NUMBER: _ClassVar[int]
    KREF_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    routing_key: str
    kref: Kref
    timestamp: str
    author: str
    tenant_id: str
    details: _containers.ScalarMap[str, str]
    username: str
    cursor: str
    def __init__(self, routing_key: _Optional[str] = ..., kref: _Optional[_Union[Kref, _Mapping]] = ..., timestamp: _Optional[str] = ..., author: _Optional[str] = ..., tenant_id: _Optional[str] = ..., details: _Optional[_Mapping[str, str]] = ..., username: _Optional[str] = ..., cursor: _Optional[str] = ...) -> None: ...

class GetEventCapabilitiesRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class EventCapabilities(_message.Message):
    __slots__ = ("supports_replay", "supports_cursor", "supports_consumer_groups", "max_retention_hours", "max_buffer_size", "tier")
    SUPPORTS_REPLAY_FIELD_NUMBER: _ClassVar[int]
    SUPPORTS_CURSOR_FIELD_NUMBER: _ClassVar[int]
    SUPPORTS_CONSUMER_GROUPS_FIELD_NUMBER: _ClassVar[int]
    MAX_RETENTION_HOURS_FIELD_NUMBER: _ClassVar[int]
    MAX_BUFFER_SIZE_FIELD_NUMBER: _ClassVar[int]
    TIER_FIELD_NUMBER: _ClassVar[int]
    supports_replay: bool
    supports_cursor: bool
    supports_consumer_groups: bool
    max_retention_hours: int
    max_buffer_size: int
    tier: str
    def __init__(self, supports_replay: bool = ..., supports_cursor: bool = ..., supports_consumer_groups: bool = ..., max_retention_hours: _Optional[int] = ..., max_buffer_size: _Optional[int] = ..., tier: _Optional[str] = ...) -> None: ...

class CreateProjectRequest(_message.Message):
    __slots__ = ("name", "description")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    name: str
    description: str
    def __init__(self, name: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

class ProjectResponse(_message.Message):
    __slots__ = ("project_id", "name", "description", "created_at", "updated_at", "deprecated", "allow_public")
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    DEPRECATED_FIELD_NUMBER: _ClassVar[int]
    ALLOW_PUBLIC_FIELD_NUMBER: _ClassVar[int]
    project_id: str
    name: str
    description: str
    created_at: str
    updated_at: str
    deprecated: bool
    allow_public: bool
    def __init__(self, project_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., created_at: _Optional[str] = ..., updated_at: _Optional[str] = ..., deprecated: bool = ..., allow_public: bool = ...) -> None: ...

class GetProjectsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetProjectsResponse(_message.Message):
    __slots__ = ("projects",)
    PROJECTS_FIELD_NUMBER: _ClassVar[int]
    projects: _containers.RepeatedCompositeFieldContainer[ProjectResponse]
    def __init__(self, projects: _Optional[_Iterable[_Union[ProjectResponse, _Mapping]]] = ...) -> None: ...

class DeleteProjectRequest(_message.Message):
    __slots__ = ("project_id", "force")
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    project_id: str
    force: bool
    def __init__(self, project_id: _Optional[str] = ..., force: bool = ...) -> None: ...

class UpdateProjectRequest(_message.Message):
    __slots__ = ("project_id", "allow_public", "description")
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    ALLOW_PUBLIC_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    project_id: str
    allow_public: bool
    description: str
    def __init__(self, project_id: _Optional[str] = ..., allow_public: bool = ..., description: _Optional[str] = ...) -> None: ...

class SetDeprecatedRequest(_message.Message):
    __slots__ = ("kref", "deprecated")
    KREF_FIELD_NUMBER: _ClassVar[int]
    DEPRECATED_FIELD_NUMBER: _ClassVar[int]
    kref: Kref
    deprecated: bool
    def __init__(self, kref: _Optional[_Union[Kref, _Mapping]] = ..., deprecated: bool = ...) -> None: ...

class GetTenantUsageRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class TenantUsageResponse(_message.Message):
    __slots__ = ("node_count", "node_limit", "tenant_id")
    NODE_COUNT_FIELD_NUMBER: _ClassVar[int]
    NODE_LIMIT_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    node_count: int
    node_limit: int
    tenant_id: str
    def __init__(self, node_count: _Optional[int] = ..., node_limit: _Optional[int] = ..., tenant_id: _Optional[str] = ...) -> None: ...
