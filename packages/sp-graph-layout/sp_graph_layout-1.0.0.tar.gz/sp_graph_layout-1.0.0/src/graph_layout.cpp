#include "graph_layout.h"

#include <format>
#include <fstream>
#include <cmath>
#include <ranges>
#include <algorithm>

#include "svg_diagram.h"
using namespace std;
using namespace svg_diagram;
using namespace graph_layout;

DirectedGraphHierarchicalLayout::DirectedGraphHierarchicalLayout() = default;

shared_ptr<SPDirectedGraph> DirectedGraphHierarchicalLayout::createGraph(const size_t numVertices) {
    _initialNumVertices = static_cast<int>(numVertices);
    _graph = make_shared<SPDirectedGraph>(numVertices);
    return _graph;
}

void DirectedGraphHierarchicalLayout::setGraph(const shared_ptr<SPDirectedGraph>& graph) {
    _initialNumVertices = static_cast<int>(graph->numVertices());
    _graph = graph;
}

shared_ptr<SPDirectedGraph> DirectedGraphHierarchicalLayout::graph() const {
    return _graph;
}

Attributes & DirectedGraphHierarchicalLayout::attributes() {
    return _attributes;
}

void DirectedGraphHierarchicalLayout::setFeedbackArcsMethod(const FeedbackArcsMethod method) {
    _feedbackArcsFinder.setMethod(method);
}

void DirectedGraphHierarchicalLayout::setLayerAssignmentMethod(const LayerAssignmentMethod method) {
    _layerAssignment.setMethod(method);
}

void DirectedGraphHierarchicalLayout::setCrossMinimizationMethod(const CrossMinimizationMethod method) {
    _crossMinimization.setMethod(method);
}

void DirectedGraphHierarchicalLayout::setVertexPositioningMethod(const VertexPositioningMethod method) {
    _vertexPositioning.setMethod(method);
}

void DirectedGraphHierarchicalLayout::setLayerMargin(const double margin) {
    _vertexPositioning.setLayerMargin(margin);
}

void DirectedGraphHierarchicalLayout::layoutGraph() {
    if (_graph == nullptr) {
        return;
    }
    computeVertexSizes();
    const size_t n = _graph->numVertices();
    const auto rankDir = _attributes.rankDir();
    int newVertexIndex = static_cast<int>(n);
    int edgeIndex = CrossMinimization::VIRTUAL_EDGE_ID_OFFSET;
    _graph->disableSelfCycleEdges();
    GraphComponentSplitter splitter;
    const auto feedbackArcs = _feedbackArcsFinder.findFeedbackArcs(*_graph);
    _graph->reverseEdges(feedbackArcs);
    _xs.resize(n);
    _ys.resize(n);
    _virtualEdges.clear();
    double subGraphShift = 0.0;
    auto subGraphs = splitter.splitGraph(*_graph);
    for (int groupIndex = 0; groupIndex < static_cast<int>(subGraphs.size()); ++groupIndex) {
        auto& subGraph = subGraphs[groupIndex];
        const int subN = static_cast<int>(subGraph.numVertices());
        auto ranks = _layerAssignment.rankVertices(subGraph);
        auto [layering, virtualEdges] = _crossMinimization.reduceNumCross(subGraph, ranks);
        auto [subXs, subYs] = _vertexPositioning.assignCoordinates(subGraph, layering);
        double maxLeftVertexSize = 0.0, maxRightVertexSize = 0.0, maxX = 0.0;
        for (int u = 0; u < subN; ++u) {
            if (subXs[u] == 0.0) {
                maxLeftVertexSize = max(maxLeftVertexSize, _vertexPositioning.vertexSizeAt(u));
            }
            if (subXs[u] >= maxX) {
                maxX = subXs[u];
                maxRightVertexSize = max(maxRightVertexSize, _vertexPositioning.vertexSizeAt(u));
            }
        }
        if (groupIndex > 0) {
            subGraphShift += maxLeftVertexSize * 0.5;
        }
        for (const auto& virtualEdge : virtualEdges) {
            SPVirtualEdge newVirtualEdge;
            const auto& originalEdge = virtualEdge.originalEdge;
            newVirtualEdge.originalEdge = originalEdge;
            const auto& edgeIds = virtualEdge.virtualEdgeIds;
            bool isReversed = _graph->isReverseEdge(originalEdge.id);
            bool removeOriginalEdge = false;
            int lastVertex = originalEdge.u;
            vector<int> newEdgeIds;
            for (int i = 0; i + 1 < static_cast<int>(edgeIds.size()); ++i) {
                const auto& inEdge = subGraph.getEdge(edgeIds[i]);
                const auto& outEdge = subGraph.getEdge(edgeIds[i + 1]);
                if (abs(subXs[inEdge.u] - subXs[inEdge.v]) > 1e-8 || abs(subXs[outEdge.u] - subXs[outEdge.v]) > 1e-8) {
                    removeOriginalEdge = true;
                    _graph->updateNumVertices(newVertexIndex + 1);
                    newEdgeIds.push_back(edgeIndex);
                    newVirtualEdge.virtualEdgeIds.emplace_back(edgeIndex);
                    if (!isReversed) {
                        _graph->addEdge({edgeIndex++, lastVertex, newVertexIndex});
                    } else {
                        _graph->addEdge({edgeIndex++, newVertexIndex, lastVertex});
                    }
                    _xs.push_back(subXs[inEdge.v] + subGraphShift);
                    _ys.push_back(subYs[inEdge.v]);
                    lastVertex = newVertexIndex++;
                    if (subXs[inEdge.v] >= maxX) {
                        maxX = subXs[inEdge.v];
                        maxRightVertexSize = max(maxRightVertexSize, _vertexPositioning.vertexSizeAt(inEdge.v));
                    }
                }
            }
            if (removeOriginalEdge) {
                _graph->removeEdge(originalEdge.id);
                newEdgeIds.push_back(edgeIndex);
                newVirtualEdge.virtualEdgeIds.emplace_back(edgeIndex);
                if (!isReversed) {
                    _graph->addEdge({edgeIndex++, lastVertex, originalEdge.v});
                } else {
                    _graph->addEdge({edgeIndex++, originalEdge.v, lastVertex});
                }
                if (isReversed) {
                    swap(newVirtualEdge.originalEdge.u, newVirtualEdge.originalEdge.v);
                    ranges::reverse(newVirtualEdge.virtualEdgeIds);
                }
                _virtualEdges.emplace_back(newVirtualEdge);
            }
        }
        for (int u = 0; u < subN; ++u) {
            _xs[splitter.originalVertexId(groupIndex, u)] = subXs[u] + subGraphShift;
            _ys[splitter.originalVertexId(groupIndex, u)] = subYs[u];
        }
        subGraphShift += maxX + maxRightVertexSize * 0.5;
    }
    _graph->reverseEdgesBack();
    _graph->enableSelfCycleEdges();
    adjustCoordinatesByGraphRank();
}

