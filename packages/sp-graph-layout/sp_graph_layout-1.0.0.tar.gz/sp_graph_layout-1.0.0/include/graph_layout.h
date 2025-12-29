#ifndef GRAPHLAYOUT_GRAPH_LAYOUT_H
#define GRAPHLAYOUT_GRAPH_LAYOUT_H

#include <vector>
#include "common/graph_def.h"
#include "common/graph_attributes.h"
#include "directed/feedback_arcs.h"
#include "directed/layer_assignment.h"
#include "directed/cross_minimization.h"
#include "directed/vertex_positioning.h"

namespace graph_layout {

    /** A Sugiyama style directed graph layout. */
    class DirectedGraphHierarchicalLayout {
    public:
        DirectedGraphHierarchicalLayout();
        ~DirectedGraphHierarchicalLayout() = default;

        [[nodiscard]] std::shared_ptr<SPDirectedGraph> createGraph(size_t numVertices);
        void setGraph(const std::shared_ptr<SPDirectedGraph>& graph);
        [[nodiscard]] std::shared_ptr<SPDirectedGraph> graph() const;

        Attributes& attributes();

        void setFeedbackArcsMethod(FeedbackArcsMethod method);
        void setLayerAssignmentMethod(LayerAssignmentMethod method);
        void setCrossMinimizationMethod(CrossMinimizationMethod method);
        void setVertexPositioningMethod(VertexPositioningMethod method);
        void setLayerMargin(double margin);

        void layoutGraph();
        /** Add numeric vertex labels.
         *
         * @param start The start index.
         */
        void initVertexLabelsWithNumericalValues(int start = 1);
        void setVertexLabels(const std::vector<std::string>& vertexLabels);
        void setEdgeLabel(int edgeId, const std::string& label);

        [[nodiscard]] std::string render() const;
        void render(const std::string& filePath) const;

    private:
        std::shared_ptr<SPDirectedGraph> _graph = nullptr;

        Attributes _attributes;

        FeedbackArcsFinder _feedbackArcsFinder;
        LayerAssignment _layerAssignment;
        CrossMinimization _crossMinimization;
        VertexPositioning _vertexPositioning;

        int _initialNumVertices = 0;
        std::vector<double> _xs, _ys;
        std::vector<SPVirtualEdge> _virtualEdges;

        [[nodiscard]] bool isVirtualVertex(int u) const;
        void adjustCoordinatesByGraphRank();

        void computeVertexSizes();
    };

}

#endif //GRAPHLAYOUT_GRAPH_LAYOUT_H