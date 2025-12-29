#include "common/graph_def.h"

#include <algorithm>
#include <ranges>
#include <functional>
using namespace std;
using namespace graph_layout;

std::vector<int> GraphComponentSplitter::getConnectedComponents(const SPDirectedGraph &graph) {
    const size_t n = graph.numVertices();
    vector<int> parent(n);
    for (int i = 0; i < static_cast<int>(n); ++i) {
        parent[i] = i;
    }
    std::function<int(int)> find = [&] (const int x) {
        if (x == parent[x]) {
            return x;
        }
        return parent[x] = find(parent[x]);
    };
    auto combine = [&] (const int x, const int y) {
        parent[find(x)] = find(y);
    };
    for (const auto &edge : graph.edges()) {
        combine(edge.u, edge.v);
    }
    for (int i = 0; i < static_cast<int>(n); ++i) {
        parent[i] = find(i);
    }
    return parent;
}

std::vector<SPDirectedGraph>& GraphComponentSplitter::splitGraph(const SPDirectedGraph &graph) {
    const size_t n = graph.numVertices();
    const auto parent = getConnectedComponents(graph);
    unordered_map<int, vector<int>> groupsMap;
    for (int i = 0; i < static_cast<int>(n); ++i) {
        groupsMap[parent[i]].emplace_back(i);
    }
    _groups.clear();
    for (auto &val: groupsMap | views::values) {
        ranges::sort(val);
        _groups.emplace_back(val);
    }
    ranges::sort(_groups, [] (const auto &x, const auto &y) {
        return x[0] < y[0];
    });
    vector<size_t> groupIndices(n);
    vector<unordered_map<int, int>> newVertexIndices(_groups.size());
    for (size_t g = 0; g < _groups.size(); ++g) {
        for (int i = 0; i < static_cast<int>(_groups[g].size()); ++i) {
            newVertexIndices[g][_groups[g][i]] = i;
            groupIndices[_groups[g][i]] = g;
        }
    }

    _graphs.clear();
    for (auto &group: _groups) {
        SPDirectedGraph subGraph(group.size());
        _graphs.emplace_back(subGraph);
    }
    for (const auto &edge : graph.edges()) {
        const size_t g = groupIndices[edge.u];
        const int u = newVertexIndices[g][edge.u];
        const int v = newVertexIndices[g][edge.v];
        _graphs[g].addEdge({edge.id, u, v});
    }
    return _graphs;
}

SPDirectedGraph GraphComponentSplitter::mergeBack() const {
    size_t n = 0;
    for (const auto &graph : _graphs) {
        n += graph.numVertices();
    }
    SPDirectedGraph newGraph(n);
    for (size_t g = 0; g < _groups.size(); ++g) {
        for (const auto &edge : _graphs[g].edges()) {
            newGraph.addEdge({edge.id, _groups[g][edge.u], _groups[g][edge.v]});
        }
    }
    newGraph.sortEdgesById();
    return newGraph;
}

int GraphComponentSplitter::originalVertexId(const int groupIndex, const int u) const {
    return _groups[groupIndex][u];
}
