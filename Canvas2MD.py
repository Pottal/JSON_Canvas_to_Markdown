import json

# Load the provided JSON Canvas file
def load_canvas(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

# Function to find the starting nodes of main stories
def find_starting_nodes(edges):
    to_nodes = {edge['toNode'] for edge in edges}
    from_nodes = {edge['fromNode'] for edge in edges}
    start_nodes = from_nodes - to_nodes
    return list(start_nodes)

# Function to find the path of a story
def find_story_path(start_node, edges, follow_arrows=True):
    path = [start_node]
    current_node = start_node
    while True:
        if follow_arrows:
            next_edges = [edge for edge in edges if edge['fromNode'] == current_node and edge.get('fromEnd', 'arrow') != 'none' and edge.get('toEnd', 'arrow') != 'none']
        else:
            next_edges = [edge for edge in edges if edge['fromNode'] == current_node and (edge.get('fromEnd') == 'none' or edge.get('toEnd') == 'none')]
        if not next_edges:
            break
        next_node = next_edges[0]['toNode']
        path.append(next_node)
        current_node = next_node
    return path

# Function to extract main stories, sub stories and isolated nodes
    # メインストーリー(main_story)の定義: ノード同士が一方向矢印で結ばれた一連のノード(分岐はしない)
    # サブストーリー(sub_story)の定義: メインストーリーのノードに対して矢印ではなく**線**で結ばれた**1つの**ノード
    # 孤立したノード(isolated nodes)の定義: どのノードとも結びついていない孤立したノード
def extract_stories(data):
    nodes = {node['id']: node for node in data['nodes']}
    edges = data.get('edges', [])

    # Separate edges into main story candidates and sub story candidates
    main_story_edges = [edge for edge in edges if edge.get('fromEnd', 'arrow') != 'none' and edge.get('toEnd', 'arrow') != 'none']
    sub_story_edges = [edge for edge in edges if edge.get('fromEnd', 'none') == 'none' or edge.get('toEnd', 'none') == 'none']

    # Find main stories
    start_nodes = find_starting_nodes(main_story_edges)
    main_stories = [find_story_path(start_node, main_story_edges) for start_node in start_nodes]

    # Identify all nodes involved in main stories
    main_story_nodes = {node for story in main_stories for node in story}

    # Find sub stories
    sub_stories = []
    visited_nodes = set(main_story_nodes)
    sub_story_map = {}
    for edge in sub_story_edges:
        if edge['fromNode'] not in visited_nodes:
            sub_story = find_story_path(edge['fromNode'], sub_story_edges, follow_arrows=False)
            sub_story = [node_id for node_id in sub_story if node_id not in main_story_nodes]
            if sub_story:
                sub_stories.append(sub_story)
                sub_story_map[edge['toNode']] = sub_story[0]
                visited_nodes.update(sub_story)
        elif edge['toNode'] not in visited_nodes:
            sub_story = find_story_path(edge['toNode'], sub_story_edges, follow_arrows=False)
            sub_story = [node_id for node_id in sub_story if node_id not in main_story_nodes]
            if sub_story:
                sub_stories.append(sub_story)
                sub_story_map[edge['fromNode']] = sub_story[0]
                visited_nodes.update(sub_story)

    connected_nodes = set(edge['fromNode'] for edge in edges).union(edge['toNode'] for edge in edges)
    isolated_nodes = [node['id'] for node in nodes.values() if node['id'] not in connected_nodes]

    return main_stories, sub_stories, isolated_nodes, sub_story_map

# Function to convert nodes to Markdown
def node_to_markdown(node, indent_level=0, add_sub_ref_id=None):
    indent = "  " * indent_level
    content = ""
    if node['type'] == 'text':
        content = f"{indent}{node['text'].replace('\n', f'\n{indent}')}"
    elif node['type'] == 'file':
        content = f"{indent}![]({node['file']})"
    if add_sub_ref_id:
        content += f" [^sub_{add_sub_ref_id}]"
    return content

# Function to generate Markdown content from JSON Canvas data
def generate_markdown(data):
    nodes = {node['id']: node for node in data['nodes']}
    main_stories, sub_stories, isolated_nodes, sub_story_map = extract_stories(data)
    
    markdown_lines = []

    # Main Stories
    for main_story in main_stories:
        for node_id in main_story:
            node = nodes[node_id]
            add_sub_ref_id = sub_story_map.get(node_id)
            markdown_lines.append(node_to_markdown(node, add_sub_ref_id=add_sub_ref_id))
        markdown_lines.append("")  # Separate main stories with a newline

    # Sub Stories
    for sub_story in sub_stories:
        if sub_story:
            first_node_id = sub_story[0]
            markdown_lines.append(f"\n[^sub_{first_node_id}]:")
        for node_id in sub_story:
            node = nodes[node_id]
            markdown_lines.append(node_to_markdown(node, indent_level=2))
        markdown_lines.append("")  # Separate sub stories with a newline

    # Isolated Nodes
    for node_id in isolated_nodes:
        node = nodes[node_id]
        markdown_lines.append(f"---\n{node_to_markdown(node)}\n---")

    return "\n".join(markdown_lines)

# Function to save Markdown content to a file
def save_markdown(content, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

# Main function to execute the script
if __name__ == "__main__":
    canvas_file = 'Sample.canvas'           # 読み込むJSON Canvasファイルをフルパスで入力してください。
    output_markdown_file = 'Sample.md'      # Markdownファイルの出力先を指定してください。
                                            # Canvasファイルと違うディレクトリの場合、JSON Canvas中に埋め込んだMarkdownファイルや画像がうまく表示されない場合があります。
    try:
        canvas_data = load_canvas(canvas_file)
        markdown_content = generate_markdown(canvas_data)
        save_markdown(markdown_content, output_markdown_file)
        print(f"Markdown file generated and saved as {output_markdown_file}")
    except Exception as e:
        print(f"An error occurred: {e}")
