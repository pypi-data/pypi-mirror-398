from typing import List

from .wallaroo_ml_ops_api_client.models.edge import Edge as MLOpsEdge


class Edge(MLOpsEdge):
    @classmethod
    def from_dict(self, data):
        edge = super().from_dict(data)

        # Let's set additional properties from publish so we can use them as attributes
        if edge.additional_properties:
            edge.__dict__.update(edge.additional_properties)

        return edge

    def _repr_html_(self):
        html = f"""
        <tr><th>Key</th><th>Value</th></tr>
        <tr><td>ID</td><td>{self.id}</td></tr>
        <tr><td>Name</td><td>{self.name}</td></tr>
        <tr><td>Tags</td><td>{self.tags}</td></tr>
        <tr><td>CPUs</td><td>{self.cpus}</td></tr>
        <tr><td>Memory</td><td>{self.memory}</td></tr>
        <tr><td>SPIFFE ID</td><td>{self.spiffe_id}</td></tr>
        <tr><td>Publish Id</td><td>{self.should_run_publish}</td></tr>
    """
        if self.additional_properties:
            html += f"""
            <tr><td>Created At</td><td>{self.created_at}</td></tr>
            <tr><td>Created On Version</td><td>{self.created_on_version}</td></tr>
            <tr><td>Pipeline Name</td><td>{self.pipeline_name}</td></tr>
            <tr><td>Pipeline Version</td><td>{self.pipeline_version_name}</td></tr>
            <tr><td>Workspace Id</td><td>{self.workspace_id}</td></tr>
            <tr><td>Workspace Name</td><td>{self.workspace_name}</td></tr>
            <tr>
                    <td>Docker Run Command</td>
                    <td>
                        <table>{self.docker_run}</table>
                        <br />
                        <i>
                            Note: Please set the {self.additional_envs}<code>EDGE_PORT</code>, <code>OCI_USERNAME</code>, and <code>OCI_PASSWORD</code> environment variables.
                        </i>
                    </td>
                </tr>
                <tr>
                    <td>Helm Install Command</td>
                    <td>
                        <table>{self.helm_install}</table>
                        <br />
                        <i>
                            Note: Please set the <code>HELM_INSTALL_NAME</code>, <code>HELM_INSTALL_NAMESPACE</code>,
                            <code>OCI_USERNAME</code>, and <code>OCI_PASSWORD</code> environment variables.
                        </i>
                    </td>
                </tr>
                """
        return f"<table>{html}</table>"


class EdgeList(List[Edge]):
    def _repr_html_(self) -> str:
        def row(edge: Edge):
            html = f"""
                <td>{edge.id}</td>
                <td>{edge.name}</td>
                <td>{edge.should_run_publish}</td>
                <td>{edge.created_at}</td>
                <td>{edge.tags}</td>
                <td>{edge.cpus}</td>
                <td>{edge.memory}</td>
                <td>{edge.spiffe_id}</td>
            """
            if edge.additional_properties:
                html += f"""
                    <td>{getattr(edge, 'pipeline_name', '')}</td>   
                    <td>{getattr(edge, 'pipeline_version_name', '')}</td>
                    <td>{getattr(edge, 'workspace_id', '')}</td>
                    <td>{getattr(edge, 'workspace_name', '')}</td>
                """
            return "<tr>" + html + "</tr>"

        fields = [
            "ID",
            "Name",
            "Publish ID",
            "Created At",
            "Tags",
            "CPUs",
            "Memory",
            "SPIFFE ID",
        ]
        if self and self[0].additional_properties:
            fields.extend(
                [
                    "Pipeline Name",
                    "Pipeline Version",
                    "Workspace ID",
                    "Workspace Name",
                ]
            )

        if self == []:
            return "(No Edges)"
        else:
            return (
                "<table>"
                + "<tr><th>"
                + "</th><th>".join(fields)
                + "</th></tr>"
                + ("".join([row(p) for p in self]))
                + "</table>"
            )
