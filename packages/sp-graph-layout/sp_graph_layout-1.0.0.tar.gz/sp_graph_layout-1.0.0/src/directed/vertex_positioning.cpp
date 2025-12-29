#include "directed/vertex_positioning.h"

#include <chrono>
#include <ranges>
#include <algorithm>
using namespace std;
using namespace graph_layout;

VertexPositioning::VertexPositioning(const VertexPositioningMethod method) : _method(method) {
}

void VertexPositioning::setMethod(const VertexPositioningMethod method) {
    _method = method;
}

void VertexPositioning::setVertexMargin(const double margin) {
    _vertexMargin = margin;
}

double VertexPositioning::vertexMargin() const {
    return _vertexMargin;
}

void VertexPositioning::setLayerMargin(const double margin) {
    _layerMargin = margin;
}

void VertexPositioning::setVertexSizes(const double size) {
    _vertexSize = size;
}

void VertexPositioning::setVertexSizes(std::vector<double> &&sizes) {
    _vertexSizes = std::move(sizes);
    if (!_vertexSizes.empty()) {
        _vertexSize = ranges::min(_vertexSizes);
    }
}

/** Sort the incident edges of all vertices based on the current ordering within each layer.
 *
 * @param graph A connected DAG.
 * @param layering  The ordering of the vertices in each layer.
 */
void VertexPositioning::sortIncidentEdges(SPDirectedGraph& graph, SPLayering& layering) {
    const int numLayers = static_cast<int>(layering.orders.size());
    auto& inEdgeIds = graph.getInEdgeIdsRef();
    auto& outEdgeIds = graph.getOutEdgeIdsRef();
    for (int i = 0; i < numLayers; i++) {
        for (const auto u : layering.orders[i]) {
            ranges::sort(inEdgeIds[u], [&](const int a, const int b) {
                return layering.positions[i - 1][graph.getEdge(a).u] < layering.positions[i - 1][graph.getEdge(b).u];
            });
            ranges::sort(outEdgeIds[u], [&](const int a, const int b) {
                return layering.positions[i + 1][graph.getEdge(a).v] < layering.positions[i + 1][graph.getEdge(b).v];
            });
        }
    }
}

/** Assign y coordinates for each vertex based on the layer margin.
 *
 * @param graph A connected DAG.
 * @param layering  The ordering of the vertices in each layer.
 * @return Y coordinates.
 */
std::vector<double> VertexPositioning::assignYCoordinates(SPDirectedGraph& graph, SPLayering& layering) const {
    const int n = static_cast<int>(graph.numVertices());
    const int numLayers = static_cast<int>(layering.orders.size());
    vector<double> heights(numLayers);
    for (int layerIndex = 1; layerIndex < numLayers; layerIndex++) {
        double vertexMargin = 0.0;
        for (const auto u : layering.orders[layerIndex]) {
            for (const auto& edge : graph.getInEdges(u)) {
                const int v = edge.u;
                double margin = (vertexSizeAt(u) + vertexSizeAt(v)) / 2.0;
                vertexMargin = max(vertexMargin, margin);
            }
        }
        heights[layerIndex] = heights[layerIndex - 1] + _layerMargin * (layering.layerRanks[layerIndex] - layering.layerRanks[layerIndex - 1]) + vertexMargin;
    }
    vector<double> positions(n);
    for (int u = 0; u < n; u++) {
        positions[u] = heights[layering.idToLayer[u]];
    }
    return positions;
}

/** Align a vertex as closely as possible to the median position of the vertices it is connected to in the previous layer.
 *
 * @param graph A connected DAG.
 * @param layering The ordering of the vertices in each layer.
 * @param forward Whether it is from low rank to high rank.
 * @param leftToRight Whether it is from left to right.
 * @return A roots vector and an aligns vector.
 * The root is the ID of the first vertex in the uninterrupted sequence of vertices sharing the same X coordinate,
 * and align is a circular linked list pointing to the next vertex with the same X coordinate.
 */
std::pair<VertexPositioning::RootVec, VertexPositioning::AlignVec> VertexPositioning::verticalAlignment(
    SPDirectedGraph& graph, SPLayering& layering, const bool forward, const bool leftToRight) {
    const int n = static_cast<int>(graph.numVertices());
    if (n == 0) {
        return {{}, {}};
    }
    const int numLayers = static_cast<int>(layering.orders.size());
    RootVec roots(n);
    AlignVec aligns(n);
    for (int u = 0; u < n; ++u) {
        roots[u] = aligns[u] = u;
    }
    vector<int> candidates(2);
    for (int layerIndex = forward ? 1 : numLayers - 2;
        forward ? layerIndex < numLayers : layerIndex >= 0;
        forward ? ++layerIndex : --layerIndex) {
        const int lastLayerIndex = forward ? layerIndex - 1 : layerIndex + 1;
        const int numVertices = static_cast<int>(layering.orders[layerIndex].size());
        int lastPosition = leftToRight ? -1 : INT32_MAX;
        for (int vertexIndex = leftToRight ? 0 : numVertices - 1;
            leftToRight ? vertexIndex < numVertices : vertexIndex >= 0;
            leftToRight ? ++vertexIndex : --vertexIndex) {
            const int u = layering.orders[layerIndex][vertexIndex];
            const auto& edgeIds = (forward ? graph.getInEdgeIds() : graph.getOutEdgeIds())[u];
            if (const int numEdges = static_cast<int>(edgeIds.size()); numEdges == 0) {
                continue;
            } else if (numEdges % 2 == 1) {
                const auto& edge = graph.getEdge(edgeIds[numEdges / 2]);
                candidates[0] = forward ? edge.u : edge.v;
                candidates[1] = -1;
            } else {
                const auto& edge1 = graph.getEdge(edgeIds[(numEdges - 1) / 2]);
                const auto& edge2 = graph.getEdge(edgeIds[numEdges / 2]);
                candidates[0] = forward ? edge1.u : edge1.v;
                candidates[1] = forward ? edge2.u : edge2.v;
                if (!leftToRight) {
                    swap(candidates[0], candidates[1]);
                }
            }
            for (const auto v : candidates) {
                if (v == -1) {
                    continue;
                }
                if (const int posV = layering.positions[lastLayerIndex][v]; leftToRight ? lastPosition < posV : lastPosition > posV) {
                    aligns[v] = u;
                    roots[u] = roots[v];
                    aligns[u] = roots[v];
                    lastPosition = posV;
                    break;
                }
            }
        }
    }
    return {roots, aligns};
}

