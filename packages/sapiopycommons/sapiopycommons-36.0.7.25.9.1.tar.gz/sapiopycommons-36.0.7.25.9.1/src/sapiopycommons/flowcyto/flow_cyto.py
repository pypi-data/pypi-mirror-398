from __future__ import annotations

from weakref import WeakValueDictionary

from databind.json import dumps
from sapiopylib.rest.User import SapioUser
from sapiopylib.rest.utils.singletons import SapioContextManager

from sapiopycommons.flowcyto.flowcyto_data import FlowJoWorkspaceInputJson, UploadFCSInputJson, \
    ComputeFlowStatisticsInputJson


class FlowCytoManager(SapioContextManager):
    """
    This manager includes flow cytometry analysis tools that would require FlowCyto license to use.
    """

    def create_flowjo_workspace(self, workspace_input: FlowJoWorkspaceInputJson) -> int:
        """
        Create FlowJo Workspace and return the workspace record ID of workspace root record,
        after successful creation.
        :param workspace_input: the request data payload.
        :return: The new workspace record ID.
        """
        payload = dumps(workspace_input, FlowJoWorkspaceInputJson)
        response = self._user.plugin_post("flowcyto/workspace", payload=payload, is_payload_plain_text=True)
        self._user.raise_for_status(response)
        return int(response.json())

    def upload_fcs_for_sample(self, upload_input: UploadFCSInputJson) -> int:
        """
        Upload FCS file as root of the sample FCS.
        :param upload_input: The request data payload
        :return: The root FCS file uploaded under sample.
        """
        payload = dumps(upload_input, UploadFCSInputJson)
        response = self._user.plugin_post("flowcyto/fcs", payload=payload, is_payload_plain_text=True)
        self._user.raise_for_status(response)
        return int(response.json())

    def compute_statistics(self, stat_compute_input: ComputeFlowStatisticsInputJson) -> list[int]:
        """
        Requests to compute flow cytometry statistics.
        The children are of type FCSStatistic.
        If the FCS files have not been evaluated yet,
        then the lazy evaluation will be performed immediately prior to computing statistics, which can take longer.
        If any new statistics are computed as children of FCS, they will be returned in the result record id list.
        Note: if input has multiple FCS files, the client should try to get parent FCS file from each record to figure out which one is for which FCS.
        :param stat_compute_input:
        :return:
        """
        payload = dumps(stat_compute_input, ComputeFlowStatisticsInputJson)
        response = self._user.plugin_post("flowcyto/statistics", payload=payload, is_payload_plain_text=True)
        self._user.raise_for_status(response)
        return list(response.json())
