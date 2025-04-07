import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import random

def create_timeline_chart(db, profile):
    """
    Create a timeline visualization of the knowledge base.
    
    Args:
        db (VectorDB): Vector database instance
        profile (str): User profile name
        
    Returns:
        plotly.graph_objects.Figure: Interactive timeline chart
    """
    # Extract data from database
    metadata = db.metadata
    
    # If no data, return empty chart
    if not metadata:
        fig = go.Figure()
        fig.update_layout(
            title="No data available for timeline visualization",
            xaxis_title="Date",
            yaxis_title="Topics"
        )
        return fig
        
    # Prepare data for visualization
    data = []
    
    for item in metadata:
        try:
            # Parse date
            date_str = item.get("date", "2023-01-01 00:00:00")
            date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            
            # Create data entry
            entry = {
                "topic": item["topic"],
                "date": date_obj,
                "source": item["source"],
                "content_preview": item["content"][:100] + "..." if len(item["content"]) > 100 else item["content"]
            }
            
            data.append(entry)
        except Exception as e:
            print(f"Error processing metadata item for visualization: {str(e)}")
            continue
            
    # Create dataframe
    df = pd.DataFrame(data)
    
    # If dataframe is empty, return empty chart
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="No valid data available for timeline visualization",
            xaxis_title="Date",
            yaxis_title="Topics"
        )
        return fig
        
    # Count topics for bubble size
    topic_counts = df["topic"].value_counts().to_dict()
    df["count"] = df["topic"].map(topic_counts)
    
    # Create timeline visualization
    fig = px.scatter(
        df,
        x="date",
        y="topic",
        size="count",
        color="topic",
        hover_name="topic",
        hover_data=["source", "content_preview"],
        size_max=30,
        title=f"Knowledge Timeline for {profile}",
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Date Added",
        yaxis_title="Topics",
        showlegend=False
    )
    
    return fig

def create_knowledge_network(db):
    """
    Create a network visualization of related topics.
    
    Args:
        db (VectorDB): Vector database instance
        
    Returns:
        plotly.graph_objects.Figure: Interactive network chart
    """
    # Extract topics and their metadata
    topics = db.get_all_topics()
    
    # If no topics, return empty chart
    if not topics:
        fig = go.Figure()
        fig.update_layout(
            title="No topics available for network visualization",
            xaxis_title="",
            yaxis_title=""
        )
        return fig
    
    # Create a simple network layout
    import math
    
    # Count items per topic for node size
    topic_counts = {}
    for item in db.metadata:
        topic = item.get("topic", "Unknown")
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    
    # Node positions and data
    nodes_x = []
    nodes_y = []
    node_sizes = []
    node_text = []
    node_colors = []
    
    # Create color map
    colors = px.colors.qualitative.Plotly
    color_map = {}
    
    # Group topics by prefix if possible (Research Note:, Citation:, etc.)
    topic_groups = {}
    for topic in topics:
        if ":" in topic:
            prefix = topic.split(":")[0]
            if prefix not in topic_groups:
                topic_groups[prefix] = []
            topic_groups[prefix].append(topic)
        else:
            if "General" not in topic_groups:
                topic_groups["General"] = []
            topic_groups["General"].append(topic)
    
    # Generate node colors by group
    for i, group in enumerate(topic_groups.keys()):
        color_map[group] = colors[i % len(colors)]
    
    # Calculate positions using a circle layout with groups
    radius = 10
    group_count = len(topic_groups)
    
    node_group_map = {}  # Map each node to its group index
    
    # Create nodes for each group
    node_index = 0
    for group_i, (group_name, group_topics) in enumerate(topic_groups.items()):
        # Calculate group center position
        group_angle = (2 * math.pi * group_i) / group_count
        group_x = radius * math.cos(group_angle)
        group_y = radius * math.sin(group_angle)
        
        # Create nodes for each topic in the group
        topic_count = len(group_topics)
        for i, topic in enumerate(group_topics):
            # Calculate position around group center
            inner_radius = 3 + (topic_counts.get(topic, 1) * 0.5)  # Adjust for better spacing
            inner_angle = (2 * math.pi * i) / max(1, topic_count)
            
            x = group_x + (inner_radius * 0.25 * math.cos(inner_angle))
            y = group_y + (inner_radius * 0.25 * math.sin(inner_angle))
            
            nodes_x.append(x)
            nodes_y.append(y)
            
            # Node size based on content count
            size = 15 + (topic_counts.get(topic, 1) * 3)  # Base size + scaling
            node_sizes.append(size)
            
            # Node text with count
            node_text.append(f"{topic}<br>({topic_counts.get(topic, 0)} items)")
            
            # Node color by group
            group_key = group_name if group_name in color_map else "General"
            node_colors.append(color_map[group_key])
            
            # Store node's group
            node_group_map[node_index] = group_i
            node_index += 1
    
    # Create edges between nodes
    edge_x = []
    edge_y = []
    
    # Connect all nodes within the same group
    for i in range(len(nodes_x)):
        for j in range(i+1, len(nodes_x)):
            # Connect nodes in the same group
            if node_group_map[i] == node_group_map[j]:
                # Draw line between nodes
                edge_x.extend([nodes_x[i], nodes_x[j], None])
                edge_y.extend([nodes_y[i], nodes_y[j], None])
    
    # Add edges trace
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines'
    )
    
    # Add nodes trace
    node_trace = go.Scatter(
        x=nodes_x, y=nodes_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=False,
            color=node_colors,
            size=node_sizes,
            line=dict(width=2, color='white')
        )
    )
    
    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title="Knowledge Network by Topic Groups",
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        plot_bgcolor='rgba(255,255,255,0.8)'
                    ))
    
    return fig
