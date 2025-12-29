import pytest
import asyncio
from service_forge.workflow.nodes import *
from service_forge.workflow.edge import Edge
from service_forge.workflow.workflow import Workflow


@pytest.mark.asyncio
async def test_single_print_node():
    """Test a single PrintNode in a workflow."""
    workflow = Workflow([])
    print_node = PrintNode('print_0')
    print_node.fill_input_by_name('message', 'Hello')
    
    workflow.add_nodes([print_node])
    await workflow.run()

@pytest.mark.asyncio
async def test_multiple_print_nodes():
    """Test multiple PrintNodes in a workflow."""
    workflow = Workflow([])
    
    print_1 = PrintNode('print_1')
    print_1.fill_input_by_name('message', 'World')
    
    print_2 = PrintNode('print_2')
    print_2.fill_input_by_name('message', 'Test')
    
    workflow.add_nodes([print_1, print_2])
    await workflow.run()
    
@pytest.mark.asyncio
async def test_if_node_true_branch():
    """Test IfNode with true condition."""
    workflow = Workflow([])
    print_0 = PrintNode('print_0')
    print_1 = PrintNode('print_1')

    if_node = IfNode('if')
    if_node.fill_input_by_name('condition', '0 == 0')

    edge_0 = Edge(if_node, print_0, 'true', 'message')
    edge_1 = Edge(if_node, print_1, 'false', 'message')

    if_node.output_edges = [edge_0, edge_1]
    print_0.input_edges = [edge_0]
    print_1.input_edges = [edge_1]

    workflow.add_nodes([if_node, print_0, print_1])
    await workflow.run()
    
@pytest.mark.asyncio
async def test_if_node_false_branch():
    """Test IfNode with false condition."""
    workflow = Workflow([])
    print_0 = PrintNode('print_0')
    print_1 = PrintNode('print_1')

    if_node = IfNode('if')
    if_node.fill_input_by_name('condition', '1 == 0')

    edge_0 = Edge(if_node, print_0, 'true', 'message')
    edge_1 = Edge(if_node, print_1, 'false', 'message')

    if_node.output_edges = [edge_0, edge_1]
    print_0.input_edges = [edge_0]
    print_1.input_edges = [edge_1]

    workflow.add_nodes([if_node, print_0, print_1])
    await workflow.run()
    