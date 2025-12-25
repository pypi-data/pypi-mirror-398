from wedata_pre_code.common.base_client import BaseClient


class Wedata2PreCodeClient(BaseClient):
    def __init__(self, wedata_project_id: str = None, wedata_notebook_engine: str = None, qcloud_uin: str = None,
                 qcloud_subuin: str = None, wedata_default_feature_store_database: str = None,
                 wedata_feature_store_databases: str = None, qcloud_region: str = None,
                 mlflow_tracking_uri: str = None, kernel_task_name: str = None, kernel_task_id: str = None,
                 kernel_submit_form_workflow: str = None, kernel_region: str = None, kernel_is_international: str = None):

        self.wedata_project_id = wedata_project_id
        self.wedata_notebook_engine = wedata_notebook_engine
        self.qcloud_uin = qcloud_uin
        self.qcloud_subuin = qcloud_subuin
        self.wedata_default_feature_store_database = wedata_default_feature_store_database
        self.wedata_feature_store_databases = wedata_feature_store_databases
        self.qcloud_region = qcloud_region
        self.mlflow_tracking_uri = mlflow_tracking_uri
        self.kernel_task_name = kernel_task_name
        self.kernel_task_id = kernel_task_id
        self.kernel_submit_form_workflow = kernel_submit_form_workflow
        self.kernel_region = kernel_region
        self.kernel_is_international = kernel_is_international
        self.check_required_properties("wedata_project_id", "wedata_notebook_engine", "qcloud_uin", "qcloud_subuin",
                                       "wedata_default_feature_store_database", "wedata_feature_store_databases",
                                       "qcloud_region", "mlflow_tracking_uri", "kernel_task_name", "kernel_task_id",
                                       "kernel_submit_form_workflow", "kernel_region")
        self.init_pre_code()

    def init_pre_code(self):
        import os
        from mlflow.tracking._tracking_service.client import TrackingServiceClient
        from mlflow.tracking import MlflowClient
        from functools import wraps
        import json

        os.environ['WEDATA_PROJECT_ID'] = self.wedata_project_id
        os.environ['WEDATA_NOTEBOOK_ENGINE'] = self.wedata_notebook_engine
        os.environ['QCLOUD_UIN'] = self.qcloud_uin
        os.environ['QCLOUD_SUBUIN'] = self.qcloud_subuin
        os.environ['WEDATA_DEFAULT_FEATURE_STORE_DATABASE'] = self.wedata_default_feature_store_database
        os.environ['WEDATA_FEATURE_STORE_DATABASES'] = self.wedata_feature_store_databases
        os.environ['QCLOUD_REGION'] = self.qcloud_region
        os.environ["MLFLOW_TRACKING_URI"] = self.mlflow_tracking_uri

        user_name = self.qcloud_uin
        task_name = self.kernel_task_name
        task_id = self.kernel_task_id
        try:
            workflow_id = self.kernel_submit_form_workflow
        except Exception:
            workflow_id = ""

        project_id = self.wedata_project_id
        os.environ["WEDATA_PROJECT_ID"] = project_id
        os.environ["KERNEL_SUBMIT_FORM_WORKFLOW"] = workflow_id

        region = self.kernel_region
        is_international = self.kernel_is_international

        template = (
            "https://{region}.wedata.tencentcloud.com"  # 国际站
            if is_international
            else "https://{region}.wedata.cloud.tencent.com"  # 国内站
        )
        base_url = f"{template.format(region=region)}"

        run_context_data = {
            "mlflow.source.name": task_name,
            "mlflow.user": user_name,
            "wedata.taskId": task_id,
            "wedata.workflowId": workflow_id,
            "wedata.datascience.type": "MACHINE_LEARNING",
            "wedata.project": project_id
        }
        run_context_value = json.dumps(run_context_data, indent=None)

        os.environ["MLFLOW_RUN_CONTEXT"] = run_context_value

        def log_after_terminated(func):
            @wraps(func)
            def wrapper(self, run_id, *args, **kwargs):
                print("wedata log_after_terminated wrapper")
                # 调用原set_terminated
                result = func(self, run_id, *args, **kwargs)
                # 获取experiment_id
                run_info = self.store.get_run(run_id).info
                run_name = run_info.run_name
                experiment_id = run_info.experiment_id
                experment_url = f"{base_url}/datascience/experiments-single/{experiment_id}?ProjectId={project_id}"
                run_url = f"{base_url}/datascience/experiments/task-detail-learn/{run_id}?ProjectId={project_id}"
                print(f"View run {run_name} at :{run_url}")
                print(f"View experiment at:{experment_url}")
                return result

            return wrapper

        from mlflow.models.model import Model
        def inject_model_version_tag(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                print("wedata inject_model_version_tag wrapper")
                registered_model_name = kwargs.get("registered_model_name")
                if registered_model_name is None:
                    # 如果在 args 里，找到它的位置
                    import inspect
                    sig = inspect.signature(func)
                    params = list(sig.parameters.keys())
                    if 'registered_model_name' in params:
                        idx = params.index('registered_model_name') - 1  # -1 因为 self
                        if len(args) > idx:
                            registered_model_name = args[idx]
                result = func(*args, **kwargs)
                model_version = result.registered_model_version
                # 添加 tag
                if registered_model_name and model_version:
                    from mlflow import MlflowClient
                    MlflowClient().set_model_version_tag(registered_model_name, model_version, "mlflow.user",
                                                         "{user_name}")
                    MlflowClient().set_model_version_tag(registered_model_name, model_version, "wedata.project",
                                                         "{project_id}")
                    MlflowClient().set_model_version_tag(registered_model_name, model_version,
                                                         "wedata.datascience.type", "MACHINE_LEARNING")
                return result

            return wrapper

        Model.log = inject_model_version_tag(Model.log)

        def inject_project_filter(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 从环境变量获取 project 值
                project = os.getenv("WEDATA_PROJECT_ID")
                if project:
                    # 获取原始过滤条件
                    filter_str = kwargs.get("filter_string", "")
                    # 拼接新的过滤条件（假设 project 存储在 run 的 tag 中）
                    new_filter = f"tags.wedata.project = '{project}' and tags.wedata.datascience.type='MACHINE_LEARNING'"
                    if filter_str:
                        new_filter = f"({filter_str}) and ({new_filter})"
                    kwargs["filter_string"] = new_filter
                return func(*args, **kwargs)

            return wrapper

        def inject_project_tag(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                project = os.getenv("WEDATA_PROJECT_ID")
                workflow_id = os.getenv("KERNEL_SUBMIT_FORM_WORKFLOW")
                args_list = list(args)
                if project:
                    if 'tags' in kwargs:
                        tags = kwargs['tags'] or {}
                        tags = tags.copy()
                        tags["wedata.project"] = project
                        tags["wedata.datascience.type"] = "MACHINE_LEARNING"
                        tags["wedata.workflowId"] = workflow_id
                        kwargs['tags'] = tags
                    else:
                        current_tags = {}
                        method_name = func.__name__
                        if current_tags == None:
                            if method_name in ('create_experiment', 'create_run'):
                                if len(args_list) >= 3:
                                    current_tags = args_list[2]
                            elif method_name in ('create_registered_model'):
                                if len(args_list) >= 2:
                                    current_tags = args[1]
                            elif method_name in ('create_model_version'):
                                if len(args_list) >= 5:
                                    current_tags = args[4]
                        if current_tags is None:
                            current_tags = {}
                        else:
                            current_tags = current_tags.copy()  # 避免修改原始字典
                        current_tags["wedata.project"] = project
                        current_tags["wedata.datascience.type"] = "MACHINE_LEARNING"
                        current_tags["mlflow.user"] = "{user_name}"
                        kwargs["tags"] = current_tags
                return func(self, *args, **kwargs)

            return wrapper

        def validate_wedata_tag(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                project = os.getenv("WEDATA_PROJECT_ID")
                # 调用原始方法获取 Experiment
                obj = func(*args, **kwargs)

                # 如果 Experiment 不存在，直接返回错误
                if obj is None:
                    # print("object is not exists")
                    return obj

                project_tag = None
                datascience_type_tag = None
                method_name = func.__name__
                obj_name = 'object'
                if 'run' in method_name:
                    project_tag = obj.data.tags.get("wedata.project")
                    datascience_type_tag = obj.data.tags.get("wedata.datascience.type")
                    obj_name = 'run'
                elif 'experiment' in method_name:
                    obj_name = 'experiment'
                    project_tag = obj.tags.get("wedata.project")
                    datascience_type_tag = obj.tags.get("wedata.datascience.type")
                elif 'model' in method_name:
                    obj_name = 'model'
                    project_tag = obj.tags.get("wedata.project")
                    datascience_type_tag = obj.tags.get("wedata.datascience.type")
                # 检查标签是否存在且值正确
                if project and project_tag != project:
                    print(f"this project:{project},has no {obj_name}")
                    return None
                if datascience_type_tag != 'MACHINE_LEARNING':
                    print("Only MACHINE_LEARNING experiment/run/model can be operated in the notebook")
                    return None
                return obj

            return wrapper

        def validate_wedata_before_operation(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                project = os.getenv("WEDATA_PROJECT_ID")
                # 如果未设置环境变量，直接执行原删除操作
                if not project:
                    return func(self, *args, **kwargs)
                method_name = func.__name__

                id_name = None
                res = None
                project_tag = None
                data_science_type = None
                # 如果设置了环境变量，则校验标签
                # 获取 Experiment 对象
                if 'experiment' in method_name:
                    id_name = kwargs.get("experiment_id") or (args[0] if args else None)
                    res = self.get_experiment(id_name)
                    if not res:
                        print(f"Experiment: '{id_name}' not exist or does not have permission to operate")
                        return
                    project_tag = res.tags.get("wedata.project")
                    data_science_type = res.tags.get("wedata.datascience.type")
                elif 'model' in method_name:
                    id_name = kwargs.get("name") or (args[0] if args else None)
                    res = self.get_registered_model(id_name)
                    if not res:
                        print(f"Model '{id_name}' not exist or does not have permission to operate")
                        return
                    project_tag = res.tags.get("wedata.project")
                    data_science_type = res.tags.get("wedata.datascience.type")
                else:
                    id_name = kwargs.get("run_id") or (args[0] if args else None)
                    res = self.get_run(id_name)
                    if not res:
                        print(f"run: '{id_name}' not exist or does not have permission to operate")
                        return
                    project_tag = res.data.tags.get("wedata.project")
                    data_science_type = res.data.tags.get("wedata.datascience.type")
                # print(f"query result:{res}")
                # 检查标签是否匹配
                if project_tag != project or data_science_type != 'MACHINE_LEARNING':
                    print(f"Unauthorized operation:{method_name} ({id_name})")
                    return  # 不执行删除

                # print(method_name)
                # 操作标签的操作需要确认不会影响内置标签wedata.project
                if method_name in ("update_tag", "delete_tags",
                                   "set_registered_model_tag",
                                   "delete_registered_model_tag",
                                   "delete_model_version_tag", "set_experiment_tag"):
                    # 获取 key 参数的值
                    key_value = kwargs.get("key") or (args[1] if args else None)
                    print(key_value)
                    if key_value == "wedata.project":
                        print(f"No permission to operate protected tags: {key_value}")
                        return
                # 标签匹配，执行删除
                return func(self, *args, **kwargs)

            return wrapper

        # 1. 应用装饰器，过滤条件filter_str 中添加tag
        MlflowClient.search_experiments = inject_project_filter(MlflowClient.search_experiments)
        MlflowClient.search_runs = inject_project_filter(MlflowClient.search_runs)
        MlflowClient.search_registered_models = inject_project_filter(MlflowClient.search_registered_models)
        MlflowClient.search_model_versions = inject_project_filter(MlflowClient.search_model_versions)
        MlflowClient.create_experiment = inject_project_tag(MlflowClient.create_experiment)
        MlflowClient.create_registered_model = inject_project_tag(MlflowClient.create_registered_model)
        MlflowClient.create_model_version = inject_project_tag(MlflowClient.create_model_version)
        # 2. 后置返回结果过滤wedata_project tag
        MlflowClient.get_experiment = validate_wedata_tag(MlflowClient.get_experiment)
        MlflowClient.get_experiment_by_name = validate_wedata_tag(MlflowClient.get_experiment_by_name)
        MlflowClient.get_run = validate_wedata_tag(MlflowClient.get_run)
        MlflowClient.get_parent_run = validate_wedata_tag(MlflowClient.get_parent_run)
        MlflowClient.get_registered_model = validate_wedata_tag(MlflowClient.get_registered_model)
        TrackingServiceClient.set_terminated = log_after_terminated(TrackingServiceClient.set_terminated)
        # MlflowClient.get_model_version = validate_wedata_tag(MlflowClient.get_model_version)
        # MlflowClient.get_model_version_download_uri = validate_wedata_tag(MlflowClient.get_model_version_download_uri)
        # MlflowClient.get_latest_versions = validate_wedata_tag(MlflowClient.get_latest_versions)
        # 4. 操作前校验,参数experment_id
        MlflowClient.delete_experiment = validate_wedata_before_operation(MlflowClient.delete_experiment)
        MlflowClient.restore_experiment = validate_wedata_before_operation(MlflowClient.restore_experiment)
        MlflowClient.rename_experiment = validate_wedata_before_operation(MlflowClient.rename_experiment)
        MlflowClient.set_experiment_tag = validate_wedata_before_operation(MlflowClient.set_experiment_tag)
        # 操作前校验 参数run_id
        MlflowClient.set_tag = validate_wedata_before_operation(MlflowClient.set_tag)
        MlflowClient.delete_tag = validate_wedata_before_operation(MlflowClient.delete_tag)
        MlflowClient.update_run = validate_wedata_before_operation(MlflowClient.update_run)
        MlflowClient.download_artifacts = validate_wedata_before_operation(MlflowClient.download_artifacts)
        MlflowClient.list_artifacts = validate_wedata_before_operation(MlflowClient.list_artifacts)
        MlflowClient.delete_run = validate_wedata_before_operation(MlflowClient.delete_run)
        MlflowClient.restore_run = validate_wedata_before_operation(MlflowClient.restore_run)
        # 操作前校验 参数name
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

        # TOOD：设置tag相关需要校验设置的key是否为wedata_project
        MlflowClient.set_registered_model_tag = validate_wedata_before_operation(MlflowClient.set_registered_model_tag)
        MlflowClient.delete_registered_model_tag = validate_wedata_before_operation(
            MlflowClient.delete_registered_model_tag)
