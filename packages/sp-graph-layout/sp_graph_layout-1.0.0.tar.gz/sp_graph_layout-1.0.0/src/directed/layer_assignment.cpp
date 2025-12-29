#include "directed/layer_assignment.h"

#include <queue>
#include <set>
#include <utility>
#include <iostream>
#include <ostream>
#include <ranges>
#include <stack>
using namespace std;
using namespace graph_layout;

LayerAssignment::LayerAssignment(const LayerAssignmentMethod method) : _method(method) {
}

void LayerAssignment::setMethod(const LayerAssignmentMethod method) {
    _method = method;
}

void LayerAssignment::setMinEdgeLengths(unordered_map<int, int>&& minEdgeLens) {
    _minEdgeLens = std::move(minEdgeLens);
}

void LayerAssignment::clearMinEdgeLengths() {
    _minEdgeLens = unordered_map<int, int>();
}

int LayerAssignment::minEdgeLength(const int id) const {
    if (const auto it = _minEdgeLens.find(id); it != _minEdgeLens.end()) {
        return it->second;
    }
    return 1;
}

vector<int> LayerAssignment::rankVertices(SPDirectedGraph& graph) const {
    switch (_method) {
        case LayerAssignmentMethod::TOPOLOGICAL:
        case LayerAssignmentMethod::MIN_NUM_OF_LAYERS:
            return rankVerticesTopological(graph);
        case LayerAssignmentMethod::GANSNER_93:
        case LayerAssignmentMethod::MIN_TOTAL_EDGE_LENGTH:
            return rankVerticesGansner93(graph);
    }
    return {};
}

long long LayerAssignment::computeTotalEdgeLength(const SPDirectedGraph& graph, const vector<int>& ranks) {
    long long cost = 0;
    for (const auto& edge : graph.edges()) {
        cost += ranks[edge.v] - ranks[edge.u];
    }
    return cost;
}

/** Assign vertices to layers with topological sort.
 * This also results in the graph having the minimum possible height.
 *
 * @param graph A DAG.
 * @return The layers that each vertex belongs to.
 */
vector<int> LayerAssignment::rankVerticesTopological(SPDirectedGraph& graph) const {
    const size_t n = graph.numVertices();
    const auto edges = graph.edges();
    vector inDegrees(graph.getInDegrees());
    queue<int> q;
    vector<int> ranks(n);
    for (size_t i = 0; i < n; i++) {
        if (inDegrees[i] == 0) {
            q.emplace(i);
            ranks[i] = 0;
        }
    }
    while (!q.empty()) {
        const auto u = q.front();
        q.pop();
        for (const auto& edge : graph.getOutEdges(u)) {
            const int v = edge.v;
            ranks[v] = max(ranks[v], ranks[u] + minEdgeLength(edge.id));
            if (--inDegrees[v] == 0) {
                q.push(v);
            }
        }
    }
    return ranks;
}

/** Assign vertices to layers with the algorithm in graphviz.
 * This also results in the graph having the minimum total edge length.
 *
 * This algorithm first builds a spanning tree based on the "slack" values.
 * Then it repeatedly finds the edge with the smallest "cut value" in the spanning tree and
 * replaces it with an adjacent edge that has the smallest "slack".
 *
 * @param graph A DAG.
 * @return The layers that each vertex belongs to.
 */
