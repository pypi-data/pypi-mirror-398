from wedata_pre_code.common.base_client import BaseClient
import types


class Wedata3PreCodeClient(BaseClient):
    def __init__(self, workspace_id: str = None, mlflow_tracking_uri: str = None, base_url: str = None,
                 region: str = None, run_context_data: str = None):
        self.workspace_id = workspace_id
        self.mlflow_tracking_uri = mlflow_tracking_uri
        self.base_url = base_url
        self.region = region
        self.run_context_data = run_context_data
        self.check_required_properties("workspace_id", "mlflow_tracking_uri", "base_url", "run_context_data")
        self.init_pre_code()

    def init_pre_code(self):
        import os
        import json
        import mlflow
        from mlflow.tracking._tracking_service.client import TrackingServiceClient
        from mlflow.tracking import MlflowClient
        from mlflow.store.tracking.rest_store import RestStore
        import logging
        from functools import wraps
        import inspect
        from mlflow.models.model import Model
        os.environ["MLFLOW_RUN_CONTEXT"] = self.run_context_data
        os.environ["WEDATA_WORKSPACE_ID"] = self.workspace_id

        mlflow.set_tracking_uri(getattr(self, "mlflow_tracking_uri", "http://127.0.0.1:5000"))
        if self.region:
            # 日志输出装饰器
            base_url = self.base_url
            workspace_id = self.workspace_id

            def log_after_terminated(func):
                @wraps(func)
                def wrapper(self, run_id, *args, **kwargs):
                    print("wedata log_after_terminated wrapper")
                    result = func(self, run_id, *args, **kwargs)
                    run_info = self.store.get_run(run_id).info
                    run_name = run_info.run_name
                    experiment_id = run_info.experiment_id
                    experiment_url = f"${base_url}/datascience/experiments/experiments-single/{experiment_id}?o=${workspace_id}"
                    run_url = f"${base_url}/datascience/experiments/task-detail-learn/{run_id}?o=${workspace_id}"
                    print(f"View run {run_name} at :{run_url}")
                    print(f"View experiment at:{experiment_url}")
                    return result

                return wrapper

            TrackingServiceClient.set_terminated = log_after_terminated(TrackingServiceClient.set_terminated)

        # 模型版本标签注入装饰器
        def inject_model_version_tag(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                print("wedata inject_model_version_tag wrapper")
                registered_model_name = kwargs.get("registered_model_name")
                if registered_model_name is None:
                    sig = inspect.signature(func)
                    params = list(sig.parameters.keys())
                    if 'registered_model_name' in params:
                        idx = params.index('registered_model_name') - 1
                        if len(args) > idx:
                            registered_model_name = args[idx]
                result = func(*args, **kwargs)
                model_version = result.registered_model_version
                if registered_model_name and model_version:
                    from mlflow import MlflowClient
                    MlflowClient().set_model_version_tag(registered_model_name, model_version, "mlflow.user", "${uin}")
                    MlflowClient().set_model_version_tag(registered_model_name, model_version, "wedata.workspace",
                                                         "${workspaceId}")
                    MlflowClient().set_model_version_tag(registered_model_name, model_version,
                                                         "wedata.datascience.type", "MACHINE_LEARNING")
                return result

            return wrapper

        Model.log = inject_model_version_tag(Model.log)

        # 项目标签注入装饰器
        def inject_workspace_tag(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                workspace = os.getenv("WEDATA_WORKSPACE_ID")
                args_list = list(args)
                if workspace:
                    if 'tags' in kwargs:
                        tags = kwargs['tags'] or {}
                        tags = tags.copy()
                        # 如果传入的参数中有wedata.workspace和wedata.datascience.type，则不进行注入
                        if "wedata.workspace" not in tags:
                            tags["wedata.workspace"] = workspace
                        if "wedata.datascience.type" not in tags:
                            tags["wedata.datascience.type"] = "MACHINE_LEARNING"
                        kwargs['tags'] = tags
                    else:
                        current_tags = None
                        method_name = func.__name__
                        if current_tags is None:
                            if method_name in ('create_experiment', 'create_run'):
                                if len(args_list) >= 3:
                                    current_tags = args_list[2]
                            elif method_name in ('create_registered_model'):
                                if len(args_list) >= 2:
                                    current_tags = args_list[1]
                            elif method_name in ('create_model_version'):
                                if len(args_list) >= 5:
                                    current_tags = args_list[4]
                        if current_tags is None:
                            current_tags = {}
                        else:
                            current_tags = current_tags.copy()
                        current_tags["wedata.workspace"] = workspace
                        current_tags["wedata.datascience.type"] = "MACHINE_LEARNING"
                        current_tags["mlflow.user"] = "${uin}"
                        kwargs["tags"] = current_tags
                return func(self, *args, **kwargs)

            return wrapper

        # 标签验证装饰器
        def validate_wedata_tag(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                workspace = os.getenv("WEDATA_WORKSPACE_ID")
                obj = func(*args, **kwargs)
                if obj is None:
                    return obj
                workspace_tag = None
                datascience_type_tag = None
                method_name = func.__name__
                obj_name = 'object'
                if 'run' in method_name:
                    workspace_tag = obj.data.tags.get("wedata.workspace")
                    datascience_type_tag = obj.data.tags.get("wedata.datascience.type")
                    obj_name = 'run'
                elif 'experiment' in method_name:
                    obj_name = 'experiment'
                    workspace_tag = obj.tags.get("wedata.workspace")
                    datascience_type_tag = obj.tags.get("wedata.datascience.type")
                elif 'model' in method_name:
                    obj_name = 'model'
                    workspace_tag = obj.tags.get("wedata.workspace")
                    datascience_type_tag = obj.tags.get("wedata.datascience.type")
                if workspace and workspace_tag != workspace:
                    print(f"this workspace:{workspace},has no {obj_name}")
                    return None
                if datascience_type_tag not in ('MACHINE_LEARNING', 'DEEP_LEARNING'):
                    print(
                        "Only MACHINE_LEARNING and DEEP_LEARNING experiment/run/model can be operated in the notebook")
                    return None
                return obj

            return wrapper

        # 操作前验证装饰器
        def validate_wedata_before_operation(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                workspace = os.getenv("WEDATA_WORKSPACE_ID")
                if not workspace:
                    return func(self, *args, **kwargs)
                method_name = func.__name__
                id_name = None
                res = None
                workspace_tag = None
                data_science_type = None
                if 'experiment' in method_name:
                    id_name = kwargs.get("experiment_id") or (args[0] if args else None)
                    res = self.get_experiment(id_name)
                    if not res:
                        print(f"Experiment: '{id_name}' not exist or does not have permission to operate")
                        return
                    workspace_tag = res.tags.get("wedata.workspace")
                    data_science_type = res.tags.get("wedata.datascience.type")
                elif 'model' in method_name:
                    id_name = kwargs.get("name") or (args[0] if args else None)
                    res = self.get_registered_model(id_name)
                    if not res:
                        print(f"Model '{id_name}' not exist or does not have permission to operate")
                        return
                    workspace_tag = res.tags.get("wedata.workspace")
                    data_science_type = res.tags.get("wedata.datascience.type")
                else:
                    id_name = kwargs.get("run_id") or (args[0] if args else None)
                    res = self.get_run(id_name)
                    if not res:
                        print(f"run: '{id_name}' not exist or does not have permission to operate")
                        return
                    workspace_tag = res.data.tags.get("wedata.workspace")
                    data_science_type = res.data.tags.get("wedata.datascience.type")
                if workspace_tag != workspace or data_science_type not in ('MACHINE_LEARNING', 'DEEP_LEARNING'):
                    print(f"Unauthorized operation:{method_name} ({id_name})")
                    return
                if method_name in (
                        "update_tag", "delete_tags", "set_registered_model_tag", "delete_registered_model_tag",
                        "delete_model_version_tag", "set_experiment_tag"):
                    key_value = kwargs.get("key") or (args[1] if args else None)
                    if key_value == "wedata.workspace":
                        print(f"No permission to operate protected tags: {key_value}")
                        return
                return func(self, *args, **kwargs)

            return wrapper

        # 应用装饰器
        MlflowClient.create_experiment = inject_workspace_tag(MlflowClient.create_experiment)
        MlflowClient.create_registered_model = inject_workspace_tag(MlflowClient.create_registered_model)
        MlflowClient.create_model_version = inject_workspace_tag(MlflowClient.create_model_version)
        MlflowClient.get_experiment = validate_wedata_tag(MlflowClient.get_experiment)
        MlflowClient.get_experiment_by_name = validate_wedata_tag(MlflowClient.get_experiment_by_name)
        MlflowClient.get_run = validate_wedata_tag(MlflowClient.get_run)
        MlflowClient.get_parent_run = validate_wedata_tag(MlflowClient.get_parent_run)
        MlflowClient.get_registered_model = validate_wedata_tag(MlflowClient.get_registered_model)
        MlflowClient.delete_experiment = validate_wedata_before_operation(MlflowClient.delete_experiment)
        MlflowClient.restore_experiment = validate_wedata_before_operation(MlflowClient.restore_experiment)
        MlflowClient.rename_experiment = validate_wedata_before_operation(MlflowClient.rename_experiment)
        MlflowClient.set_experiment_tag = validate_wedata_before_operation(MlflowClient.set_experiment_tag)
        MlflowClient.set_tag = validate_wedata_before_operation(MlflowClient.set_tag)
        MlflowClient.delete_tag = validate_wedata_before_operation(MlflowClient.delete_tag)
        MlflowClient.update_run = validate_wedata_before_operation(MlflowClient.update_run)
        MlflowClient.download_artifacts = validate_wedata_before_operation(MlflowClient.download_artifacts)
        MlflowClient.list_artifacts = validate_wedata_before_operation(MlflowClient.list_artifacts)
        MlflowClient.delete_run = validate_wedata_before_operation(MlflowClient.delete_run)
        MlflowClient.restore_run = validate_wedata_before_operation(MlflowClient.restore_run)
        MlflowClient.rename_registered_model = validate_wedata_before_operation(MlflowClient.rename_registered_model)
        MlflowClient.update_registered_model = validate_wedata_before_operation(MlflowClient.update_registered_model)
        MlflowClient.delete_registered_model = validate_wedata_before_operation(MlflowClient.delete_registered_model)
        MlflowClient.update_model_version = validate_wedata_before_operation(MlflowClient.update_model_version)
        MlflowClient.delete_model_version = validate_wedata_before_operation(MlflowClient.delete_model_version)
        MlflowClient.set_model_version_tag = validate_wedata_before_operation(MlflowClient.set_model_version_tag)
        MlflowClient.delete_model_version_tag = validate_wedata_before_operation(MlflowClient.delete_model_version_tag)
        MlflowClient.set_registered_model_alias = validate_wedata_before_operation(
            MlflowClient.set_registered_model_alias)
        MlflowClient.delete_registered_model_alias = validate_wedata_before_operation(
            MlflowClient.delete_registered_model_alias)
        MlflowClient.set_registered_model_tag = validate_wedata_before_operation(MlflowClient.set_registered_model_tag)
        MlflowClient.delete_registered_model_tag = validate_wedata_before_operation(
            MlflowClient.delete_registered_model_tag)
