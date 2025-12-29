#include "directed/feedback_arcs.h"

#include <queue>
#include <set>
using namespace std;
using namespace graph_layout;

FeedbackArcsFinder::FeedbackArcsFinder(const FeedbackArcsMethod method) : _method(method) {
}

void FeedbackArcsFinder::setMethod(const FeedbackArcsMethod method) {
    _method = method;
}

unordered_set<int> FeedbackArcsFinder::findFeedbackArcs(SPDirectedGraph& graph) const {
    switch (_method) {
    case FeedbackArcsMethod::EADES_93:
        return findFeedbackArcsEades93(graph);
    case FeedbackArcsMethod::MIN_ID:
        return findFeedbackArcsMinID(graph);
    }
    return {};
}

/** Find feedback arcs with the greedy heuristic.
 *
 * While the graph is not empty, the algorithm first tries to remove all sinks and sources,
 * along with their corresponding edges.
 * Then it removes the vertex with the maximum out-degree minus in-degree to break cycles.
 * All the in-edges are added to the feedback arcs set.
 *
 * @param graph A graph.
 * @return A set of edge IDs representing the feedback arcs.
 */
unordered_set<int> FeedbackArcsFinder::findFeedbackArcsEades93(SPDirectedGraph& graph) {
    const auto n = graph.numVertices();
    const auto& edges = graph.edges();
    const auto m = edges.size();
    vector inDegree(graph.getInDegrees());
    vector outDegree(graph.getOutDegrees());
    // Group edges by outdegree minus indegree.
    // so that we can find the edge with the largest difference in amortized O(1) time complexity.
    int bucketUpperBound = static_cast<int>(m) * 2;
    vector<vector<int>> differenceBuckets(bucketUpperBound + 1);
    vector<pair<size_t, size_t>> bucketIndices(n);
    auto removeFromDifferenceBuckets = [&](const int u) {
        auto [bucketIndex, vectorIndex] = bucketIndices[u];
        const auto lastElement = differenceBuckets[bucketIndex][differenceBuckets[bucketIndex].size() - 1];
        differenceBuckets[bucketIndex][vectorIndex] = lastElement;
        differenceBuckets[bucketIndex].pop_back();
        bucketIndices[lastElement].second = vectorIndex;
    };
    auto addToDifferenceBuckets = [&](const int u) {
        size_t index = outDegree[u] - inDegree[u] + m;
        bucketIndices[u] = {index, differenceBuckets[index].size()};
        differenceBuckets[index].emplace_back(u);
        bucketUpperBound = max(bucketUpperBound, static_cast<int>(index));
    };
    queue<int> sources, sinks;
    for (int i = 0; i < static_cast<int>(n); ++i) {
        if (outDegree[i] == 0) {
            sinks.emplace(i);
        }
        if (inDegree[i] == 0) {
            sources.emplace(i);
        }
        addToDifferenceBuckets(i);
    }
    int numPoppedVertices = 0;
    vector<bool> popped(n);
    auto removeNode = [&](const int u) {
        if (popped[u]) {
            return;
        }
        ++numPoppedVertices;
        popped[u] = true;
        removeFromDifferenceBuckets(u);
        for (const auto& edge : graph.getInEdges(u)) {
            if (const int v = edge.u; !popped[v]) {
                if (--outDegree[v] == 0) {
                    sinks.push(v);
                }
                removeFromDifferenceBuckets(v);
                addToDifferenceBuckets(v);
            }
        }
        for (const auto& edge : graph.getOutEdges(u)) {
            if (const int v = edge.v; !popped[v]) {
                if (--inDegree[v] == 0) {
                    sources.push(v);
                }
                removeFromDifferenceBuckets(v);
                addToDifferenceBuckets(v);
            }
        }
    };
    // In each iteration, we first remove all source and sink nodes,
    // and then break cycles by reversing all incoming edges of the node
    // with the largest outdegree minus indegree.
    unordered_set<int> feedbackArcs;
    while (numPoppedVertices < static_cast<int>(n)) {
        while (!sinks.empty()) {
            removeNode(sinks.front());
            sinks.pop();
        }
        while (!sources.empty()) {
            removeNode(sources.front());
            sources.pop();
        }
        if (numPoppedVertices < static_cast<int>(n)) {
            while (bucketUpperBound >= 0) {
                if (differenceBuckets[bucketUpperBound].empty()) {
                    --bucketUpperBound;
                } else {
                    const int u = differenceBuckets[bucketUpperBound][0];
                    removeNode(u);
                    for (const auto& edge : graph.getInEdges(u)) {
                        if (const int v = edge.u; !popped[v]) {
                            feedbackArcs.emplace(edge.id);
                        }
                    }
                    break;
                }
            }
        }
    }
    return feedbackArcs;
}

std::unordered_set<int> FeedbackArcsFinder::findFeedbackArcsMinID(SPDirectedGraph& graph) {
    const auto n = graph.numVertices();
    vector inDegree(graph.getInDegrees());
    vector outDegree(graph.getOutDegrees());
    set<int> remainingVertices;
    queue<int> sources, sinks;
    for (int i = 0; i < static_cast<int>(n); ++i) {
        remainingVertices.emplace(i);
        if (outDegree[i] == 0) {
            sinks.emplace(i);
        }
        if (inDegree[i] == 0) {
            sources.emplace(i);
        }
    }
    auto removeNode = [&](const int u) {
        if (!remainingVertices.contains(u)) {
            return;
        }
        remainingVertices.erase(u);
        for (const auto& edge : graph.getInEdges(u)) {
            if (const int v = edge.u; --outDegree[v] == 0) {
                sinks.push(v);
            }
        }
        for (const auto& edge : graph.getOutEdges(u)) {
            if (const int v = edge.v; --inDegree[v] == 0) {
                sources.push(v);
            }
        }
    };
    unordered_set<int> feedbackArcs;
    while (!remainingVertices.empty()) {
        while (!sinks.empty()) {
            removeNode(sinks.front());
            sinks.pop();
        }
        while (!sources.empty()) {
            removeNode(sources.front());
            sources.pop();
        }
        if (!remainingVertices.empty()) {
            const int u = *remainingVertices.begin();
            removeNode(u);
            for (const auto& edge : graph.getInEdges(u)) {
                if (const int v = edge.u; remainingVertices.contains(v)) {
                    feedbackArcs.emplace(edge.id);
                }
            }
        }
    }
    return feedbackArcs;
}
