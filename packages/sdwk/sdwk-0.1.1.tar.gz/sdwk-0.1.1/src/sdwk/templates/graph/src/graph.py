"""
图执行引擎 - 负责工作流图的执行和管理
"""
import asyncio
import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import networkx as nx

from .models import (
    NodeData, NodeResult, NodeStatus, GraphExecutionRequest,
    GraphExecutionResult, WorkflowConfig, NodeConfig, EdgeConfig
)
from .nodes import create_node, BaseNode


class GraphEngine:
    """
    图执行引擎

    负责加载工作流定义、构建执行图、管理节点执行顺序和并行处理
    """

    def __init__(self, workflow_path: Optional[Path] = None):
        """
        初始化图执行引擎

        Args:
            workflow_path: 工作流定义文件路径
        """
        self.workflow_config: Optional[WorkflowConfig] = None
        self.execution_graph: Optional[nx.DiGraph] = None
        self.nodes: Dict[str, BaseNode] = {}
        self.node_configs: Dict[str, NodeConfig] = {}
        self.edge_configs: List[EdgeConfig] = []

        if workflow_path:
            self.load_workflow(workflow_path)

    def load_workflow(self, workflow_path: Path) -> None:
        """
        加载工作流定义

        Args:
            workflow_path: 工作流定义文件路径

        Raises:
            FileNotFoundError: 工作流文件不存在
            ValueError: 工作流定义格式错误
        """
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")

        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)

            self.workflow_config = WorkflowConfig(**workflow_data)
            self._build_execution_graph()

        except Exception as e:
            raise ValueError(f"Failed to load workflow: {e}")

    def _build_execution_graph(self) -> None:
        """构建执行图"""
        if not self.workflow_config:
            raise ValueError("No workflow config loaded")

        # 创建有向图
        self.execution_graph = nx.DiGraph()

        # 添加节点
        for node_config in self.workflow_config.nodes:
            self.node_configs[node_config.id] = node_config
            self.nodes[node_config.id] = create_node(
                node_config.type,
                node_config.model_dump()
            )
            self.execution_graph.add_node(node_config.id)

        # 添加边
        for edge_config in self.workflow_config.edges:
            self.edge_configs.append(edge_config)
            self.execution_graph.add_edge(
                edge_config.from_node,
                edge_config.to_node,
                edge_config=edge_config
            )

        # 验证图的有效性
        self._validate_graph()

    def _validate_graph(self) -> None:
        """验证图的有效性"""
        if not self.execution_graph:
            raise ValueError("Execution graph not built")

        # 检查是否有环
        if not nx.is_directed_acyclic_graph(self.execution_graph):
            raise ValueError("Workflow contains cycles")

        # 检查是否有孤立节点
        isolated_nodes = list(nx.isolates(self.execution_graph))
        if isolated_nodes:
            raise ValueError(f"Isolated nodes found: {isolated_nodes}")

        # 检查入度为0的节点（起始节点）
        start_nodes = [node for node in self.execution_graph.nodes()
                      if self.execution_graph.in_degree(node) == 0]
        if not start_nodes:
            raise ValueError("No start nodes found")

        # 检查出度为0的节点（结束节点）
        end_nodes = [node for node in self.execution_graph.nodes()
                    if self.execution_graph.out_degree(node) == 0]
        if not end_nodes:
            raise ValueError("No end nodes found")

    async def execute(self, request: GraphExecutionRequest) -> GraphExecutionResult:
        """
        执行工作流图

        Args:
            request: 图执行请求

        Returns:
            GraphExecutionResult: 执行结果
        """
        if not self.execution_graph:
            raise ValueError("No workflow loaded")

        execution_id = str(uuid.uuid4())
        start_time = asyncio.get_event_loop().time()

        # 获取执行配置
        config = request.execution_config or {}
        max_parallel = config.get("max_parallel", 4)
        timeout = config.get("timeout", 300)

        # 初始化执行状态
        node_results: Dict[str, NodeResult] = {}
        node_outputs: Dict[str, NodeData] = {}
        completed_nodes: Set[str] = set()
        failed_nodes: Set[str] = set()

        try:
            # 确定起始节点
            start_node = request.start_node
            if not start_node:
                start_nodes = [node for node in self.execution_graph.nodes()
                              if self.execution_graph.in_degree(node) == 0]
                start_node = start_nodes[0] if start_nodes else None

            if not start_node:
                raise ValueError("No start node specified or found")

            # 初始化起始节点的输入数据
            node_outputs[start_node] = request.input_data

            # 执行图遍历
            await self._execute_graph(
                start_node, node_results, node_outputs,
                completed_nodes, failed_nodes, max_parallel, timeout
            )

            # 确定最终输出
            end_nodes = [node for node in self.execution_graph.nodes()
                        if self.execution_graph.out_degree(node) == 0]
            final_output = None
            if end_nodes and end_nodes[0] in node_outputs:
                final_output = node_outputs[end_nodes[0]]

            # 计算总执行时间
            total_time = asyncio.get_event_loop().time() - start_time

            # 确定整体状态
            overall_status = NodeStatus.SUCCESS
            if failed_nodes:
                overall_status = NodeStatus.FAILED
            elif len(completed_nodes) < len(self.execution_graph.nodes()):
                overall_status = NodeStatus.FAILED

            return GraphExecutionResult(
                execution_id=execution_id,
                status=overall_status,
                node_results=list(node_results.values()),
                final_output=final_output,
                total_execution_time=total_time,
                error_summary=self._generate_error_summary(failed_nodes, node_results)
            )

        except Exception as e:
            total_time = asyncio.get_event_loop().time() - start_time
            return GraphExecutionResult(
                execution_id=execution_id,
                status=NodeStatus.FAILED,
                node_results=list(node_results.values()),
                total_execution_time=total_time,
                error_summary=str(e)
            )

    async def _execute_graph(self, start_node: str, node_results: Dict[str, NodeResult],
                           node_outputs: Dict[str, NodeData], completed_nodes: Set[str],
                           failed_nodes: Set[str], max_parallel: int, timeout: float) -> None:
        """执行图遍历"""
        # 使用拓扑排序确定执行顺序
        execution_order = list(nx.topological_sort(self.execution_graph))

        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(max_parallel)

        # 跟踪正在执行的任务
        running_tasks: Dict[str, asyncio.Task] = {}

        for node_id in execution_order:
            # 检查前置条件
            if not await self._check_prerequisites(node_id, completed_nodes, failed_nodes):
                continue

            # 准备输入数据
            input_data = await self._prepare_node_input(node_id, node_outputs)
            if not input_data:
                continue

            # 创建并启动节点执行任务
            task = asyncio.create_task(
                self._execute_node_with_semaphore(
                    semaphore, node_id, input_data, timeout
                )
            )
            running_tasks[node_id] = task

        # 等待所有任务完成
        if running_tasks:
            results = await asyncio.gather(*running_tasks.values(), return_exceptions=True)

            for node_id, result in zip(running_tasks.keys(), results):
                if isinstance(result, Exception):
                    # 创建失败结果
                    node_results[node_id] = NodeResult(
                        node_id=node_id,
                        status=NodeStatus.FAILED,
                        error=str(result),
                        execution_time=0.0
                    )
                    failed_nodes.add(node_id)
                else:
                    node_results[node_id] = result
                    if result.status == NodeStatus.SUCCESS:
                        completed_nodes.add(node_id)
                        if result.data:
                            node_outputs[node_id] = result.data
                    else:
                        failed_nodes.add(node_id)

    async def _execute_node_with_semaphore(self, semaphore: asyncio.Semaphore,
                                         node_id: str, input_data: NodeData,
                                         timeout: float) -> NodeResult:
        """使用信号量执行节点"""
        async with semaphore:
            try:
                node = self.nodes[node_id]
                return await asyncio.wait_for(node.run(input_data), timeout=timeout)
            except asyncio.TimeoutError:
                raise Exception(f"Node {node_id} execution timeout")

    async def _check_prerequisites(self, node_id: str, completed_nodes: Set[str],
                                 failed_nodes: Set[str]) -> bool:
        """检查节点执行的前置条件"""
        # 获取前驱节点
        predecessors = list(self.execution_graph.predecessors(node_id))

        # 如果没有前驱节点，可以执行
        if not predecessors:
            return True

        # 检查所有前驱节点是否已完成
        for pred in predecessors:
            if pred not in completed_nodes:
                # 检查是否有失败的前驱节点
                if pred in failed_nodes:
                    # 根据错误处理策略决定是否继续
                    error_handling = self.workflow_config.error_handling or {}
                    node_specific = error_handling.get("node_specific", {})
                    if node_id in node_specific:
                        strategy = node_specific[node_id].get("strategy", "stop_on_error")
                        if strategy == "skip_and_continue":
                            continue
                    return False
                else:
                    return False

        return True

    async def _prepare_node_input(self, node_id: str, node_outputs: Dict[str, NodeData]) -> Optional[NodeData]:
        """准备节点输入数据"""
        predecessors = list(self.execution_graph.predecessors(node_id))

        # 如果没有前驱节点，使用空数据
        if not predecessors:
            return NodeData(data={}, metadata={}, node_id=node_id)

        # 合并前驱节点的输出
        merged_data = {}
        merged_metadata = {}

        for pred in predecessors:
            if pred in node_outputs:
                pred_output = node_outputs[pred]

                # 获取边配置进行数据映射
                edge_data = self.execution_graph.get_edge_data(pred, node_id)
                if edge_data and edge_data.get("edge_config"):
                    edge_config = edge_data["edge_config"]
                    data_mapping = edge_config.data_mapping or {}

                    # 应用数据映射
                    for source_key, target_key in data_mapping.items():
                        if source_key in pred_output.data:
                            merged_data[target_key] = pred_output.data[source_key]
                else:
                    # 默认合并所有数据
                    merged_data.update(pred_output.data)

                merged_metadata.update(pred_output.metadata)

        return NodeData(
            data=merged_data,
            metadata=merged_metadata,
            node_id=node_id
        )

    def _generate_error_summary(self, failed_nodes: Set[str],
                              node_results: Dict[str, NodeResult]) -> Optional[str]:
        """生成错误摘要"""
        if not failed_nodes:
            return None

        errors = []
        for node_id in failed_nodes:
            if node_id in node_results:
                result = node_results[node_id]
                errors.append(f"{node_id}: {result.error}")

        return "; ".join(errors)

    def get_workflow_info(self) -> Dict[str, Any]:
        """获取工作流信息"""
        if not self.workflow_config:
            return {"status": "no_workflow_loaded"}

        return {
            "name": self.workflow_config.name,
            "version": self.workflow_config.version,
            "description": self.workflow_config.description,
            "node_count": len(self.workflow_config.nodes),
            "edge_count": len(self.workflow_config.edges),
            "nodes": [
                {
                    "id": node.id,
                    "type": node.type,
                    "name": node.name
                }
                for node in self.workflow_config.nodes
            ]
        }