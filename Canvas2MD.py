import json

def load_canvas(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def find_starting_nodes(edges):
    to_nodes = {edge['toNode'] for edge in edges}
    from_nodes = {edge['fromNode'] for edge in edges}
    start_nodes = from_nodes - to_nodes
    return list(start_nodes)

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

def extract_stories(data):
    nodes = {node['id']: node for node in data['nodes']}
    edges = data.get('edges', [])

    main_story_edges = [edge for edge in edges if edge.get('fromEnd', 'arrow') != 'none' and edge.get('toEnd', 'arrow') != 'none']
    sub_story_edges = [edge for edge in edges if edge.get('fromEnd', 'none') == 'none' or edge.get('toEnd', 'none') == 'none']

    start_nodes = find_starting_nodes(main_story_edges)
    main_stories = [find_story_path(start_node, main_story_edges) for start_node in start_nodes]

    main_story_nodes = {node for story in main_stories for node in story}

    sub_stories = []
    visited_nodes = set(main_story_nodes)
    sub_story_map = {}
    select_stories = {}
    
    for edge in sub_story_edges:
        if edge['fromNode'] not in visited_nodes:
            sub_story = find_story_path(edge['fromNode'], sub_story_edges, follow_arrows=False)
            sub_story = [node_id for node_id in sub_story if node_id not in main_story_nodes]
            if sub_story:
                sub_stories.append(sub_story)
                if edge['toNode'] not in sub_story_map:
                    sub_story_map[edge['toNode']] = []
                sub_story_map[edge['toNode']].append(sub_story[0])
                visited_nodes.update(sub_story)
        elif edge['toNode'] not in visited_nodes:
            sub_story = find_story_path(edge['toNode'], sub_story_edges, follow_arrows=False)
            sub_story = [node_id for node_id in sub_story if node_id not in main_story_nodes]
            if sub_story:
                sub_stories.append(sub_story)
                if edge['fromNode'] not in sub_story_map:
                    sub_story_map[edge['fromNode']] = []
                sub_story_map[edge['fromNode']].append(sub_story[0])
                visited_nodes.update(sub_story)

    for story in main_stories:
        for node_id in story:
            connected_edges = [edge for edge in main_story_edges if edge['fromNode'] == node_id]
            if len(connected_edges) > 1:
                select_stories[node_id] = [edge['toNode'] for edge in connected_edges]

    connected_nodes = set(edge['fromNode'] for edge in edges).union(edge['toNode'] for edge in edges)
    isolated_nodes = [node['id'] for node in nodes.values() if node['id'] not in connected_nodes]

    # セレクトストーリーのノードIDを取得
    select_story_nodes = {node_id for node_ids in select_stories.values() for node_id in node_ids}

    # セレクトストーリーがメインストーリーに含まれている場合、それを除外する
    main_stories = [[node_id for node_id in story if node_id not in select_story_nodes] for story in main_stories]

    return main_stories, sub_stories, isolated_nodes, sub_story_map, select_stories, select_story_nodes

def sort_nodes_by_position(node_ids, nodes):
    return sorted(node_ids, key=lambda node_id: (nodes[node_id]['y'], nodes[node_id]['x']))

def node_to_markdown(node, indent_level=0, add_sub_ref_ids=None, is_select_story=False):
    indent = "  " * indent_level
    content = "\n"
    if is_select_story:
        content += f'<a id="{node["id"]}"></a>\n\n'
    if node['type'] == 'text':
        content += f"{indent}{node['text'].replace('\n', f'\n{indent}')}\n"
    elif node['type'] == 'file':
        content += f"{indent}![]({node['file']})\n"
    if add_sub_ref_ids:
        for sub_ref_id in add_sub_ref_ids:
            content += f"\n{indent}[^sub_{sub_ref_id}]\n"
    return content + "\n"

def generate_markdown(data):
    nodes = {node['id']: node for node in data['nodes']}
    main_stories, sub_stories, isolated_nodes, sub_story_map, select_stories, select_story_nodes = extract_stories(data)
    
    markdown_lines = []

    # サブストーリーを変換するための辞書を作成
    sub_story_content_map = {}
    for sub_story in sub_stories:
        if sub_story and sub_story[0] not in select_story_nodes:
            for node_id in sub_story:
                node = nodes[node_id]
                sub_story_content_map[node_id] = node_to_markdown(node, indent_level=2)

    for main_story in main_stories:
        for node_id in main_story:
            node = nodes[node_id]
            # セレクトストーリーでないサブストーリーの参照IDのみ追加
            add_sub_ref_ids = [ref_id for ref_id in sub_story_map.get(node_id, []) if ref_id not in select_story_nodes]
            markdown_lines.append(node_to_markdown(node, add_sub_ref_ids=add_sub_ref_ids))
            if node_id in select_stories:
                sorted_select_nodes = sort_nodes_by_position(select_stories[node_id], nodes)
                markdown_lines.append("\n")
                for idx, select_node_id in enumerate(sorted_select_nodes, start=1):
                    markdown_lines.append(f"[セレクトストーリー_{idx}にとぶ](#{select_node_id})\n")
                markdown_lines.append("\n")
                for select_node_id in sorted_select_nodes:
                    select_node = nodes[select_node_id]
                    add_select_sub_ref_ids = [ref_id for ref_id in sub_story_map.get(select_node_id, []) if ref_id not in select_story_nodes]
                    markdown_lines.append(node_to_markdown(select_node, is_select_story=True, add_sub_ref_ids=add_select_sub_ref_ids))
                    markdown_lines.append("\n")
        markdown_lines.append("\n")

    # サブストーリーの内容を脚注として追加
    for node_id, content in sub_story_content_map.items():
        markdown_lines.append(f"\n[^sub_{node_id}]:")
        markdown_lines.append(content)

    for node_id in isolated_nodes:
        node = nodes[node_id]
        markdown_lines.append(f"---\n{node_to_markdown(node)}\n---")

    return "\n".join(markdown_lines)

def save_markdown(content, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

if __name__ == "__main__":
    canvas_file = 'PtPr3/PtPr3/Add_files/Canvas2MD/Simple_Canvas.canvas'
    output_markdown_file = 'PtPr3/PtPr3/Add_files/Canvas2MD/Simple_Canvas.md'
    try:
        canvas_data = load_canvas(canvas_file)
        markdown_content = generate_markdown(canvas_data)
        save_markdown(markdown_content, output_markdown_file)
        print(f"Markdown file generated and saved as {output_markdown_file}")
    except Exception as e:
        print(f"An error occurred: {e}")