vector<int> LayerAssignment::rankVerticesGansner93(SPDirectedGraph& graph) const {
    const int n = static_cast<int>(graph.numVertices());
    if (n == 0) {
        return {};
    }
    if (n == 1) {
        return {0};
    }
    auto ranks = rankVerticesTopological(graph);
    auto [root, parents] = gansner93InitFeasibleTree(graph, ranks);
    auto tree = graph.buildSpanningTree(parents);
    while (true) {
        auto [minCutIndex, cuts] = gansner93ComputeCutValues(graph, tree, root, parents);
        if (cuts[minCutIndex] >= 0) {
            break;
        }
        const auto cutEdgeId = parents[minCutIndex];
        const auto& cutEdge = graph.getEdge(cutEdgeId);
        tree.removeEdge(cutEdgeId);
        const auto connectedComponents = GraphComponentSplitter::getConnectedComponents(tree);
        int minSlackId = -1, minSlack = 0;
        for (int u = 0; u < n; ++u) {
            if (connectedComponents[u] == connectedComponents[cutEdge.v]) {
                for (const auto& edge : graph.getOutEdges(u)) {
                    if (connectedComponents[edge.v] == connectedComponents[cutEdge.u]) {
                        const int slack = ranks[edge.v] - ranks[u] - minEdgeLength(edge.id);
                        if (minSlackId == -1 || slack < minSlack) {
                            minSlackId = edge.id;
                            minSlack = slack;
                        }
                    }
                }
            }
        }
        const auto& newEdge = graph.getEdge(minSlackId);
        if (minSlack) {
            int delta = minSlack;
            if (connectedComponents[newEdge.u] != connectedComponents[0]) {
                delta = -delta;
            }
            for (int u = 0; u < n; ++u) {
                if (connectedComponents[u] == connectedComponents[0]) {
                    ranks[u] += delta;
                }
            }
        }
        tree.addEdge(newEdge);
        queue<pair<int, int>> q;
        q.emplace(root, -1);
        while (!q.empty()) {
            const auto [u, p] = q.front();
            q.pop();
            for (const auto& edge : tree.getInEdges(u)) {
                const int v = edge.u;
                if (v == p) {
                    continue;
                }
                parents[v] = edge.id;
                q.emplace(v, u);
            }
            for (const auto& edge : tree.getOutEdges(u)) {
                const int v = edge.v;
                if (v == p) {
                    continue;
                }
                parents[v] = edge.id;
                q.emplace(v, u);
            }
        }
    }
    int minRank = ranks[0];
    for (int u = 1; u < n; ++u) {
        minRank = min(minRank, ranks[u]);
    }
    for (int u = 0; u < n; ++u) {
        ranks[u] -= minRank;
    }
    return ranks;
}

/** Find an initial spanning tree based on the given initial ranks.
 *
 * The spanning tree should be "tight", i.e., for every edge in the tree, slack(e) = 0.
 * The "slack" of an edge is defined as its length minus the minimum length of that edge.
 * While the spanning tree does not cover all the vertices in the graph,
 * in each iteration we select a non-tree edge that is incident on the tree and has the minimum slack.
 * We then add it to the spanning tree and adjust the ranks of the vertices
 * that are already in the tree, so that the new edge remains tight.
 *
 * @param graph A DAG.
 * @param ranks Initial ranks, which could be the result of the topological solution,
 * are also used to store the updated ranks.
 * @return The root and a parent vector that represents the spanning tree.
 */