string DirectedGraphHierarchicalLayout::render() const {
    if (_graph == nullptr) {
        return "";
    }
    const int n = static_cast<int>(_graph->numVertices());
    SVGDiagram diagram;
    if (const auto bgColor = _attributes.graphAttributes(ATTRIBUTE_KEY_BG_COLOR); !bgColor.empty()) {
        diagram.setBackgroundColor(bgColor);
    }
    unordered_map<int, unordered_set<int>> outEdges;
    const auto rankDir = _attributes.rankDir();
    for (const auto& [id, u, v] : _graph->edges()) {
        outEdges[u].insert(v);
    }
    vector<string> nodeIds(n);
    for (int u = 0; u < n; ++u) {
        nodeIds[u] = format("node{}", u);
        const auto node = diagram.addNode(nodeIds[u]);
        node->setCenter(_xs[u], _ys[u]);
        if (u < _initialNumVertices) {
            node->setShape(_attributes.vertexAttributes(u, ATTRIBUTE_KEY_SHAPE));
            node->setLabel(_attributes.vertexAttributes(u, ATTRIBUTE_KEY_LABEL));
        } else {
            node->setShape(string("none"));
            node->setMargin(0, 0);
        }
    }
    for (const auto& edge : _graph->edges()) {
        if (isVirtualVertex(edge.u) || isVirtualVertex(edge.v)) {
            continue;
        }
        const auto label = _attributes.edgeAttributes(edge.id, ATTRIBUTE_KEY_LABEL);
        const auto e = diagram.addEdge(nodeIds[edge.u], nodeIds[edge.v]);
        e->setLabel(label);
        e->setMargin(2);
        e->setArrowHead();
        if (edge.u != edge.v) {
            if (outEdges[edge.v].contains(edge.u)) {
                // There is a reverse edge
                const auto x1 = _xs[edge.u];
                const auto y1 = _ys[edge.u];
                const auto x2 = _xs[edge.v];
                const auto y2 = _ys[edge.v];
                const double dx = x2 - x1;
                const double dy = y2 - y1;
                const double len = sqrt(dx * dx + dy * dy);
                const double nx = -dy / len;
                const double ny = dx / len;
                const double midX = (x1 + x2) / 2;
                const double midY = (y1 + y2) / 2;
                const double x = midX + nx * 10.0;
                const double y = midY + ny * 10.0;
                e->addConnectionPoint(x, y);
            }
        } else {
            const double vertexSize = _vertexPositioning.vertexSizeAt(edge.u);
            if (rankDir == AttributeRankDir::TOP_TO_BOTTOM) {
                e->setSelfLoopAttributes(180, vertexSize * 0.8, 30);
            } else if (rankDir == AttributeRankDir::BOTTOM_TO_TOP) {
                e->setSelfLoopAttributes(0, vertexSize * 0.8, 30);
            } else if (rankDir == AttributeRankDir::LEFT_TO_RIGHT) {
                e->setSelfLoopAttributes(-90, vertexSize * 0.8, 30);
            } else {
                e->setSelfLoopAttributes(90, vertexSize * 0.8, 30);
            }
        }
    }
    for (const auto& virtualEdge : _virtualEdges) {
        const auto& originalEdge = virtualEdge.originalEdge;
        const auto& edgeIds = virtualEdge.virtualEdgeIds;
        const auto label = _attributes.edgeAttributes(virtualEdge.originalEdge.id, ATTRIBUTE_KEY_LABEL);
        const auto e = diagram.addEdge(nodeIds[originalEdge.u], nodeIds[originalEdge.v]);
        e->setLabel(label);
        e->setSplines(SVGEdge::SPLINES_LINE);
        e->setArrowHead();
        e->setMargin(2);
        for (int i = 0; i + 1 < static_cast<int>(edgeIds.size()); ++i) {
            const auto& edge = _graph->getEdge(edgeIds[i]);
            e->addConnectionPoint(_xs[edge.v], _ys[edge.v]);
        }
    }
    return diagram.render();
}

