#include "common/graph_def.h"

#include <cassert>
#include <queue>
#include <random>
#include <iostream>
#include <ranges>
#include <algorithm>
using namespace std;
using namespace graph_layout;

bool SPEdge::operator==(const SPEdge& edge) const {
    return id == edge.id && u == edge.u && v == edge.v;
}

SPDirectedGraph::SPDirectedGraph(const size_t numVertices) : _numVertices(numVertices) {
}

void SPDirectedGraph::updateNumVertices(size_t numVertices) {
    _numVertices = numVertices;
}

void SPDirectedGraph::addEdge(const SPEdge& edge) {
    assert(0 <= edge.u && edge.u < static_cast<int>(_numVertices));
    assert(0 <= edge.v && edge.v < static_cast<int>(_numVertices));
    _edges.emplace_back(edge);
    resetInitialization();
}

int SPDirectedGraph::addEdge(const int u, const int v) {
    const int id = static_cast<int>(_edges.size());
    addEdge(SPEdge(id, u, v));
    return id;
}

void SPDirectedGraph::addEdges(const vector<pair<int, int>>& edges) {
    for (const auto& [u, v]: edges) {
        addEdge(u, v);
    }
}

void SPDirectedGraph::addOutEdges(const int u, const vector<int>& vertices) {
    for (const auto& v: vertices) {
        addEdge(u, v);
    }
}

SPEdge& SPDirectedGraph::getEdge(const int id) {
    const int index = static_cast<int>(getEdgeIdToIndexMap().find(id)->second);
    return _edges[index];
}

void SPDirectedGraph::removeEdge(const int id) {
    resetInitialization();
    const int index = static_cast<int>(getEdgeIdToIndexMap().find(id)->second);
    _edges[index] = _edges[_edges.size() - 1];
    _edges.pop_back();
}

bool SPDirectedGraph::operator==(const SPDirectedGraph& other) const {
    if (_numVertices != other._numVertices) {
        return false;
    }
    if (numEdges() != other.numEdges()) {
        return false;
    }
    for (size_t i = 0; i < numEdges(); ++i) {
        if (_edges[i] != other._edges[i]) {
            return false;
        }
    }
    return true;
}

/**
 * Temporarily remove all self-cycle edges.
 */
void SPDirectedGraph::disableSelfCycleEdges() {
    resetInitialization();
    int newNumEdges = 0;
    for (auto& _edge : _edges) {
        if (_edge.u == _edge.v) {
            _selfCycleEdges.emplace_back(_edge);
        } else {
            _edges[newNumEdges++] = _edge;
        }
    }
    _edges.erase(_edges.begin() + newNumEdges, _edges.end());
}

/**
 * Add self-cycle edges back.
 */
void SPDirectedGraph::enableSelfCycleEdges() {
    resetInitialization();
    _edges.insert(_edges.end(), _selfCycleEdges.begin(), _selfCycleEdges.end());
}

/** Temporarily reverse some edges.
 *
 * @param ids Edge IDs.
 */
void SPDirectedGraph::reverseEdges(const std::unordered_set<int> &ids) {
    resetInitialization();
    _reverseIds = ids;
    for (auto& [id, u, v] : _edges) {
        if (_reverseIds.contains(id)) {
            swap(u, v);
        }
    }
}

/**
 * Reverse some edges back.
 */
void SPDirectedGraph::reverseEdgesBack() {
    resetInitialization();
    for (auto& [id, u, v] : _edges) {
        if (_reverseIds.contains(id)) {
            swap(u, v);
        }
    }
    _reverseIds.clear();
}

bool SPDirectedGraph::isReverseEdge(const int id) const {
    return _reverseIds.contains(id);
}

void SPDirectedGraph::sortEdgesById() {
    ranges::sort(_edges, [] (const SPEdge &a, const SPEdge &b) {
        return a.id < b.id;
    });
}

const unordered_map<int, size_t>& SPDirectedGraph::getEdgeIdToIndexMap() {
    if (!_edgeIdToIndexMapInitialized) {
        _edgeIdToIndexMap.clear();
        for (size_t i = 0; i < _edges.size(); i++) {
            _edgeIdToIndexMap[_edges[i].id] = i;
        }
        _edgeIdToIndexMapInitialized = true;
    }
    return _edgeIdToIndexMap;
}

const vector<int>& SPDirectedGraph::getInDegrees() {
    if (!_degreesInitialized) {
        initializeDegrees();
    }
    return _inDegrees;
}

const vector<int>& SPDirectedGraph::getOutDegrees() {
    if (!_degreesInitialized) {
        initializeDegrees();
    }
    return _outDegrees;
}

const vector<vector<int>>& SPDirectedGraph::getInVertices() {
    if (!_inOutVerticesInitialized) {
        initializeInOutVertices();
    }
    return _inVertices;
}

const vector<vector<int>>& SPDirectedGraph::getOutVertices() {
    if (!_inOutVerticesInitialized) {
        initializeInOutVertices();
    }
    return _outVertices;
}

std::vector<std::vector<int>>& SPDirectedGraph::getInEdgeIdsRef() {
    if (!_inOutEdgesInitialized) {
        initializeInOutEdges();
    }
    return _inEdges;
}

std::vector<std::vector<int>>& SPDirectedGraph::getOutEdgeIdsRef() {
    if (!_inOutEdgesInitialized) {
        initializeInOutEdges();
    }
    return _outEdges;
}

const vector<vector<int>>& SPDirectedGraph::getInEdgeIds() {
    return getInEdgeIdsRef();
}

const vector<vector<int>>& SPDirectedGraph::getOutEdgeIds() {
    return getOutEdgeIdsRef();
}

