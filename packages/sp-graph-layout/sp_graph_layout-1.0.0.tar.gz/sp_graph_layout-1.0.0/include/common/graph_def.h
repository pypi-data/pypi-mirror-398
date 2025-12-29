#ifndef GRAPHLAYOUT_GRAPH_DEF_H
#define GRAPHLAYOUT_GRAPH_DEF_H

#include <vector>
#include <unordered_set>
#include <unordered_map>
#include <memory>

namespace graph_layout {

    class EdgeIterationWithIDs;

    struct SPEdge {
        int id, u, v;

        bool operator==(const SPEdge&) const;
    };

    struct SPVirtualEdge {
        SPEdge originalEdge;
        std::vector<int> virtualEdgeIds;
    };

    class SPDirectedGraph {
    public:
        explicit SPDirectedGraph(size_t numVertices);
        ~SPDirectedGraph() = default;

        void updateNumVertices(size_t numVertices);
        [[nodiscard]] size_t numVertices() const { return _numVertices; }
        [[nodiscard]] size_t numEdges() const { return _edges.size(); }
        [[nodiscard]] const std::vector<SPEdge>& edges() const { return _edges; }
        std::vector<SPEdge>& edges() { return _edges;}

        void addEdge(const SPEdge& edge);
        int addEdge(int u, int v);
        void addEdges(const std::vector<std::pair<int ,int>>& edges);
        void addOutEdges(int u, const std::vector<int>& vertices);
        SPEdge& getEdge(int id);
        void removeEdge(int id);

        bool operator==(const SPDirectedGraph& other) const;

        void disableSelfCycleEdges();
        void enableSelfCycleEdges();

        void reverseEdges(const std::unordered_set<int>& ids);
        void reverseEdgesBack();
        [[nodiscard]] bool isReverseEdge(int id) const;

        void sortEdgesById();
        const std::unordered_map<int, size_t>& getEdgeIdToIndexMap();
        const std::vector<int>& getInDegrees();
        const std::vector<int>& getOutDegrees();
        const std::vector<std::vector<int>>& getInVertices();
        const std::vector<std::vector<int>>& getOutVertices();
        std::vector<std::vector<int>>& getInEdgeIdsRef();
        std::vector<std::vector<int>>& getOutEdgeIdsRef();
        const std::vector<std::vector<int>>& getInEdgeIds();
        const std::vector<std::vector<int>>& getOutEdgeIds();
        EdgeIterationWithIDs getInEdges(int v);
        EdgeIterationWithIDs getOutEdges(int u);
        bool hasCycle();

        [[nodiscard]] SPDirectedGraph buildSpanningTree(const std::vector<int>& parents);

    private:
        size_t _numVertices{};
        std::vector<SPEdge> _edges;

        bool _edgeIdToIndexMapInitialized = false;
        std::unordered_map<int, size_t> _edgeIdToIndexMap;

        bool _degreesInitialized = false;
        std::vector<int> _inDegrees;
        std::vector<int> _outDegrees;

        bool _inOutVerticesInitialized = false;
        std::vector<std::vector<int>> _inVertices;
        std::vector<std::vector<int>> _outVertices;

        bool _inOutEdgesInitialized = false;
        std::vector<std::vector<int>> _inEdges;
        std::vector<std::vector<int>> _outEdges;

        bool _hasCycleInitialized = false;
        bool _hasCycle = false;

        std::vector<SPEdge> _selfCycleEdges;

        std::unordered_set<int> _reverseIds;

        void resetInitialization();
        void initializeDegrees();
        void initializeInOutVertices();
        void initializeInOutEdges();
        void initializeHasCycle();
    };

    class EdgeIterationWithIDs {
    public:
        EdgeIterationWithIDs(SPDirectedGraph& graph, const std::vector<int>& ids) : _graph(graph), _ids(ids) {}

        class iterator {
        public:
            explicit iterator(SPDirectedGraph& graph, const std::vector<int>& ids, const int index) : _graph(graph), _ids(ids), _index(index) {}
            const SPEdge &operator*() const;
            iterator& operator++() { ++_index; return *this; }
            bool operator!=(const iterator& other) const { return _index != other._index; }
        private:
            SPDirectedGraph& _graph;
            const std::vector<int>& _ids;
            int _index;
        };

        [[nodiscard]] iterator begin() const { return iterator(_graph, _ids, 0); }
        [[nodiscard]] iterator end() const { return iterator(_graph, _ids, static_cast<int>(_ids.size())); }
    private:
        SPDirectedGraph &_graph;
        const std::vector<int> &_ids;
    };

    class RandomSimpleDirectedGraphGenerator {
    public:
        explicit RandomSimpleDirectedGraphGenerator(const int maxNumVertices) : _minNumVertices(1), _maxNumVertices(maxNumVertices), _allowSelfCycle(false) {}

        [[nodiscard]] SPDirectedGraph generateRandomGraph() const;
        [[nodiscard]] SPDirectedGraph generateRandomGraphWithoutDuplicateEdge() const;
    private:
        int _minNumVertices;
        int _maxNumVertices;
        bool _allowSelfCycle;
    };

    class GraphComponentSplitter {
    public:
        static std::vector<int> getConnectedComponents(const SPDirectedGraph& graph);
        std::vector<SPDirectedGraph>& splitGraph(const SPDirectedGraph& graph);
        [[nodiscard]] SPDirectedGraph mergeBack() const;
        [[nodiscard]] int originalVertexId(int groupIndex, int u) const;

    private:
        std::vector<SPDirectedGraph> _graphs;
        std::vector<std::vector<int>> _groups;
    };

}

#endif //GRAPHLAYOUT_GRAPH_DEF_H