void DirectedGraphHierarchicalLayout::render(const string& filePath) const {
    ofstream file(filePath);
    file << render();
    file.close();
}

void DirectedGraphHierarchicalLayout::initVertexLabelsWithNumericalValues(const int start) {
    const int n = _initialNumVertices;
    for (int i = 0; i < n; ++i) {
        _attributes.setVertexAttributes(i, ATTRIBUTE_KEY_LABEL, format("{}", start + i));
    }
}

void DirectedGraphHierarchicalLayout::setVertexLabels(const vector<string> &vertexLabels) {
    for (int i = 0; i < static_cast<int>(vertexLabels.size()); ++i) {
        _attributes.setVertexAttributes(i, ATTRIBUTE_KEY_LABEL, vertexLabels[i]);
    }
}

void DirectedGraphHierarchicalLayout::setEdgeLabel(const int edgeId, const string& label) {
    _attributes.setEdgeAttributes(edgeId, ATTRIBUTE_KEY_LABEL, label);
}

/** A vertex is virtual if the vertex ID is greater than the maximum vertex ID in the beginning graph.
 *
 * @param u A vertex ID.
 * @return Whether the vertex is virtual.
 */
bool DirectedGraphHierarchicalLayout::isVirtualVertex(const int u) const {
    return u >= _initialNumVertices;
}

/** Adjust the coordinates by `_graphAttributes.rank`.
 * The default rank is top to bottom.
 */
void DirectedGraphHierarchicalLayout::adjustCoordinatesByGraphRank() {
    const auto rankDir = _attributes.rankDir();
    if (rankDir == AttributeRankDir::TOP_TO_BOTTOM) {
        return;
    }
    if (rankDir == AttributeRankDir::BOTTOM_TO_TOP || rankDir == AttributeRankDir::RIGHT_TO_LEFT) {
        const auto yMin = ranges::min(_ys);
        const auto yMax = ranges::max(_ys);
        for (auto& y : _ys) {
            y = yMax - y + yMin;
        }
    }
    if (rankDir == AttributeRankDir::LEFT_TO_RIGHT || rankDir == AttributeRankDir::RIGHT_TO_LEFT) {
        swap_ranges(_xs.begin(), _xs.end(), _ys.begin());
    }
}

void DirectedGraphHierarchicalLayout::computeVertexSizes() {
    const int n = static_cast<int>(_graph->numVertices());
    const auto rankDir = _attributes.rankDir();
    double layerMargin = VertexPositioning::DEFAULT_LAYER_MARGIN;
    double vertexMargin = VertexPositioning::DEFAULT_VERTEX_MARGIN;
    vector vertexSizes(n, VertexPositioning::DEFAULT_VERTEX_SIZE);
    for (int u = 0; u < n; ++u) {
        SVGNode node;
        node.setShape(_attributes.vertexAttributes(u, ATTRIBUTE_KEY_SHAPE));
        node.setLabel(_attributes.vertexAttributes(u, ATTRIBUTE_KEY_LABEL));
        node.setFontName(_attributes.vertexAttributes(u, ATTRIBUTE_KEY_FONT_NAME));
        node.setFontSize(stod(_attributes.vertexAttributes(u, ATTRIBUTE_KEY_FONT_SIZE)));
        node.adjustNodeSize();
        const auto width = node.width();
        const auto height = node.height();
        vertexSizes[u] = max(vertexSizes[u], max(width, height));
        if (rankDir == AttributeRankDir::TOP_TO_BOTTOM || rankDir == AttributeRankDir::BOTTOM_TO_TOP) {
            vertexMargin = max(vertexMargin, width);
            layerMargin = max(layerMargin, height);
        } else {
            vertexMargin = max(vertexMargin, height);
            layerMargin = max(layerMargin, width);
        }
    }
    _vertexPositioning.setVertexSizes(std::move(vertexSizes));
    _vertexPositioning.setVertexMargin(vertexMargin);
    _vertexPositioning.setLayerMargin(layerMargin);
}
