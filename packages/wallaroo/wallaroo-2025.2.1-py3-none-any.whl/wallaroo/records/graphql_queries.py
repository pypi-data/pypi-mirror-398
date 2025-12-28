# Generated from root api

import gql

CreateDefaultUserWorkspace = gql.gql(
    """
mutation CreateDefaultUserWorkspace($user_id: String!, $workspace_name: String!, $user_type: String) { insert_workspace_one( object: { name: $workspace_name, owner_id: $user_id, users: { data: { user_id: $user_id, user_type: $user_type } }, archived: false, user_default_workspaces: { data: { user_id: $user_id } } }, on_conflict: { constraint: workspace_name_key, update_columns: [] } ) { id } }
"""
)

CreateDeployment = gql.gql(
    """
mutation CreateDeployment($deploy_id: String!, $pipeline_id: bigint, $deployed: Boolean, $engine_config: jsonb) { insert_deployment( objects: { deployed: $deployed, deploy_id: $deploy_id, pipeline_id: $pipeline_id, engine_config: $engine_config} on_conflict: { constraint: deployment_pipeline_id_key, update_columns: [updated_at, deployed, engine_config] } ) { returning { id deployed deployment_name: deploy_id engine_config created_at } } }
"""
)

CreatePipelineWithDefinition = gql.gql(
    """
mutation CreatePipelineWithDefinition( $pipeline_id: String!, $definition: jsonb!, $visibility: String, $workspace_id: bigint! ) { insert_pipeline( objects: { pipeline_versions: { data: { definition: $definition } } pipeline_id: $pipeline_id visibility: $visibility workspace_id: $workspace_id } on_conflict: { constraint: pipeline_pipeline_id_workspace_id_key, update_columns: [updated_at, visibility] } ) { returning { id, pipeline_versions(order_by: {id: desc}, limit: 1) { id } } } }
"""
)

CreateTag = gql.gql(
    """
mutation CreateTag($tag_text: String!) { insert_tag(objects: {tag: $tag_text}) { returning { id tag } } }
"""
)

CreateWorkspace = gql.gql(
    """
mutation CreateWorkspace($user_id: String!, $workspace_name: String!, $user_type:String) { insert_workspace_one(object: {name: $workspace_name, created_by: $user_id, users: {data: {user_id: $user_id, user_type: $user_type}}, archived: false}) { id } }
"""
)

DeleteWorkspaceUser = gql.gql(
    """
mutation DeleteWorkspaceUser($user_id: String!, $workspace_id: bigint!) { delete_workspace_users(where: {user_id: {_eq: $user_id}, _and: {workspace_id: {_eq: $workspace_id}}}) { affected_rows } }
"""
)

GetDeploymentForPipeline = gql.gql(
    """
query GetDeploymentForPipeline($pipeline_id: bigint!) { pipeline_by_pk(id: $pipeline_id) { deployment { id deploy_id deployed } } }
"""
)

GetModelConfigs = gql.gql(
    """
query GetModelConfigs($workspace_id: bigint!) { model_config(where: {model: {model: {workspace_id: {_eq: $workspace_id}}}}) { id model { id file_name model_id model_version models_pk_id sha updated_at owner_id } } }
"""
)

GetModels = gql.gql(
    """
query GetModels($workspace_id: bigint!) { models(where: {workspace_id: {_eq: $workspace_id}}) { id models { sha models_pk_id model_version owner_id model_id id file_name } } }
"""
)

GetPipelineAndWorkspace = gql.gql(
    """
query GetPipelineAndWorkspace($pk_id: bigint!) { pipeline_by_pk(id: $pk_id) { workspace_id pipeline_id } }
"""
)

GetPipelineByName = gql.gql(
    """
fragment pipelineFields on pipeline { id pipeline_id owner_id created_at updated_at visibility pipeline_tags { id pipeline_pk_id tag_pk_id tag { id tag } } pipeline_versions { version created_at updated_at deployment_pipeline_versions { deployment { deployed engine_config } } } } query GetPipelineByName($pipeline_id: String, $workspace_id: bigint) { pipeline(where: { pipeline_id: { _eq: $pipeline_id }, workspace_id: { _eq: $workspace_id } }) { ...pipelineFields } }
"""
)

GetPipelinesForModels = gql.gql(
    """
query GetPipelinesForModels($id: bigint!) { deployment_model_configs(where: {model_config: {model_id: {_eq: $id}}}) { model_config { model { id model_id model_version models_pk_id } } pipeline_version { pipeline { id pipeline_id } updated_at version } } }
"""
)

GetPipelineVersionDeploymentDetails = gql.gql(
    """
query GetPipelineVersionDeploymentDetails($pipeline_version_pk_id: bigint) { deployment_pipeline_version(where: {pipeline_version_pk_id: {_eq: $pipeline_version_pk_id}}) { pipeline_version { pipeline_pk_id definition pipeline { workspace_id pipeline_id } } } }
"""
)

