"""
LibreNMS MCP Server Tools
"""

from typing import Annotated
from typing import Any
from urllib.parse import quote

from fastmcp import Context
from pydantic import Field

from librenms_mcp.librenms_client import LibreNMSClient


def register_tools(mcp, config):
    """Register LibreNMS tools with the MCP server"""

    ##########################
    # Alert Tools
    ##########################

    @mcp.tool(
        tags={"librenms", "alert", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def alerts_get(
        state: Annotated[
            int | None,
            Field(
                default=None,
                description="Filter the alerts by state: 0 = ok, 1 = alert, 2 = ack. Optional.",
            ),
        ] = None,
        severity: Annotated[
            str | None,
            Field(
                default=None,
                description="Filter the alerts by severity. Valid values: ok, warning, critical. Optional.",
            ),
        ] = None,
        alert_rule: Annotated[
            int | None,
            Field(
                default=None, description="Filter alerts by alert rule ID. Optional."
            ),
        ] = None,
        order: Annotated[
            str | None,
            Field(
                default=None,
                description="How to order the output, default is by timestamp (descending). Can be appended by DESC or ASC to change the order. Optional.",
            ),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """
        Get alerts from LibreNMS with optional filters.

        Args:
            state (int, optional): Filter the alerts by state: 0 = ok, 1 = alert, 2 = ack.
            severity (str, optional): Filter the alerts by severity. Valid values: ok, warning, critical.
            alert_rule (int, optional): Filter alerts by alert rule ID.
            order (str, optional): How to order the output, default is by timestamp (descending). Can be appended by DESC or ASC.

        Returns:
            dict: The JSON response from the API.
        """
        params: dict[str, Any] = {}
        if state is not None:
            params["state"] = state
        if severity is not None:
            params["severity"] = severity
        if alert_rule is not None:
            params["alert_rule"] = alert_rule
        if order is not None:
            params["order"] = order

        try:
            await ctx.info("Retrieving alerts...")

            async with LibreNMSClient(config) as client:
                return await client.get("alerts", params=params)

        except Exception as e:
            await ctx.error(f"Error retrieving alerts: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "alert", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def alert_get_by_id(
        alert_id: Annotated[
            int,
            Field(description="The ID of the alert to retrieve.", ge=1),
        ],
        ctx: Context = None,
    ) -> dict:
        """
        Get a specific alert from LibreNMS by ID.

        Args:
            alert_id (int): The ID of the alert to retrieve.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Retrieving alert {alert_id}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"alerts/{alert_id}")

        except Exception as e:
            await ctx.error(f"Error retrieving alert {alert_id}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "alert"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def alert_acknowledge(
        alert_id: Annotated[int, Field(ge=1, description="Alert ID to acknowledge")],
        ctx: Context = None,
    ) -> dict:
        """
        Acknowledge an alert in LibreNMS by ID.

        Args:
            alert_id (int): Alert ID to acknowledge.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Acknowledging alert {alert_id}")

            async with LibreNMSClient(config) as client:
                return await client.put(f"alerts/{alert_id}")

        except Exception as e:
            await ctx.error(f"Error acknowledging alert {alert_id}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "alert"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def alert_unmute(
        alert_id: Annotated[int, Field(ge=1, description="Alert ID to unmute")],
        ctx: Context = None,
    ) -> dict:
        """
        Unmute an alert in LibreNMS by ID.

        Args:
            alert_id (int): Alert ID to unmute.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Unmuting alert {alert_id}")

            async with LibreNMSClient(config) as client:
                return await client.put(f"alerts/unmute/{alert_id}")

        except Exception as e:
            await ctx.error(f"Error unmuting alert {alert_id}: {e!s}")
            return {"error": str(e)}

    ##########################
    # Alert Rules
    ##########################

    @mcp.tool(
        tags={"librenms", "alert-rules", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def alert_rules_list(ctx: Context = None) -> dict:
        """
        List all alert rules from LibreNMS.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Listing all alert rules...")

            async with LibreNMSClient(config) as client:
                return await client.get("rules")

        except Exception as e:
            await ctx.error(f"Error listing rules: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "alert-rules", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def alert_rule_get(
        rule_id: Annotated[int, Field(ge=1, description="Alert rule ID")],
        ctx: Context = None,
    ) -> dict:
        """
        Get details for a specific alert rule by ID.

        Args:
            rule_id (int): Alert rule ID.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting details for rule {rule_id}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"rules/{rule_id}")

        except Exception as e:
            await ctx.error(f"Error getting rule {rule_id}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "alert-rules"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
        },
    )
    async def alert_rule_add(
        payload: Annotated[dict, Field(description="Alert rule definition payload")],
        ctx: Context = None,
    ) -> dict:
        """
        Add a new alert rule to LibreNMS.

        Args:
            payload (dict): Alert rule definition payload.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Adding new alert rule...")

            async with LibreNMSClient(config) as client:
                return await client.post("rules", data=payload)

        except Exception as e:
            await ctx.error(f"Error adding rule: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "alert-rules"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        },
    )
    async def alert_rule_edit(
        payload: Annotated[
            dict, Field(description="Edited alert rule payload (must include ID)")
        ],
        ctx: Context = None,
    ) -> dict:
        """
        Edit an existing alert rule in LibreNMS.

        Args:
            payload (dict): Edited alert rule payload (must include ID).

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Editing rule {payload.get('id')}...")

            async with LibreNMSClient(config) as client:
                return await client.put("rules", data=payload)

        except Exception as e:
            await ctx.error(f"Error editing rule: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "alert-rules"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        },
    )
    async def alert_rule_delete(
        rule_id: Annotated[int, Field(ge=1, description="Alert rule ID to delete")],
        ctx: Context = None,
    ) -> dict:
        """
        Delete an alert rule from LibreNMS by ID.

        Args:
            rule_id (int): Alert rule ID to delete.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Deleting rule {rule_id}...")

            async with LibreNMSClient(config) as client:
                return await client.delete(f"rules/{rule_id}")

        except Exception as e:
            await ctx.error(f"Error deleting rule {rule_id}: {e!s}")
            return {"error": str(e)}

    ##########################
    # ARP
    ##########################

    @mcp.tool(
        tags={"librenms", "arp", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def arp_search(
        query: Annotated[
            str, Field(description="Search string for ARP entries (MAC/IP/partial)")
        ],
        ctx: Context = None,
    ) -> dict:
        """
        Retrieve ARP entries from LibreNMS by search query.

        Args:
            query (str): Search string for ARP entries (MAC/IP/partial).

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Searching ARP entries with query: {query}")

            async with LibreNMSClient(config) as client:
                return await client.get(f"resources/ip/arp/{query}")

        except Exception as e:
            await ctx.error(f"Error ARP search {query}: {e!s}")
            return {"error": str(e)}

    ##########################
    # Bills (read endpoints + write)
    ##########################

    @mcp.tool(
        tags={"librenms", "bills", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def bills_list(
        period: Annotated[
            str | None,
            Field(
                default=None,
                description="Optional: previous to list previous period bills",
            ),
        ] = None,
        ref: Annotated[
            str | None, Field(default=None, description="Bill reference filter")
        ] = None,
        custid: Annotated[
            str | None, Field(default=None, description="Customer ID filter")
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """
        List bills from LibreNMS with optional filters.

        Args:
            period (str, optional): List previous period bills.
            ref (str, optional): Bill reference filter.
            custid (str, optional): Customer ID filter.

        Returns:
            dict: The JSON response from the API.
        """
        params: dict[str, Any] = {}
        if period is not None:
            params["period"] = period
        if ref is not None:
            params["ref"] = ref
        if custid is not None:
            params["custid"] = custid

        try:
            await ctx.info("Listing bills...")

            async with LibreNMSClient(config) as client:
                return await client.get("bills", params=params or None)

        except Exception as e:
            await ctx.error(f"Error listing bills: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "bills", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def bill_get(
        bill_id: Annotated[int, Field(ge=1, description="Bill ID")],
        period: Annotated[
            str | None, Field(default=None, description="Optional period=previous")
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """
        Get a specific bill from LibreNMS by ID.

        Args:
            bill_id (int): Bill ID.
            period (str, optional): Optional period=previous.

        Returns:
            dict: The JSON response from the API.
        """
        params: dict[str, Any] = {}
        if period is not None:
            params["period"] = period

        try:
            await ctx.info(f"Getting bill {bill_id}...")
            async with LibreNMSClient(config) as client:
                return await client.get(f"bills/{bill_id}", params=params)

        except Exception as e:
            await ctx.error(f"Error getting bill {bill_id}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "bills", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def bill_graph(
        bill_id: Annotated[int, Field(ge=1)],
        graph_type: Annotated[str, Field(description="Graph type, e.g. bits")],
        ctx: Context = None,
    ) -> dict:
        """
        Get bill graph image from LibreNMS.

        Args:
            bill_id (int): Bill ID.
            graph_type (str): Graph type, e.g. bits.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting bill graph {bill_id}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"bills/{bill_id}/graphs/{graph_type}")

        except Exception as e:
            await ctx.error(f"Error bill graph {bill_id}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "bills", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def bill_graph_data(
        bill_id: Annotated[int, Field(ge=1)],
        graph_type: Annotated[str, Field(description="Graph type")],
        ctx: Context = None,
    ) -> dict:
        """
        Get bill graph data from LibreNMS.

        Args:
            bill_id (int): Bill ID.
            graph_type (str): Graph type.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting bill graph data {bill_id}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"bills/{bill_id}/graphdata/{graph_type}")

        except Exception as e:
            await ctx.error(f"Error bill graph data {bill_id}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "bills", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def bill_history(
        bill_id: Annotated[int, Field(ge=1)],
        ctx: Context = None,
    ) -> dict:
        """
        Get bill history from LibreNMS.

        Args:
            bill_id (int): Bill ID.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting bill history {bill_id}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"bills/{bill_id}/history")

        except Exception as e:
            await ctx.error(f"Error bill history {bill_id}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "bills", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def bill_history_graph(
        bill_id: Annotated[int, Field(ge=1)],
        history_id: Annotated[int, Field(ge=1, description="Bill history ID")],
        graph_type: Annotated[str, Field(description="Graph type")],
        ctx: Context = None,
    ) -> dict:
        """
        Get bill history graph from LibreNMS.

        Args:
            bill_id (int): Bill ID.
            history_id (int): Bill history ID.
            graph_type (str): Graph type.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting bill history graph {bill_id}...")

            async with LibreNMSClient(config) as client:
                return await client.get(
                    f"bills/{bill_id}/history/{history_id}/graphs/{graph_type}"
                )

        except Exception as e:
            await ctx.error(f"Error bill history graph {bill_id}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "bills", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def bill_history_graph_data(
        bill_id: Annotated[int, Field(ge=1)],
        history_id: Annotated[int, Field(ge=1)],
        graph_type: Annotated[str, Field()],
        ctx: Context = None,
    ) -> dict:
        """
        Get bill history graph data from LibreNMS.

        Args:
            bill_id (int): Bill ID.
            history_id (int): Bill history ID.
            graph_type (str): Graph type.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting bill history graph data {bill_id}...")

            async with LibreNMSClient(config) as client:
                return await client.get(
                    f"bills/{bill_id}/history/{history_id}/graphdata/{graph_type}"
                )

        except Exception as e:
            await ctx.error(f"Error bill history graph data {bill_id}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "bills"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
        },
    )
    async def bill_create_or_update(
        payload: Annotated[dict, Field(description="Bill payload (create/update)")],
        ctx: Context = None,
    ) -> dict:
        """
        Create or update a bill in LibreNMS.

        Args:
            payload (dict): Bill payload (create/update).

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Creating/updating bill...")

            async with LibreNMSClient(config) as client:
                return await client.post("bills", data=payload)

        except Exception as e:
            await ctx.error(f"Error creating/updating bill: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "bills"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        },
    )
    async def bill_delete(
        bill_id: Annotated[int, Field(ge=1, description="Bill ID to delete")],
        ctx: Context = None,
    ) -> dict:
        """
        Delete a bill from LibreNMS by ID.

        Args:
            bill_id (int): Bill ID to delete.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Deleting bill {bill_id}...")

            async with LibreNMSClient(config) as client:
                return await client.delete(f"bills/{bill_id}")

        except Exception as e:
            await ctx.error(f"Error deleting bill {bill_id}: {e!s}")
            return {"error": str(e)}

    ##########################
    # Device Groups
    ##########################
    @mcp.tool(
        tags={"librenms", "device-groups", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def devicegroups_list(ctx: Context = None) -> dict:
        """
        List all device groups from LibreNMS.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Getting device groups...")

            async with LibreNMSClient(config) as client:
                return await client.get("devicegroups")

        except Exception as e:
            await ctx.error(f"Error listing device groups: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "device-groups"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
        },
    )
    async def devicegroup_add(
        payload: Annotated[dict, Field(description="Device group definition payload")],
        ctx: Context = None,
    ) -> dict:
        """
        Add a new device group to LibreNMS.

        Args:
            payload (dict): Device group definition payload.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Creating/updating device group...")

            async with LibreNMSClient(config) as client:
                return await client.post("devicegroups", data=payload)

        except Exception as e:
            await ctx.error(f"Error adding device group: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "device-groups"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        },
    )
    async def devicegroup_update(
        name: Annotated[str, Field(description="Device group name")],
        payload: Annotated[dict, Field(description="Patch payload")],
        ctx: Context = None,
    ) -> dict:
        """
        Update a device group in LibreNMS.

        Args:
            name (str): Device group name.
            payload (dict): Patch payload.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Updating device group {name}...")

            async with LibreNMSClient(config) as client:
                return await client.put(f"devicegroups/{name}", data=payload)

        except Exception as e:
            await ctx.error(f"Error updating device group {name}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "device-groups"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        },
    )
    async def devicegroup_delete(
        name: Annotated[str, Field(description="Device group name to delete")],
        ctx: Context = None,
    ) -> dict:
        """
        Delete a device group from LibreNMS by name.

        Args:
            name (str): Device group name to delete.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Deleting device group {name}...")

            async with LibreNMSClient(config) as client:
                return await client.delete(f"devicegroups/{name}")

        except Exception as e:
            await ctx.error(f"Error deleting device group {name}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "device-groups", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def devicegroup_devices(
        name: Annotated[str, Field(description="Device group name")],
        ctx: Context = None,
    ) -> dict:
        """
        List devices in a device group from LibreNMS.

        Args:
            name (str): Device group name.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Listing devices in group {name}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"devicegroups/{name}")

        except Exception as e:
            await ctx.error(f"Error listing devices in group {name}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "device-groups"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        },
    )
    async def devicegroup_set_maintenance(
        name: Annotated[str, Field()],
        payload: Annotated[dict, Field(description="Maintenance payload")],
        ctx: Context = None,
    ) -> dict:
        """
        Set maintenance for a device group in LibreNMS.

        Args:
            name (str): Device group name.
            payload (dict): Maintenance payload.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Setting maintenance for group {name}...")

            async with LibreNMSClient(config) as client:
                return await client.post(
                    f"devicegroups/{name}/maintenance", data=payload
                )

        except Exception as e:
            await ctx.error(f"Error setting maintenance for group {name}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "device-groups"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
        },
    )
    async def devicegroup_add_devices(
        name: Annotated[str, Field()],
        payload: Annotated[dict, Field(description="Device IDs/hostnames to add")],
        ctx: Context = None,
    ) -> dict:
        """
        Add devices to a device group in LibreNMS.

        Args:
            name (str): Device group name.
            payload (dict): Device IDs/hostnames to add.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Adding devices to group {name}...")

            async with LibreNMSClient(config) as client:
                return await client.post(f"devicegroups/{name}/devices", data=payload)

        except Exception as e:
            await ctx.error(f"Error adding devices to group {name}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "device-groups"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
        },
    )
    async def devicegroup_remove_devices(
        name: Annotated[str, Field()],
        payload: Annotated[dict, Field(description="Device IDs/hostnames to remove")],
        ctx: Context = None,
    ) -> dict:
        """
        Remove devices from a device group in LibreNMS.

        Args:
            name (str): Device group name.
            payload (dict): Device IDs/hostnames to remove.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Removing devices from group {name}...")

            async with LibreNMSClient(config) as client:
                return await client.delete(
                    f"devicegroups/{name}/devices", params=payload
                )

        except Exception as e:
            await ctx.error(f"Error removing devices from group {name}: {e!s}")
            return {"error": str(e)}

    ##########################
    # Devices (subset of most-used endpoints)
    ##########################
    @mcp.tool(
        tags={"librenms", "devices", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def devices_list(
        query: Annotated[
            dict | None,
            Field(
                default=None,
                description="Optional query parameters (limit, type, etc.)",
            ),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """
        List devices from LibreNMS.

        Args:
            query (dict, optional): Optional query parameters (limit, type, etc.).

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Listing devices...")

            async with LibreNMSClient(config) as client:
                return await client.get("devices", params=query)

        except Exception as e:
            await ctx.error(f"Error listing devices: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "devices"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
        },
    )
    async def device_add(
        payload: Annotated[
            dict, Field(description="Device add payload (hostname, community, etc.)")
        ],
        ctx: Context = None,
    ) -> dict:
        """
        Add a new device to LibreNMS.

        Args:
            payload (dict): Device add payload (hostname, community, etc.).

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Adding device...")

            async with LibreNMSClient(config) as client:
                return await client.post("devices", data=payload)

        except Exception as e:
            await ctx.error(f"Error adding device: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "devices", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def device_get(
        hostname: Annotated[str, Field(description="Device hostname")],
        ctx: Context = None,
    ) -> dict:
        """
        Get device details from LibreNMS by hostname.

        Args:
            hostname (str): Device hostname.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting device {hostname}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"devices/{hostname}")

        except Exception as e:
            await ctx.error(f"Error getting device {hostname}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "devices"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        },
    )
    async def device_delete(
        hostname: Annotated[str, Field(description="Device hostname to delete")],
        ctx: Context = None,
    ) -> dict:
        """
        Delete a device from LibreNMS by hostname.

        Args:
            hostname (str): Device hostname to delete.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Deleting device {hostname}...")

            async with LibreNMSClient(config) as client:
                return await client.delete(f"devices/{hostname}")

        except Exception as e:
            await ctx.error(f"Error deleting device {hostname}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "devices"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        },
    )
    async def device_update(
        hostname: Annotated[str, Field()],
        payload: Annotated[dict, Field(description="Patch fields for device")],
        ctx: Context = None,
    ) -> dict:
        """
        Update device fields in LibreNMS.

        Args:
            hostname (str): Device hostname.
            payload (dict): Patch fields for device.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Updating device {hostname}...")

            async with LibreNMSClient(config) as client:
                return await client.put(f"devices/{hostname}", data=payload)

        except Exception as e:
            await ctx.error(f"Error updating device {hostname}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "devices", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def device_ports(
        hostname: Annotated[str, Field()], ctx: Context = None
    ) -> dict:
        """
        List ports for a device from LibreNMS.

        Args:
            hostname (str): Device hostname.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Listing ports for {hostname}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"devices/{hostname}/ports")

        except Exception as e:
            await ctx.error(f"Error listing ports for {hostname}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "devices", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def device_ports_get(
        hostname: Annotated[str, Field()],
        ifname: Annotated[str, Field(description="Interface name")],
        ctx: Context = None,
    ) -> dict:
        """
        Get port info for a device by interface name.

        Args:
            hostname (str): Device hostname.
            ifname (str): Interface name.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting port {ifname} on {hostname}...")

            async with LibreNMSClient(config) as client:
                return await client.get(
                    f"devices/{hostname}/ports/{quote(ifname, safe='')}"
                )

        except Exception as e:
            await ctx.error(f"Error getting port {ifname} on {hostname}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "devices", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def device_availability(
        hostname: Annotated[str, Field()], ctx: Context = None
    ) -> dict:
        """
        Get device availability from LibreNMS.

        Args:
            hostname (str): Device hostname.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting availability for {hostname}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"devices/{hostname}/availability")

        except Exception as e:
            await ctx.error(f"Error availability {hostname}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "devices", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def device_outages(
        hostname: Annotated[str, Field()], ctx: Context = None
    ) -> dict:
        """
        Get device outages from LibreNMS.

        Args:
            hostname (str): Device hostname.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting outages for {hostname}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"devices/{hostname}/outages")

        except Exception as e:
            await ctx.error(f"Error outages {hostname}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "devices"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def device_set_maintenance(
        hostname: Annotated[str, Field()],
        payload: Annotated[dict, Field(description="Maintenance payload")],
        ctx: Context = None,
    ) -> dict:
        """
        Set device maintenance in LibreNMS.

        Args:
            hostname (str): Device hostname.
            payload (dict): Maintenance payload.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Setting maintenance for {hostname}...")

            async with LibreNMSClient(config) as client:
                return await client.post(
                    f"devices/{hostname}/maintenance", data=payload
                )

        except Exception as e:
            await ctx.error(f"Error setting maintenance {hostname}: {e!s}")
            return {"error": str(e)}

    ##########################
    # Inventory
    ##########################
    @mcp.tool(
        tags={"librenms", "inventory", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def inventory_device(
        hostname: Annotated[str, Field()], ctx: Context = None
    ) -> dict:
        """
        Get inventory for a device from LibreNMS.

        Args:
            hostname (str): Device hostname.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting inventory for {hostname}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"inventory/{hostname}")

        except Exception as e:
            await ctx.error(f"Error inventory {hostname}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "inventory", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def inventory_device_flat(
        hostname: Annotated[str, Field()], ctx: Context = None
    ) -> dict:
        """
        Get flattened inventory for a device from LibreNMS.

        Args:
            hostname (str): Device hostname.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting flattened inventory for {hostname}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"inventory/{hostname}/all")

        except Exception as e:
            await ctx.error(f"Error inventory flat {hostname}: {e!s}")
            return {"error": str(e)}

    ##########################
    # Locations
    ##########################
    @mcp.tool(
        tags={"librenms", "locations", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def locations_list(ctx: Context = None) -> dict:
        """
        List locations from LibreNMS.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Listing locations...")

            async with LibreNMSClient(config) as client:
                return await client.get("resources/locations")

        except Exception as e:
            await ctx.error(f"Error listing locations: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "locations"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
        },
    )
    async def location_add(
        payload: Annotated[dict, Field(description="Location payload")],
        ctx: Context = None,
    ) -> dict:
        """
        Add a new location to LibreNMS.

        Args:
            payload (dict): Location payload.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Adding location...")

            async with LibreNMSClient(config) as client:
                return await client.post("locations", data=payload)

        except Exception as e:
            await ctx.error(f"Error adding location: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "locations"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        },
    )
    async def location_delete(
        location: Annotated[str, Field(description="Location identifier")],
        ctx: Context = None,
    ) -> dict:
        """
        Delete a location from LibreNMS by identifier.

        Args:
            location (str): Location identifier.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Deleting location {location}...")

            async with LibreNMSClient(config) as client:
                return await client.delete(f"locations/{location}")

        except Exception as e:
            await ctx.error(f"Error deleting location {location}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "locations"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        },
    )
    async def location_edit(
        location: Annotated[str, Field()],
        payload: Annotated[dict, Field(description="Location patch payload")],
        ctx: Context = None,
    ) -> dict:
        """
        Edit a location in LibreNMS.

        Args:
            location (str): Location identifier.
            payload (dict): Location patch payload.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Editing location {location}...")

            async with LibreNMSClient(config) as client:
                return await client.put(f"locations/{location}", data=payload)

        except Exception as e:
            await ctx.error(f"Error editing location {location}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "locations", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def location_get(
        location: Annotated[str, Field()], ctx: Context = None
    ) -> dict:
        """
        Get a specific location from LibreNMS by identifier.

        Args:
            location (str): Location identifier.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting location {location}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"location/{location}")

        except Exception as e:
            await ctx.error(f"Error getting location {location}: {e!s}")
            return {"error": str(e)}

    ##########################
    # Logs
    ##########################
    @mcp.tool(
        tags={"librenms", "logs", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def logs_eventlog(
        hostname: Annotated[str, Field()], ctx: Context = None
    ) -> dict:
        """
        Get event logs for a device from LibreNMS.

        Args:
            hostname (str): Device hostname.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting event logs for {hostname}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"logs/eventlog/{hostname}")

        except Exception as e:
            await ctx.error(f"Error eventlog {hostname}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "logs", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def logs_syslog(
        hostname: Annotated[str, Field()], ctx: Context = None
    ) -> dict:
        """
        Get syslogs for a device from LibreNMS.

        Args:
            hostname (str): Device hostname.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting syslogs for {hostname}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"logs/syslog/{hostname}")

        except Exception as e:
            await ctx.error(f"Error syslog {hostname}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "logs", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def logs_alertlog(
        hostname: Annotated[str, Field()], ctx: Context = None
    ) -> dict:
        """
        Get alert logs for a device from LibreNMS.

        Args:
            hostname (str): Device hostname.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting alert logs for {hostname}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"logs/alertlog/{hostname}")

        except Exception as e:
            await ctx.error(f"Error alertlog {hostname}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "logs", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def logs_authlog(
        hostname: Annotated[str, Field()], ctx: Context = None
    ) -> dict:
        """
        Get auth logs for a device from LibreNMS.

        Args:
            hostname (str): Device hostname.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting auth logs for {hostname}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"logs/authlog/{hostname}")

        except Exception as e:
            await ctx.error(f"Error authlog {hostname}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "logs"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
        },
    )
    async def logs_syslogsink(
        payload: Annotated[dict, Field(description="Syslog sink payload")],
        ctx: Context = None,
    ) -> dict:
        """
        Add a syslog sink to LibreNMS.

        Args:
            payload (dict): Syslog sink payload.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Adding syslog sink...")

            async with LibreNMSClient(config) as client:
                return await client.post("logs/syslogsink", data=payload)

        except Exception as e:
            await ctx.error(f"Error syslogsink: {e!s}")
            return {"error": str(e)}

    ##########################
    # Poller Groups
    ##########################
    @mcp.tool(
        tags={"librenms", "poller-groups", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def poller_group_get(
        poller_group: Annotated[
            str, Field(description="Poller group identifier or 'all'")
        ],
        ctx: Context = None,
    ) -> dict:
        """
        Get poller group(s) from LibreNMS.

        Args:
            poller_group (str): Poller group identifier or 'all'.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting poller group {poller_group}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"poller_group/{poller_group}")

        except Exception as e:
            await ctx.error(f"Error poller group {poller_group}: {e!s}")
            return {"error": str(e)}

    ##########################
    # Port Groups
    ##########################
    @mcp.tool(
        tags={"librenms", "port-groups", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def port_groups_list(ctx: Context = None) -> dict:
        """
        List port groups from LibreNMS.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Getting port groups...")

            async with LibreNMSClient(config) as client:
                return await client.get("port_groups")

        except Exception as e:
            await ctx.error(f"Error listing port groups: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "port-groups"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
        },
    )
    async def port_group_add(
        payload: Annotated[dict, Field(description="Port group payload")],
        ctx: Context = None,
    ) -> dict:
        """
        Add a port group to LibreNMS.

        Args:
            payload (dict): Port group payload.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Adding port group...")

            async with LibreNMSClient(config) as client:
                return await client.post("port_groups", data=payload)

        except Exception as e:
            await ctx.error(f"Error adding port group: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "port-groups", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def port_group_list_ports(
        name: Annotated[str, Field(description="Port group name")], ctx: Context = None
    ) -> dict:
        """
        List ports in a port group from LibreNMS.

        Args:
            name (str): Port group name.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting ports in group {name}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"port_groups/{name}")

        except Exception as e:
            await ctx.error(f"Error listing ports in group {name}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "port-groups"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
        },
    )
    async def port_group_assign(
        port_group_id: Annotated[int, Field(ge=1)],
        payload: Annotated[dict, Field(description="Assignment payload")],
        ctx: Context = None,
    ) -> dict:
        """
        Assign a port group in LibreNMS.

        Args:
            port_group_id (int): Port group ID.
            payload (dict): Assignment payload.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Assigning ports to group {port_group_id}...")

            async with LibreNMSClient(config) as client:
                return await client.post(
                    f"port_groups/{port_group_id}/assign", data=payload
                )

        except Exception as e:
            await ctx.error(f"Error assigning port group {port_group_id}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "port-groups"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
        },
    )
    async def port_group_remove(
        port_group_id: Annotated[int, Field(ge=1)],
        payload: Annotated[dict, Field(description="Removal payload")],
        ctx: Context = None,
    ) -> dict:
        """
        Remove a port group in LibreNMS.

        Args:
            port_group_id (int): Port group ID.
            payload (dict): Removal payload.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Removing ports from group {port_group_id}...")

            async with LibreNMSClient(config) as client:
                return await client.post(
                    f"port_groups/{port_group_id}/remove", data=payload
                )

        except Exception as e:
            await ctx.error(f"Error removing port group {port_group_id}: {e!s}")
            return {"error": str(e)}

    ##########################
    # Ports
    ##########################
    @mcp.tool(
        tags={"librenms", "ports", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def ports_list(
        query: Annotated[
            dict | None,
            Field(
                default=None, description="Optional filters (limit, device_id, etc.)"
            ),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """
        Get all ports from LibreNMS.

        Args:
            query (dict, optional): Optional filters (limit, device_id, etc.).

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Getting all ports...")

            async with LibreNMSClient(config) as client:
                return await client.get("ports", params=query)

        except Exception as e:
            await ctx.error(f"Error listing ports: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "ports", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def ports_search(
        search: Annotated[str, Field(description="Search string")], ctx: Context = None
    ) -> dict:
        """
        Search ports in LibreNMS by search string.

        Args:
            search (str): Search string.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Searching ports {search}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"ports/search/{search}")

        except Exception as e:
            await ctx.error(f"Error searching ports {search}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "ports", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def ports_search_field(
        field: Annotated[str, Field(description="Field name")],
        search: Annotated[str, Field(description="Search term")],
        ctx: Context = None,
    ) -> dict:
        """
        Search ports in LibreNMS by field and search term.

        Args:
            field (str): Field name.
            search (str): Search term.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Searching ports {field}={search}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"ports/search/{field}/{search}")

        except Exception as e:
            await ctx.error(f"Error field search {field}={search}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "ports", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def ports_search_mac(
        mac: Annotated[str, Field(description="MAC address search")],
        ctx: Context = None,
    ) -> dict:
        """
        Search ports in LibreNMS by MAC address.

        Args:
            mac (str): MAC address search.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Searching ports by MAC address {mac}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"ports/mac/{mac}")

        except Exception as e:
            await ctx.error(f"Error MAC search {mac}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "ports", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def port_get(
        port_id: Annotated[int, Field(ge=1)], ctx: Context = None
    ) -> dict:
        """
        Get port info from LibreNMS by port ID.

        Args:
            port_id (int): Port ID.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting port {port_id}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"ports/{port_id}")

        except Exception as e:
            await ctx.error(f"Error port {port_id}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "ports", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def port_ip_info(
        port_id: Annotated[int, Field(ge=1)], ctx: Context = None
    ) -> dict:
        """
        Get port IP info from LibreNMS by port ID.

        Args:
            port_id (int): Port ID.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting port IP info {port_id}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"ports/{port_id}/ip")

        except Exception as e:
            await ctx.error(f"Error port IP {port_id}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "ports", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def port_transceiver(
        port_id: Annotated[int, Field(ge=1)], ctx: Context = None
    ) -> dict:
        """
        Get port transceiver info from LibreNMS by port ID.

        Args:
            port_id (int): Port ID.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting port transceiver info {port_id}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"ports/{port_id}/transceiver")

        except Exception as e:
            await ctx.error(f"Error transceiver {port_id}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "ports", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def port_description_get(
        port_id: Annotated[int, Field(ge=1)], ctx: Context = None
    ) -> dict:
        """
        Get port description from LibreNMS by port ID.

        Args:
            port_id (int): Port ID.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting port description {port_id}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"ports/{port_id}/description")

        except Exception as e:
            await ctx.error(f"Error description {port_id}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "ports"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        },
    )
    async def port_description_update(
        port_id: Annotated[int, Field(ge=1)],
        payload: Annotated[dict, Field(description="Description update payload")],
        ctx: Context = None,
    ) -> dict:
        """
        Update port description in LibreNMS by port ID.

        Args:
            port_id (int): Port ID.
            payload (dict): Description update payload.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Updating port description {port_id}...")

            async with LibreNMSClient(config) as client:
                return await client.put(f"ports/{port_id}/description", data=payload)

        except Exception as e:
            await ctx.error(f"Error updating description {port_id}: {e!s}")
            return {"error": str(e)}

    ##########################
    # Routing (subset)
    ##########################
    @mcp.tool(
        tags={"librenms", "routing", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def bgp_sessions(ctx: Context = None) -> dict:
        """
        List BGP sessions from LibreNMS.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Listing BGP sessions...")

            async with LibreNMSClient(config) as client:
                return await client.get("bgp")

        except Exception as e:
            await ctx.error(f"Error listing BGP sessions: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "routing", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def bgp_session_get(
        bgp_id: Annotated[int, Field(ge=1)], ctx: Context = None
    ) -> dict:
        """
        Get BGP session from LibreNMS by ID.

        Args:
            bgp_id (int): BGP session ID.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting BGP session {bgp_id}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"bgp/{bgp_id}")

        except Exception as e:
            await ctx.error(f"Error BGP session {bgp_id}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "routing"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        },
    )
    async def bgp_session_edit(
        bgp_id: Annotated[int, Field(ge=1)],
        payload: Annotated[dict, Field(description="BGP edit payload")],
        ctx: Context = None,
    ) -> dict:
        """
        Edit BGP session in LibreNMS by ID.

        Args:
            bgp_id (int): BGP session ID.
            payload (dict): BGP edit payload.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Editing BGP session {bgp_id}...")

            async with LibreNMSClient(config) as client:
                return await client.post(f"bgp/{bgp_id}", data=payload)

        except Exception as e:
            await ctx.error(f"Error editing BGP {bgp_id}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "routing", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def routing_ip_addresses(ctx: Context = None) -> dict:
        """
        List all IP addresses from LibreNMS.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Listing IP addresses...")

            async with LibreNMSClient(config) as client:
                return await client.get("resources/ip/addresses")

        except Exception as e:
            await ctx.error(f"Error listing IP addresses: {e!s}")
            return {"error": str(e)}

    ##########################
    # Services
    ##########################
    @mcp.tool(
        tags={"librenms", "services", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def services_list(ctx: Context = None) -> dict:
        """
        List all services from LibreNMS.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Listing services...")

            async with LibreNMSClient(config) as client:
                return await client.get("services")

        except Exception as e:
            await ctx.error(f"Error listing services: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "services", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def services_for_device(
        hostname: Annotated[str, Field()], ctx: Context = None
    ) -> dict:
        """
        Get services for a device from LibreNMS.

        Args:
            hostname (str): Device hostname.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Getting services for {hostname}...")

            async with LibreNMSClient(config) as client:
                return await client.get(f"services/{hostname}")

        except Exception as e:
            await ctx.error(f"Error services for {hostname}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "services"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
        },
    )
    async def service_add(
        hostname: Annotated[str, Field()],
        payload: Annotated[dict, Field(description="Service add payload")],
        ctx: Context = None,
    ) -> dict:
        """
        Add a service for a device in LibreNMS.

        Args:
            hostname (str): Device hostname.
            payload (dict): Service add payload.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Adding service for {hostname}...")

            async with LibreNMSClient(config) as client:
                return await client.post(f"services/{hostname}", data=payload)

        except Exception as e:
            await ctx.error(f"Error adding service {hostname}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "services"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        },
    )
    async def service_edit(
        service_id: Annotated[int, Field(ge=1)],
        payload: Annotated[dict, Field(description="Service edit payload")],
        ctx: Context = None,
    ) -> dict:
        """
        Edit a service in LibreNMS by service ID.

        Args:
            service_id (int): Service ID.
            payload (dict): Service edit payload.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Editing service {service_id}...")

            async with LibreNMSClient(config) as client:
                return await client.put(f"services/{service_id}", data=payload)

        except Exception as e:
            await ctx.error(f"Error editing service {service_id}: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "services"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        },
    )
    async def service_delete(
        service_id: Annotated[int, Field(ge=1)], ctx: Context = None
    ) -> dict:
        """
        Delete a service from LibreNMS by service ID.

        Args:
            service_id (int): Service ID.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info(f"Deleting service {service_id}...")

            async with LibreNMSClient(config) as client:
                return await client.delete(f"services/{service_id}")

        except Exception as e:
            await ctx.error(f"Error deleting service {service_id}: {e!s}")
            return {"error": str(e)}

    ##########################
    # Switching (subset)
    ##########################
    @mcp.tool(
        tags={"librenms", "switching", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def switching_vlans(ctx: Context = None) -> dict:
        """
        List all VLANs from LibreNMS.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Listing VLANs...")

            async with LibreNMSClient(config) as client:
                return await client.get("resources/vlans")

        except Exception as e:
            await ctx.error(f"Error listing VLANs: {e!s}")
            return {"error": str(e)}

    @mcp.tool(
        tags={"librenms", "switching", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def switching_links(ctx: Context = None) -> dict:
        """
        List all links from LibreNMS.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Listing links...")

            async with LibreNMSClient(config) as client:
                return await client.get("resources/links")

        except Exception as e:
            await ctx.error(f"Error listing links: {e!s}")
            return {"error": str(e)}

    ##########################
    # System
    ##########################
    @mcp.tool(
        tags={"librenms", "system", "read-only"},
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def system_info(ctx: Context = None) -> dict:
        """
        Get system info from LibreNMS.

        Returns:
            dict: The JSON response from the API.
        """
        try:
            await ctx.info("Getting system info...")

            async with LibreNMSClient(config) as client:
                return await client.get("system")

        except Exception as e:
            await ctx.error(f"Error system info: {e!s}")
            return {"error": str(e)}