pair<int, vector<int>> LayerAssignment::gansner93InitFeasibleTree(SPDirectedGraph& graph, std::vector<int>& ranks) const {
    const int n = static_cast<int>(graph.numVertices());
    const int m = static_cast<int>(graph.numEdges());
    unordered_map<int, int> slacks;  // slack(e) = rank(e.v) - rank(e.u) - minEdgeLength(e)
    vector parents(n, NO_PARENT);
    set<pair<int, int>> incidentEdges;
    int root = -1;
    auto calcSlack = [&](const SPEdge &edge) {
        return slacks[edge.id] = ranks[edge.v] - ranks[edge.u] - minEdgeLength(edge.id);
    };
    for (int u = 0; u < n; ++u) {
        if (ranks[u] == 0) {
            root = u;
            for (const auto& edge : graph.getOutEdges(u)) {
                incidentEdges.insert(make_pair(calcSlack(edge), edge.id));
            }
            break;
        }
    }
    unordered_set verticesInTree({root});
    auto inTree = [&](const int u) {
        return u == root || parents[u] != -1;
    };
    vector<int> slacksToUpdate(m);
    while (!incidentEdges.empty()) {
        const auto [slack, id] = *incidentEdges.begin();
        incidentEdges.erase(incidentEdges.begin());
        const auto& edge = graph.getEdge(id);
        const bool headInTree = inTree(edge.u);
        if (headInTree && inTree(edge.v)) {
            continue;
        }
        if (slack) {
            int delta = slack;
            if (!headInTree) {
                delta = -delta;
            }
            for (const auto u : verticesInTree) {
                ranks[u] += delta;
            }
            int numSlacksToUpdate = 0;
            for (const auto& val: incidentEdges | views::values) {
                const auto& incidentEdge = graph.getEdge(val);
                if (inTree(incidentEdge.u) ^ inTree(incidentEdge.v)) {
                    slacksToUpdate[numSlacksToUpdate++] = incidentEdge.id;
                }
            }
            for (int i = 0; i < numSlacksToUpdate; ++i) {
                const auto& incidentEdge = graph.getEdge(slacksToUpdate[i]);
                incidentEdges.erase({slacks[incidentEdge.id], incidentEdge.id});
                incidentEdges.insert(make_pair(calcSlack(incidentEdge), incidentEdge.id));
            }
        }
        const int newVertex = headInTree ? edge.v : edge.u;
        parents[newVertex] = id;
        verticesInTree.emplace(newVertex);
        for (const auto& newEdge : graph.getInEdges(newVertex)) {
            if (inTree(newEdge.u)) {
                continue;
            }
            incidentEdges.insert(make_pair(calcSlack(newEdge), newEdge.id));
        }
        for (const auto& newEdge : graph.getOutEdges(newVertex)) {
            if (inTree(newEdge.v)) {
                incidentEdges.erase(make_pair(calcSlack(newEdge), newEdge.id));
                continue;
            }
            incidentEdges.insert(make_pair(calcSlack(newEdge), newEdge.id));
        }
    }
    return {root, parents};
}

/** Compute all cut values of the spanning tree.
 *
 * Removing an edge from the spanning tree results in two connected components.
 * The cut value is defined as the number of edges going from the tail component to the head component,
 * minus the number of edges going from the head component to the tail component.
 *
 * @param graph A DAG.
 * @param tree The spanning tree.
 * @param root The root of the spanning tree.
 * @param parents The edge ids for finding the parent vertex.
 * @return Minimum cut index and the cut values.
 */
pair<int, vector<int>> LayerAssignment::gansner93ComputeCutValues(
    SPDirectedGraph& graph,
    SPDirectedGraph& tree,
    const int root,
    const std::vector<int>& parents) const {
    const int n = static_cast<int>(graph.numVertices());
    stack<int> forward, backward;
    forward.push(root);
    while (!forward.empty()) {
        const int u = forward.top();
        forward.pop();
        backward.push(u);
        for (const auto& edge : tree.getInEdges(u)) {
            if (const int v = edge.u; parents[v] == edge.id) {
                forward.push(v);
            }
        }
        for (const auto& edge : tree.getOutEdges(u)) {
            if (const int v = edge.v; parents[v] == edge.id) {
                forward.push(v);
            }
        }
    }
    vector<int> delta(n);
    for (int u = 0; u < n; ++u) {
        delta[u] = graph.getInDegrees()[u] - graph.getOutDegrees()[u];
    }
    vector<int> cuts(n);
    int minCutIndex = -1;
    while (backward.size() > 1) {
        const auto v = backward.top();
        backward.pop();
        const auto& edge = graph.getEdge(parents[v]);
        cuts[v] = delta[v];
        if (edge.u == v) {
            cuts[v] = -cuts[v];
            delta[edge.v] += delta[v];
        } else {
            delta[edge.u] += delta[v];
        }
        if (minCutIndex == -1 || cuts[v] < cuts[minCutIndex]) {
            minCutIndex = v;
        }
    }
    return {minCutIndex, cuts};
}