/** Assign the x coordinates for each block.
 *
 * @param graph A DAG.
 * @param layering The ordering of the vertices in each layer.
 * @param roots First vertex that has the same X coordinate as the current vertex.
 * @param aligns Next vertex that has the same X coordinate as the current vertex.
 * @param leftToRight Whether it is from left to right.
 * @return X coordinates.
 */
std::vector<double> VertexPositioning::horizontalCompaction(const SPDirectedGraph& graph,
                                                            SPLayering& layering,
                                                            const RootVec& roots, const AlignVec& aligns,
                                                            const bool leftToRight) const {
    const int n = static_cast<int>(graph.numVertices());
    if (n == 0) {
        return {};
    }
    vector<bool> visited(n), hasShifts(n);
    vector<double> positions(n), shifts(n);
    vector<int> sinks(n);
    for (int u = 0; u < n; ++u) {
        sinks[u] = u;
    }
    std::function<void(int)> placeBlock = [&] (int u) {
        if (visited[u]) {
            return;
        }
        visited[u] = true;
        const int root = u;
        do {
            const int layerIndex = layering.idToLayer[u];
            const auto& orders = layering.orders[layerIndex];
            const int posU = layering.positions[layerIndex][u];
            if (leftToRight ? posU > 0 : posU + 1 < static_cast<int>(orders.size())) {
                const int posV = leftToRight ? posU - 1 : posU + 1;
                const int v = roots[orders[posV]];
                placeBlock(v);
                if (sinks[u] == u) {
                    sinks[u] = sinks[v];
                }
                const double vertexMargin = _vertexMargin + (vertexSizeAt(u) + vertexSizeAt(orders[posV])) / 2.0;
                if (sinks[u] != sinks[v]) {
                    const double margin = positions[u] - positions[v] - vertexMargin;
                    if (!hasShifts[sinks[v]] ||
                        (leftToRight ? margin < shifts[sinks[v]] : -margin > shifts[sinks[v]])) {
                        hasShifts[sinks[v]] = true;
                        shifts[sinks[v]] = margin;
                    }
                } else {
                    const double newPos = leftToRight ? positions[v] + vertexMargin : positions[v] - vertexMargin;
                    if (leftToRight ? newPos > positions[root] : newPos < positions[root]) {
                        positions[root] = newPos;
                    }
                }
            }
            u = aligns[u];
        } while (u != root);
    };
    for (int u = 0; u < n; ++u) {
        if (roots[u] == u) {
            placeBlock(u);
        }
    }
    for (int u = 0; u < n; ++u) {
        positions[u] = positions[roots[u]];
        if (hasShifts[sinks[roots[u]]]) {
            positions[u] += shifts[sinks[roots[u]]];
        }
    }
    const double minPosition = ranges::min(positions);
    for (auto& position : positions) {
        position -= minPosition;
    }
    return positions;
}

std::pair<std::vector<double>, std::vector<double>> VertexPositioning::assignCoordinates(SPDirectedGraph& graph, SPLayering& layering) const {
    vector<double> xs;
    switch (_method) {
        case VertexPositioningMethod::BRANDES_KOPF:
            xs = assignCoordinatesBrandesKopf(graph, layering);
    }
    const auto ys = assignYCoordinates(graph, layering);
    return {xs, ys};
}

double VertexPositioning::vertexSizeAt(const int index) const {
    if (index >= static_cast<int>(_vertexSizes.size())) {
        return _vertexSize;
    }
    return _vertexSizes[index];
}

/** Assign X coordinates for all the vertices using the Brandes & Köpf algorithm.
 *
 * @param graph A DAG.
 * @param layering The ordering of the vertices in each layer.
 * @return X coordinates.
 */
std::vector<double> VertexPositioning::assignCoordinatesBrandesKopf(SPDirectedGraph& graph, SPLayering& layering) const {
    const int n = static_cast<int>(graph.numVertices());
    sortIncidentEdges(graph, layering);
    const vector forwardOptions = {true, false};
    const vector leftToRightOptions = {true, false};
    vector<vector<double>> positions;
    for (const auto forward : forwardOptions) {
        for (const auto leftToRight : leftToRightOptions) {
            const auto [roots, aligns] = verticalAlignment(graph, layering, forward, leftToRight);
            positions.emplace_back(horizontalCompaction(graph, layering, roots, aligns, leftToRight));
        }
    }
    vector<double> buffer(4);
    for (int u = 0; u < n; ++u) {
        for (int i = 0; i < 4; ++i) {
            buffer[i] = positions[i][u];
        }
        ranges::sort(buffer);
        positions[0][u] = (buffer[1] + buffer[2]) / 2.0;
    }
    return positions[0];
}