InsertDeploymentModelConfig = gql.gql(
    """
mutation InsertDeploymentModelConfig( $deployment_id: bigint $model_config_id: bigint $pipeline_version_pk_id: bigint ) { insert_deployment_model_configs( objects: { deployment_id: $deployment_id model_config_id: $model_config_id pipeline_version_pk_id: $pipeline_version_pk_id } ) { returning { id } } }
"""
)

InsertDeploymentModelConfigMultiple = gql.gql(
    """
mutation InsertDeploymentModelConfigs($objects: [deployment_model_configs_insert_input!]!) { insert_deployment_model_configs(objects: $objects) { returning { id } } }
"""
)

InsertDeploymentPipelineVersion = gql.gql(
    """
mutation InsertDeploymentPipelineVersion( $deployment_id: bigint $pipeline_version_pk_id: bigint ) { insert_deployment_pipeline_version( objects: { deployment_id: $deployment_id pipeline_version_pk_id: $pipeline_version_pk_id } ) { returning { id } } }
"""
)

InsertModelConfig = gql.gql(
    """
mutation InsertModelConfig($model_id: bigint!, $runtime: String!) { insert_model_config_one(object: {model_id: $model_id, runtime: $runtime}) { id } }
"""
)

InsertWorkspaceUser = gql.gql(
    """
mutation InsertWorkspaceUser($user_id: String!, $user_type: String!, $workspace_id: bigint) { insert_workspace_users_one(object: {user_id: $user_id, user_type: $user_type, workspace_id: $workspace_id}, on_conflict: {constraint: workspace_users_workspace_id_user_id_key, update_columns: user_type}) { id } }
"""
)

ListDeployments = gql.gql(
    """
query ListDeployments { deployment { id deploy_id deployed deployment_model_configs { model_config { id } } } }
"""
)

ListModelConversions = gql.gql(
    """
query ListModelConversions { model_conversion { id name workspace_id name comment } }
"""
)

ListModels = gql.gql(
    """
query ListModels { model(order_by: {id: desc}) { id model_id model_version file_name updated_at } }
"""
)

ListPipelines = gql.gql(
    """
query ListPipelines { pipeline(order_by: {id: desc}) { id pipeline_tags { tag { tag } } } }
"""
)

ListWorkspaces = gql.gql(
    """
query ListWorkspaces { workspace { id name created_at created_by archived models { models { id } } pipelines { id } } }
"""
)

ModelByName = gql.gql(
    """
query ModelByName($model_id: String!, $model_version: String!) { model(where: {_and: [{model_id: {_eq: $model_id}}, {model_version: {_eq: $model_version}}]}) { id model_id model_version } }
"""
)

PipelineModels = gql.gql(
    """
query PipelineModels($pipeline_id: bigint!) { pipeline_by_pk(id: $pipeline_id) { id deployment { deployment_model_configs_aggregate(distinct_on: deployment_id) { nodes { model_config { model { model { name } } } } } } } }
"""
)

PipelineVariantById = gql.gql(
    """
query PipelineVariantById($variant_id: bigint!) { pipeline_version_by_pk(id: $variant_id) { id created_at updated_at version definition pipeline { id } deployment_pipeline_versions { created_at updated_at deployment { id } } } }
"""
)

Undeploy = gql.gql(
    """
mutation Undeploy($id: bigint!) { update_deployment_by_pk(pk_columns: {id: $id} _set: { deployed: false }) { id deploy_id deployed } }
"""
)

UpdateModelConversionMetaData = gql.gql(
    """
mutation UpdateModelConversionMetaData( $model_id: bigint! $name: String! $workspace_id: bigint! $minio_path: String! $updated_at: timestamptz! $comment: String ) { insert_model_conversion_one( object: { model_id: $model_id workspace_id: $workspace_id name: $name minio_path: $minio_path updated_at: $updated_at comment: $comment } on_conflict: { constraint: model_conversion_name_workspace_id_key update_columns: [model_id, workspace_id, name, comment, minio_path] } ) { id model_id workspace_id } }
"""
)

UserDefaultWorkspace = gql.gql(
    """
query UserDefaultWorkspace($user_id: String = "") { user_default_workspace(where: {user_id: {_eq: $user_id}}) { workspace { archived created_at created_by name id users { user_id } pipelines { id } models { models { id } } } } }
"""
)

WorkspaceById = gql.gql(
    """
query WorkspaceById($id: bigint!) { workspace_by_pk(id: $id) { archived created_at created_by id name users { user_id } models { models { id } } pipelines { id } } }
"""
)

WorkspaceByName = gql.gql(
    """
query WorkspaceByName($name: string!) { workspace(where: {name: {_eq: $name}}) { archived created_at created_by id name users { user_id } models { models { id } } pipelines { id } } }
"""
)

WorkspaceNameById = gql.gql(
    """
query GetWorkspaceNameById($id: bigint!) { workspace_by_pk(id: $id) { id name } }
"""
)
