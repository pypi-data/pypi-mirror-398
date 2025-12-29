#ifndef GRAPHLAYOUT_CROSS_MINIMIZATION_H
#define GRAPHLAYOUT_CROSS_MINIMIZATION_H

#include "common/graph_def.h"
#include "common/binary_indexed_tree.h"
#include <functional>

namespace graph_layout {

    /** The struct for storing the results of cross minimization */
    struct SPLayering {
        // Discrete ranks for each layer.
        std::vector<int> layerRanks;
        // Vertex order within each layer.
        std::vector<std::vector<int>> orders;
        // Mapping from a vertex ID to its index in the corresponding layer.
        std::vector<std::unordered_map<int, int>> positions;
        // Mapping from a vertex ID to the layer it belongs to.
        std::unordered_map<int, int> idToLayer;
        // Maximum number of vertices in each layer.
        size_t width;

        /** Initialize the two mappings in this struct.
         *
         * Note that we only guarantee that the mappings are initialized
         * in the return values of `CrossMinimization`.
         */
        void initializeMapping();
    };

    enum class CrossMinimizationMethod {
        // Barycenter heuristic.
        BARYCENTER,
        // Median heuristic.
        MEDIAN,
        // Greedily switch two adjacent vertices.
        PAIRWISE_SWITCH,
    };

    /** Reduce the number of crossings between two adjacent layers. */
    class CrossMinimization {
    public:
        explicit CrossMinimization(CrossMinimizationMethod method = CrossMinimizationMethod::BARYCENTER);
        ~CrossMinimization() = default;

        // The start index for virtual edges.
        static constexpr int VIRTUAL_EDGE_ID_OFFSET = 1000000000;

        void setMethod(CrossMinimizationMethod method);

        /** Reduce the number of crossings between each two adjacent layers.
         *
         * @param graph A connected DAG.
         * @param ranks Layer assignment of vertices.
         * @return Orders of vertices in each layer and any virtual edges added to the graph.
         */
        std::pair<SPLayering, std::vector<SPVirtualEdge>> reduceNumCross(SPDirectedGraph& graph, std::vector<int>& ranks) const;

        /** Add virtual edges to the graph so that no edge spans more than two layers.
         *
         * @param graph A connected DAG.
         * @param ranks Layer assignment of vertices.
         * @return Orders of vertices in each layer and any virtual edges added to the graph.
         */
        static std::pair<SPLayering, std::vector<SPVirtualEdge>> addVirtualEdges(SPDirectedGraph& graph, std::vector<int>& ranks);

        /** Compute the total number of crossings between each two adjacent layers.
         *
         * This function is mainly used for testing.
         *
         * @param graph  A connected DAG.
         * @param layering A cross minimization result.
         * @return Total number of crossings.
         */
        static long long computeNumCross(SPDirectedGraph& graph, const SPLayering& layering);

    private:
        CrossMinimizationMethod _method;

        static long long computeNumCross(
            SPDirectedGraph &graph,
            BinaryIndexedTree &bit,
            const std::vector<int> &order1,
            const std::vector<int> &order2,
            bool forward = true);
        static long long computeNumCross(SPDirectedGraph& graph,
            const std::vector<std::unordered_map<int, int>> &positions,
            std::vector<int> &adjPositionsU,
            std::vector<int> &adjPositionsV,
            int layerIndex, int u, int v, bool forward);
        static long long computeNumCross(SPDirectedGraph& graph,
            const std::vector<std::unordered_map<int, int>> &positions,
            std::vector<int> &adjPositionsU,
            std::vector<int> &adjPositionsV,
            int layerIndex, int u, int v);

        static void reduceNumCrossWithWeightingHeuristic(SPDirectedGraph& graph, SPLayering& layering,
            const std::function<double(SPDirectedGraph&, const std::unordered_map<int, int>&, int, bool)> &weighting);
        static void reduceNumCrossWithBaryCenterHeuristic(SPDirectedGraph& graph, SPLayering& layering);
        static void reduceNumCrossWithMedianHeuristic(SPDirectedGraph& graph, SPLayering& layering);
        static void reduceNumCrossWithPairwiseSwitchHeuristic(SPDirectedGraph& graph, SPLayering& layering);
    };

}

#endif //GRAPHLAYOUT_CROSS_MINIMIZATION_H