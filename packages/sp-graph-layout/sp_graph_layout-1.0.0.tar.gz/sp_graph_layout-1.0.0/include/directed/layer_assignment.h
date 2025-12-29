#ifndef GRAPHLAYOUT_LAYER_ASSIGNMENT_H
#define GRAPHLAYOUT_LAYER_ASSIGNMENT_H

#include <vector>
#include "common/graph_def.h"

namespace graph_layout {

    enum class LayerAssignmentMethod {
        TOPOLOGICAL,
        MIN_NUM_OF_LAYERS,
        // Gansner, E. R., Koutsofios, E., North, S. C., & Vo, K. P. (2003, May).
        // A Technique for Drawing Directed Graphs.
        GANSNER_93,
        MIN_TOTAL_EDGE_LENGTH,
    };

    class LayerAssignment {
    public:
        explicit LayerAssignment(LayerAssignmentMethod method = LayerAssignmentMethod::GANSNER_93);
        ~LayerAssignment() = default;

        void setMethod(LayerAssignmentMethod method);

        /** Set the minimum length of edges.
         * The length of an edge is the number of layers spanned between its source and target, with a default value of 1.
         *
         * @param minEdgeLens A mapping from edge ID to minimum length.
         */
        void setMinEdgeLengths(std::unordered_map<int, int>&& minEdgeLens);
        void clearMinEdgeLengths();
        [[nodiscard]] int minEdgeLength(int) const;

        /** Assign each vertex to a layer.
         *
         * @param graph A DAG.
         * @return The layers that each vertex belongs to.
         */
        [[nodiscard]] std::vector<int> rankVertices(SPDirectedGraph& graph) const;

        /** Compute the total length for all edges.
         * The length of an edge is the number of layers spanned between its source and target, with a default value of 1.
         *
         * This function is mainly used for testing.
         *
         * @param graph A DAG.
         * @param ranks Assigned layers.
         * @return Total length.
         */
        static long long computeTotalEdgeLength(const SPDirectedGraph& graph, const std::vector<int>& ranks);
    private:
        LayerAssignmentMethod _method;
        std::unordered_map<int, int> _minEdgeLens;

        std::vector<int> rankVerticesTopological(SPDirectedGraph& graph) const;
        std::vector<int> rankVerticesGansner93(SPDirectedGraph& graph) const;

    protected:
        static constexpr int NO_PARENT = -1;

        std::pair<int, std::vector<int>> gansner93InitFeasibleTree(SPDirectedGraph& graph, std::vector<int>& ranks) const;
        std::pair<int, std::vector<int>> gansner93ComputeCutValues(
            SPDirectedGraph&,
            SPDirectedGraph&,
            int root,
            const std::vector<int>& parents) const;
    };

}

#endif //GRAPHLAYOUT_LAYER_ASSIGNMENT_H