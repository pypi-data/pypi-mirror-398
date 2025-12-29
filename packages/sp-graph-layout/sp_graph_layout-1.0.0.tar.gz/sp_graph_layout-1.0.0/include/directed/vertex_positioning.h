#ifndef GRAPHLAYOUT_VERTEX_POSITIONING_H
#define GRAPHLAYOUT_VERTEX_POSITIONING_H

#include "common/graph_def.h"
#include "directed/cross_minimization.h"

namespace graph_layout {

    enum class VertexPositioningMethod {
        // Brandes, U., & Köpf, B. (2001, September).
        // Fast and simple horizontal coordinate assignment.
        // In International Symposium on Graph Drawing (pp. 31-44). Berlin, Heidelberg: Springer Berlin Heidelberg.
        BRANDES_KOPF,
    };

    class VertexPositioning {
    public:
        explicit VertexPositioning(VertexPositioningMethod method = VertexPositioningMethod::BRANDES_KOPF);
        ~VertexPositioning() = default;

        void setMethod(VertexPositioningMethod method);

        using RootVec = std::vector<int>;
        using AlignVec = std::vector<int>;

        static constexpr double DEFAULT_VERTEX_MARGIN = 30.0;
        static constexpr double DEFAULT_LAYER_MARGIN = 30.0;
        static constexpr double DEFAULT_VERTEX_SIZE = 30.0;

        /** Set the minimum margin between two vertices that are in the same layer.
         *
         * @param margin Vertex margin.
         */
        void setVertexMargin(double margin);
        [[nodiscard]] double vertexMargin() const;

        /** Set the minimum margin between two adjacent layers.
         *
         * @param margin Layer margin.
         */
        void setLayerMargin(double margin);

        /** Set the size for all vertices.
         *
         * @param size Vertex size.
         */
        void setVertexSizes(double size);
        void setVertexSizes(std::vector<double>&& sizes);
        [[nodiscard]] double vertexSizeAt(int index) const;

        /** Assign each vertex a position that satisfies the margin constraints.
         *
         * @param graph A connected DAG.
         * @param layering  The ordering of the vertices in each layer.
         * @return X and Y positions.
         */
        [[nodiscard]] std::pair<std::vector<double>, std::vector<double>> assignCoordinates(SPDirectedGraph& graph, SPLayering& layering) const;

    protected:
        static void sortIncidentEdges(SPDirectedGraph& graph, SPLayering& layering);
        std::vector<double> assignYCoordinates(SPDirectedGraph& graph, SPLayering& layering) const;
        static std::pair<RootVec, AlignVec> verticalAlignment(SPDirectedGraph& graph, SPLayering& layering, bool forward, bool leftToRight);
        std::vector<double> horizontalCompaction(const SPDirectedGraph& graph, SPLayering& layering, const RootVec& roots, const AlignVec& aligns, bool leftToRight) const;

    private:
        VertexPositioningMethod _method;

        double _vertexMargin = DEFAULT_VERTEX_MARGIN;
        double _layerMargin = DEFAULT_LAYER_MARGIN;
        double _vertexSize = DEFAULT_VERTEX_SIZE;
        std::vector<double> _vertexSizes;

        std::vector<double> assignCoordinatesBrandesKopf(SPDirectedGraph& graph, SPLayering& layering) const;
    };

}

#endif //GRAPHLAYOUT_VERTEX_POSITIONING_H