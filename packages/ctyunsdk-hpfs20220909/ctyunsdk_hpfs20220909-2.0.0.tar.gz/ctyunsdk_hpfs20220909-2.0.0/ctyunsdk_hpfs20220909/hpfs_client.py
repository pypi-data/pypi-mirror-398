from ctyun_python_sdk_core import CtyunClient, Credential, ClientConfig, CtyunRequestException

from .models import *


class HpfsClient:
    def __init__(self, client_config: ClientConfig):
        self.endpoint = client_config.endpoint
        self.credential = Credential(client_config.access_key_id, client_config.access_key_secret)
        self.ctyun_client = CtyunClient(client_config.verify_tls)

    def v4_hpfs_new_protocol_service(self, request: V4HpfsNewProtocolServiceRequest) -> V4HpfsNewProtocolServiceResponse:
        """创建协议服务"""
        url = f"{self.endpoint}/v4/hpfs/new-protocol-service"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsNewProtocolServiceResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_new_dataflowtask(self, request: V4HpfsNewDataflowtaskRequest) -> V4HpfsNewDataflowtaskResponse:
        """创建数据流动任务"""
        url = f"{self.endpoint}/v4/hpfs/new-dataflowtask"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsNewDataflowtaskResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_new_dataflow(self, request: V4HpfsNewDataflowRequest) -> V4HpfsNewDataflowResponse:
        """创建数据流动策略"""
        url = f"{self.endpoint}/v4/hpfs/new-dataflow"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsNewDataflowResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_delete_protocol_service(self, request: V4HpfsDeleteProtocolServiceRequest) -> V4HpfsDeleteProtocolServiceResponse:
        """删除协议服务"""
        url = f"{self.endpoint}/v4/hpfs/delete-protocol-service"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsDeleteProtocolServiceResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_delete_dataflow(self, request: V4HpfsDeleteDataflowRequest) -> V4HpfsDeleteDataflowResponse:
        """删除数据流动策略"""
        url = f"{self.endpoint}/v4/hpfs/delete-dataflow"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsDeleteDataflowResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_list_protocol_service(self, request: V4HpfsListProtocolServiceRequest) -> V4HpfsListProtocolServiceResponse:
        """查询协议服务列表"""
        url = f"{self.endpoint}/v4/hpfs/list-protocol-service"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsListProtocolServiceResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_info_protocol_service(self, request: V4HpfsInfoProtocolServiceRequest) -> V4HpfsInfoProtocolServiceResponse:
        """查询协议服务详情"""
        url = f"{self.endpoint}/v4/hpfs/info-protocol-service"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsInfoProtocolServiceResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_list_fileset(self, request: V4HpfsListFilesetRequest) -> V4HpfsListFilesetResponse:
        """查询FILESET列表"""
        url = f"{self.endpoint}/v4/hpfs/list-fileset"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsListFilesetResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_info_fileset(self, request: V4HpfsInfoFilesetRequest) -> V4HpfsInfoFilesetResponse:
        """查询FILESET详情"""
        url = f"{self.endpoint}/v4/hpfs/info-fileset"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsInfoFilesetResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_info_by_name_sfs(self, request: V4HpfsInfoByNameSfsRequest) -> V4HpfsInfoByNameSfsResponse:
        """根据并行文件名称和资源池ID，查询文件系统详情"""
        url = f"{self.endpoint}/v4/hpfs/info-by-name-sfs"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsInfoByNameSfsResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_info_sfs(self, request: V4HpfsInfoSfsRequest) -> V4HpfsInfoSfsResponse:
        """根据资源池 ID 和 sfsUID，查询文件系统详情"""
        url = f"{self.endpoint}/v4/hpfs/info-sfs"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsInfoSfsResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_resize_sfs(self, request: V4HpfsResizeSfsRequest) -> V4HpfsResizeSfsResponse:
        """修改文件系统大小"""
        url = f"{self.endpoint}/v4/hpfs/resize-sfs"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsResizeSfsResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_list_sfs(self, request: V4HpfsListSfsRequest) -> V4HpfsListSfsResponse:
        """资源池 ID 下，所有的文件系统详情查询"""
        url = f"{self.endpoint}/v4/hpfs/list-sfs"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsListSfsResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_new_fileset(self, request: V4HpfsNewFilesetRequest) -> V4HpfsNewFilesetResponse:
        """并行文件创建FILESET"""
        url = f"{self.endpoint}/v4/hpfs/new-fileset"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsNewFilesetResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_new_directory(self, request: V4HpfsNewDirectoryRequest) -> V4HpfsNewDirectoryResponse:
        """指定并行文件创建目录并设置权限此请求是异步处理，返回800代表请求下发成功，具体结果请使用【查询并行文件目录信息】确定是否创建成功"""
        url = f"{self.endpoint}/v4/hpfs/new-directory"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsNewDirectoryResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_delete_fileset(self, request: V4HpfsDeleteFilesetRequest) -> V4HpfsDeleteFilesetResponse:
        """删除FILESET"""
        url = f"{self.endpoint}/v4/hpfs/delete-fileset"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsDeleteFilesetResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_new_sfs(self, request: V4HpfsNewSfsRequest) -> V4HpfsNewSfsResponse:
        """创建文件系统"""
        url = f"{self.endpoint}/v4/hpfs/new-sfs"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsNewSfsResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_list_baseline(self, request: V4HpfsListBaselineRequest) -> V4HpfsListBaselineResponse:
        """查询对应资源池 ID 下，指定存储类型的性能基线列表，若资源池不支持性能基线，则该接口会报错"""
        url = f"{self.endpoint}/v4/hpfs/list-baseline"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsListBaselineResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_update_fileset(self, request: V4HpfsUpdateFilesetRequest) -> V4HpfsUpdateFilesetResponse:
        """修改FILESET配额限制与描述"""
        url = f"{self.endpoint}/v4/hpfs/update-fileset"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsUpdateFilesetResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_update_label(self, request: V4HpfsUpdateLabelRequest) -> V4HpfsUpdateLabelResponse:
        """为指定并行文件实例添加标签，支持添加单个和多个标签。"""
        url = f"{self.endpoint}/v4/hpfs/update-label"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsUpdateLabelResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_refund_sfs(self, request: V4HpfsRefundSfsRequest) -> V4HpfsRefundSfsResponse:
        """退订文件系统"""
        url = f"{self.endpoint}/v4/hpfs/refund-sfs"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsRefundSfsResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_rename_sfs(self, request: V4HpfsRenameSfsRequest) -> V4HpfsRenameSfsResponse:
        """指定文件系统重命名此请求是异步处理，返回800代表请求下发成功，具体结果请使用【并行文件信息查询】确认"""
        url = f"{self.endpoint}/v4/hpfs/rename-sfs"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsRenameSfsResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_list_cluster(self, request: V4HpfsListClusterRequest) -> V4HpfsListClusterResponse:
        """查询对应资源池 ID 下集群列表"""
        url = f"{self.endpoint}/v4/hpfs/list-cluster"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsListClusterResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_list_dataflowtask(self, request: V4HpfsListDataflowtaskRequest) -> V4HpfsListDataflowtaskResponse:
        """查询资源池 ID 下，所有的数据流动任务详情"""
        url = f"{self.endpoint}/v4/hpfs/list-dataflowtask"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsListDataflowtaskResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_info_dataflowtask(self, request: V4HpfsInfoDataflowtaskRequest) -> V4HpfsInfoDataflowtaskResponse:
        """查询资源池 ID 下，指定数据流动任务详情"""
        url = f"{self.endpoint}/v4/hpfs/info-dataflowtask"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsInfoDataflowtaskResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_list_dataflow(self, request: V4HpfsListDataflowRequest) -> V4HpfsListDataflowResponse:
        """查询资源池 ID 下，所有的数据流动策略详情"""
        url = f"{self.endpoint}/v4/hpfs/list-dataflow"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsListDataflowResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_info_dataflow(self, request: V4HpfsInfoDataflowRequest) -> V4HpfsInfoDataflowResponse:
        """根据dataflowID查询指定资源池下数据流动策略信息"""
        url = f"{self.endpoint}/v4/hpfs/info-dataflow"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsInfoDataflowResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_update_dataflow(self, request: V4HpfsUpdateDataflowRequest) -> V4HpfsUpdateDataflowResponse:
        """更新数据流动策略"""
        url = f"{self.endpoint}/v4/hpfs/update-dataflow"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsUpdateDataflowResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_allocable_quota_sfs(self, request: V4HpfsAllocableQuotaSfsRequest) -> V4HpfsAllocableQuotaSfsResponse:
        """查询指定并行文件创建FILESET时可分配容量、文件数"""
        url = f"{self.endpoint}/v4/hpfs/allocable-quota-sfs"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsAllocableQuotaSfsResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_capacity_quota_sfs(self, request: V4HpfsCapacityQuotaSfsRequest) -> V4HpfsCapacityQuotaSfsResponse:
        """根据资源池ID查询用户在某地域的并行文件容量配额总量，已使用容量，剩余容量"""
        url = f"{self.endpoint}/v4/hpfs/capacity-quota-sfs"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsCapacityQuotaSfsResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_list_zone(self, request: V4HpfsListZoneRequest) -> V4HpfsListZoneResponse:
        """查询一个地域下的所有支持并行文件的可用区及该可用区所支持的文件系统类型"""
        url = f"{self.endpoint}/v4/hpfs/list-zone"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsListZoneResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_list_region(self, request: V4HpfsListRegionRequest) -> V4HpfsListRegionResponse:
        """查询并行文件支持的地域"""
        url = f"{self.endpoint}/v4/hpfs/list-region"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsListRegionResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_dataflow_quota_sfs(self, request: V4HpfsDataflowQuotaSfsRequest) -> V4HpfsDataflowQuotaSfsResponse:
        """查询指定并行文件下数据流动策略配额的总量，已使用数量，剩余数量"""
        url = f"{self.endpoint}/v4/hpfs/dataflow-quota-sfs"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsDataflowQuotaSfsResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_count_quota_sfs(self, request: V4HpfsCountQuotaSfsRequest) -> V4HpfsCountQuotaSfsResponse:
        """根据资源池ID查询用户在该资源池的并行文件数量配额总量、已使用数量、剩余数量"""
        url = f"{self.endpoint}/v4/hpfs/count-quota-sfs"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsCountQuotaSfsResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_info_directory(self, request: V4HpfsInfoDirectoryRequest) -> V4HpfsInfoDirectoryResponse:
        """查询指定文件系统的指定目录信息"""
        url = f"{self.endpoint}/v4/hpfs/info-directory"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsInfoDirectoryResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_list_sfs_by_sfstype(self, request: V4HpfsListSfsBySfstypeRequest) -> V4HpfsListSfsBySfstypeResponse:
        """查询指定存储类型的并行文件列表"""
        url = f"{self.endpoint}/v4/hpfs/list-sfs-by-sfstype"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsListSfsBySfstypeResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_list_label_by_sfs(self, request: V4HpfsListLabelBySfsRequest) -> V4HpfsListLabelBySfsResponse:
        """查询指定并行文件绑定的标签。"""
        url = f"{self.endpoint}/v4/hpfs/list-label-by-sfs"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsListLabelBySfsResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_list_sfs_by_label(self, request: V4HpfsListSfsByLabelRequest) -> V4HpfsListSfsByLabelResponse:
        """资源池 ID 下，根据标签key、value查询并行文件列表"""
        url = f"{self.endpoint}/v4/hpfs/list-sfs-by-label"
        method = 'POST'
        try:
            headers = request.get_headers() or {} 
            body = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                body=body
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsListSfsByLabelResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_list_cluster_by_device(self, request: V4HpfsListClusterByDeviceRequest) -> V4HpfsListClusterByDeviceResponse:
        """通过裸金属设备规格，查询对应资源池 ID 下集群列表"""
        url = f"{self.endpoint}/v4/hpfs/list-cluster-by-device"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsListClusterByDeviceResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))

    def v4_hpfs_list_sfs_by_cluster(self, request: V4HpfsListSfsByClusterRequest) -> V4HpfsListSfsByClusterResponse:
        """查询指定集群的并行文件列表"""
        url = f"{self.endpoint}/v4/hpfs/list-sfs-by-cluster"
        method = 'GET'
        try:
            headers = request.get_headers() or {} 
            params = request.to_dict()
            response = self.ctyun_client.request(
                url=url,
                method=method,
                credential=self.credential,
                headers=headers,
                params=params
            ) 
            return self.ctyun_client.handle_response(response, V4HpfsListSfsByClusterResponse)
        except Exception as e:
            raise CtyunRequestException(str(e))