EdgeIterationWithIDs SPDirectedGraph::getInEdges(const int v) {
    return {*this, getInEdgeIds()[v]};
}

EdgeIterationWithIDs SPDirectedGraph::getOutEdges(const int u) {
    return {*this, getOutEdgeIds()[u]};
}

bool SPDirectedGraph::hasCycle() {
    if (!_hasCycleInitialized) {
        initializeHasCycle();
    }
    return _hasCycle;
}

/** Build a spanning tree based on a list of parent edge IDs.
 *
 * @param parents Edge IDs. The vertex that has no parent has an edge ID of -1.
 * @return A spanning tree.
 */
SPDirectedGraph SPDirectedGraph::buildSpanningTree(const std::vector<int>& parents) {
    const size_t n = numVertices();
    SPDirectedGraph tree(n);
    for (const auto id : parents) {
        if (id >= 0) {
            tree.addEdge(getEdge(id));
        }
    }
    return tree;
}

void SPDirectedGraph::resetInitialization() {
    _edgeIdToIndexMapInitialized = false;
    _degreesInitialized = false;
    _inOutVerticesInitialized = false;
    _inOutEdgesInitialized = false;
    _hasCycleInitialized = false;
}

void SPDirectedGraph::initializeDegrees() {
    _inDegrees = vector(_numVertices, 0);
    _outDegrees = vector(_numVertices, 0);
    for (const auto& edge : _edges) {
        ++_outDegrees[edge.u];
        ++_inDegrees[edge.v];
    }
    _degreesInitialized = true;
}

void SPDirectedGraph::initializeInOutVertices() {
    _inVertices = vector(_numVertices, vector<int>());
    _outVertices = vector(_numVertices, vector<int>());
    for (const auto& edge : _edges) {
        _inVertices[edge.v].emplace_back(edge.u);
        _outVertices[edge.u].emplace_back(edge.v);
    }
    _inOutVerticesInitialized = true;
}

void SPDirectedGraph::initializeInOutEdges() {
    _inEdges = vector(_numVertices, vector<int>());
    _outEdges = vector(_numVertices, vector<int>());
    for (const auto&[id, u, v] : _edges) {
        _inEdges[v].emplace_back(id);
        _outEdges[u].emplace_back(id);
    }
    _inOutEdgesInitialized = true;
}

void SPDirectedGraph::initializeHasCycle() {
    auto inDegrees = vector(getInDegrees());
    const auto& outEdges = getOutEdgeIds();
    const auto& edgeIdToIndexMap = getEdgeIdToIndexMap();
    size_t numVisited = 0;
    queue<int> q;
    for (size_t i = 0; i < _numVertices; i++) {
        if (inDegrees[i] == 0) {
            q.push(static_cast<int>(i));
        }
    }
    while (!q.empty()) {
        const int u = q.front();
        q.pop();
        ++numVisited;
        for (const auto id: outEdges[u]) {
            if (const auto v = _edges[edgeIdToIndexMap.find(id)->second].v; --inDegrees[v] == 0) {
                q.push(static_cast<int>(v));
            }
        }
    }
    _hasCycle = numVisited != _numVertices;
    _hasCycleInitialized = true;
}

const SPEdge & EdgeIterationWithIDs::iterator::operator*() const {
    const auto edgeIndex = _graph.getEdgeIdToIndexMap().find(_ids[_index])->second;
    return _graph.edges()[edgeIndex];
}

/** Generate a random graph.
 *
 * This is mainly used for testing.
 *
 * @return A random graph
 */
SPDirectedGraph RandomSimpleDirectedGraphGenerator::generateRandomGraph() const {
    random_device rd;
    mt19937 gen(rd());
    uniform_int_distribution<> numVerticesDist(_minNumVertices, _maxNumVertices);
    const size_t n = numVerticesDist(gen);
    SPDirectedGraph graph(n);
    uniform_int_distribution<> numEdgesDist(0, static_cast<int>(n * min(static_cast<int>(n), 8)));
    // uniform_int_distribution<> numEdgesDist(0, 16);
    uniform_int_distribution<> verticeIndexDist(0, static_cast<int>(n - 1));
    const size_t m = numEdgesDist(gen);
    for (size_t edgeIndex = 0; edgeIndex < m; ++edgeIndex) {
        const int u = verticeIndexDist(gen);
        const int v = verticeIndexDist(gen);
        if (!_allowSelfCycle && u == v) {
            continue;
        }
        graph.addEdge(u, v);
    }
    return graph;
}

/** Generate a random graph without duplicate edges.
 *
 * This is mainly used for testing.
 *
 * @return A random graph
 */
SPDirectedGraph RandomSimpleDirectedGraphGenerator::generateRandomGraphWithoutDuplicateEdge() const {
    random_device rd;
    mt19937 gen(rd());
    uniform_int_distribution<> numVerticesDist(_minNumVertices, _maxNumVertices);
    const size_t n = numVerticesDist(gen);
    SPDirectedGraph graph(n);
    uniform_int_distribution<> numEdgesDist(0, static_cast<int>(n * min(static_cast<int>(n), 8)));
    uniform_int_distribution<> verticeIndexDist(0, static_cast<int>(n - 1));
    const size_t m = numEdgesDist(gen);
    vector<unordered_set<int>> existingEdges(n);
    for (size_t edgeIndex = 0; edgeIndex < m; ++edgeIndex) {
        const int u = verticeIndexDist(gen);
        const int v = verticeIndexDist(gen);
        if (!_allowSelfCycle && u == v) {
            continue;
        }
        if (existingEdges[u].contains(v)) {
            continue;
        }
        graph.addEdge(u, v);
        existingEdges[u].insert(v);
    }
    return graph;
}
