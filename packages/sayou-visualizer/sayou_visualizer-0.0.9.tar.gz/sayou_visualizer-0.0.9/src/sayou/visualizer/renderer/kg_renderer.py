import json
import os
from collections import defaultdict

from sayou.core.base_component import BaseComponent


class KGRenderer(BaseComponent):
    """
    Renders 3D KG with 'Virtual Hierarchy'.
    Injects missing Parent Nodes based on metadata and applies Semantic Styling.
    """

    component_name = "KGRenderer"

    def render(self, json_path: str, output_path: str = "kg_view_3d.html"):
        if not os.path.exists(json_path):
            self._log(f"Output file not found: {json_path}", level="error")
            return

        with open(json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # ---------------------------------------------------------
        # [Python Logic]
        # ---------------------------------------------------------
        nodes_by_source = defaultdict(list)
        final_nodes = []
        final_links = []

        existing_ids = set()

        for node in raw_data.get("nodes", []):
            node_id = node.get("node_id")
            existing_ids.add(node_id)
            attrs = node.get("attributes", {})
            meta = node.get("metadata", {})

            source = meta.get("source") or attrs.get("sayou:source") or "Unknown Source"
            nodes_by_source[source].append(node_id)

            sem_type = attrs.get("sayou:semanticType", "text")

            clean_attrs = {}
            for k, v in attrs.items():
                if isinstance(v, str) and len(v) > 300:
                    clean_attrs[k] = v[:200] + "..."
                else:
                    clean_attrs[k] = v

            display_label = attrs.get("schema:text", node_id)
            if len(display_label) > 30:
                display_label = display_label[:30] + "..."

            group = "Chunk"
            color = "#1e90ff"
            val = 5

            if sem_type in ["h1", "h2", "h3", "title"]:
                group = "Header"
                color = "#ffa502"
                val = 12
            elif "list" in sem_type:
                group = "List"
                color = "#2ed573"
                val = 4
            elif "table" in sem_type:
                group = "Table"
                color = "#a55eea"
                val = 10
            elif "code" in sem_type:
                group = "Code"
                color = "#ff4757"
                val = 8

            final_nodes.append(
                {
                    "id": node_id,
                    "label": display_label,
                    "group": group,
                    "sem_type": sem_type,
                    "color": color,
                    "val": val,
                    "attributes": clean_attrs,
                    "source": source,
                }
            )

        for edge in raw_data.get("links", []) + raw_data.get("edges", []):
            final_links.append(
                {
                    "source": edge.get("source"),
                    "target": edge.get("target"),
                    "relation": edge.get("relation", "relates_to"),
                }
            )

        for source_name, child_ids in nodes_by_source.items():
            if source_name in existing_ids:
                continue

            virtual_doc_id = f"VIRTUAL_DOC:{source_name}"

            final_nodes.append(
                {
                    "id": virtual_doc_id,
                    "label": source_name,
                    "group": "Document",
                    "color": "#ff4757",
                    "val": 30,
                    "attributes": {
                        "type": "Virtual Parent",
                        "child_count": len(child_ids),
                    },
                    "is_virtual": True,
                }
            )

            for child_id in child_ids:
                final_links.append(
                    {
                        "source": virtual_doc_id,
                        "target": child_id,
                        "relation": "CONTAINS",
                    }
                )

        graph_data = {"nodes": final_nodes, "links": final_links}
        self._log(f"Rendering KG with Virtual Hierarchy ({len(final_nodes)} nodes)...")

        # ---------------------------------------------------------
        # [JS Logic] Renderer
        # ---------------------------------------------------------
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sayou Dataverse</title>
    <style>
        body {{ margin: 0; background-color: #000205; overflow: hidden; }}
        #graph {{ width: 100%; height: 100vh; }}
        
        #info {{
            position: absolute; top: 20px; right: 20px; width: 300px;
            background: rgba(5, 10, 20, 0.85);
            border: 1px solid rgba(0, 242, 255, 0.3);
            border-left: 3px solid #00f2ff;
            box-shadow: 0 0 20px rgba(0, 242, 255, 0.1);
            color: #dff9fb; padding: 20px;
            font-family: 'Consolas', 'Monaco', monospace;
            backdrop-filter: blur(5px);
            display: none; pointer-events: none;
            border-radius: 0 10px 10px 0;
        }}
        .tag {{ 
            display: inline-block; padding: 2px 8px; border-radius: 2px; 
            font-size: 9px; font-weight: 800; color: #000; margin-bottom: 12px;
            text-transform: uppercase; letter-spacing: 1px;
        }}
        h3 {{ 
            margin: 0 0 12px 0; color: #fff; 
            border-bottom: 1px dashed #576574; padding-bottom: 8px; 
            font-size: 14px; line-height: 1.4;
        }}
        .row {{ font-size: 11px; margin-bottom: 4px; color: #a4b0be; }}
        .key {{ color: #00d2d3; margin-right: 5px; }}
    </style>
    <script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
    <script src="https://unpkg.com/3d-force-graph@1.73.1/dist/3d-force-graph.min.js"></script>
</head>
<body>
    <div id="graph"></div>
    <div id="info"></div>

    <script>
        const gData = {json.dumps(graph_data)};
        const infoDiv = document.getElementById('info');

        const Graph = ForceGraph3D()(document.getElementById('graph'))
            .graphData(gData)
            .backgroundColor('#000205')
            .showNavInfo(false)
            
            // [Design Logic]
            .nodeThreeObject(node => {{
                let geometry, material;
                
                // 1. Virtual Document
                if (node.group === "Document") {{
                    const size = node.val;
                    geometry = new THREE.BoxGeometry(size, size, size);
                    
                    const edges = new THREE.EdgesGeometry(geometry);
                    material = new THREE.LineBasicMaterial({{ 
                        color: node.color, 
                        transparent: true, 
                        opacity: 0.4 
                    }});
                    const wireframe = new THREE.LineSegments(edges, material);
                    
                    const coreGeo = new THREE.BoxGeometry(size*0.2, size*0.2, size*0.2);
                    const coreMat = new THREE.MeshBasicMaterial({{ color: node.color, wireframe: true }});
                    wireframe.add(new THREE.Mesh(coreGeo, coreMat));
                    
                    return wireframe;
                }}
                
                // 2. Headers (H1~H3): [발광 다이아몬드]
                else if (node.group === "Header") {{
                    geometry = new THREE.OctahedronGeometry(4);
                    material = new THREE.MeshPhongMaterial({{ 
                        color: node.color, 
                        emissive: node.color,
                        emissiveIntensity: 0.5,
                        shininess: 100,
                        flatShading: true
                    }});
                }}
                
                // 3. Chunk / Text: [데이터 오브]
                else {{
                    // 단순 구 대신 Icosahedron(정이십면체)을 써서 디지털 느낌
                    geometry = new THREE.IcosahedronGeometry(3, 1); 
                    material = new THREE.MeshLambertMaterial({{ 
                        color: node.color, 
                        transparent: true, 
                        opacity: 0.8 
                    }});
                }}
                
                return new THREE.Mesh(geometry, material);
            }})
            
            // [Link Design]
            .linkWidth(link => link.relation === "CONTAINS" ? 0 : 0.5)
            .linkColor(() => '#2f3542')
            .linkDirectionalParticles(link => link.relation === "CONTAINS" ? 1 : 3)
            .linkDirectionalParticleWidth(1.2)
            .linkDirectionalParticleSpeed(0.006)
            .linkDirectionalParticleColor(link => link.relation === "CONTAINS" ? '#57606f' : '#00f2ff')

            // [Interaction]
            .onNodeHover(node => {{
                document.body.style.cursor = node ? 'crosshair' : null;
                if (node) {{
                    infoDiv.style.display = 'block';
                    
                    let tagColor = node.color;
                    if(node.group === 'Document') tagColor = '#ff4757';
                    
                    let html = `<span class='tag' style='background:${{tagColor}}'>${{node.group}}</span>`;
                    if(node.sem_type) html += `<span class='tag' style='background:#2f3542; color:#fff; margin-left:5px'>${{node.sem_type}}</span>`;
                    
                    html += `<h3>${{node.label}}</h3>`;
                    
                    if (node.attributes) {{
                        for (const [k, v] of Object.entries(node.attributes)) {{
                            if(k === 'type' || k === 'child_count') continue;
                            let key = k.includes(':') ? k.split(':').pop() : k;
                            html += `<div class='row'><span class='key'>${{key}}:</span> ${{v}}</div>`;
                        }}
                    }}
                    infoDiv.innerHTML = html;
                }} else {{
                    infoDiv.style.display = 'none';
                }}
            }})
            .onNodeClick(node => {{
                const distance = 70;
                const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z);
                const newPos = node.x || node.y || node.z
                    ? {{ x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }}
                    : {{ x: 0, y: 0, z: distance }};
                Graph.cameraPosition(newPos, node, 1500);
            }});

        // [Lighting]
        const ambientLight = new THREE.AmbientLight(0x222222); // 어두운 기본광
        Graph.scene().add(ambientLight);
        
        const blueLight = new THREE.PointLight(0x00f2ff, 1, 100); // 청록색 포인트 조명
        blueLight.position.set(50, 50, 50);
        Graph.scene().add(blueLight);
        
        const pinkLight = new THREE.PointLight(0xff00ff, 0.5, 100); // 핑크색 포인트 조명 (반대편)
        pinkLight.position.set(-50, -50, -50);
        Graph.scene().add(pinkLight);

        // [Physics]
        Graph.d3Force('charge').strength(-50);
        Graph.d3Force('link').distance(link => link.relation === "CONTAINS" ? 60 : 30);

    </script>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        self._log(f"✅ Semantic 3D KG Showcase saved to: {output_path}")
