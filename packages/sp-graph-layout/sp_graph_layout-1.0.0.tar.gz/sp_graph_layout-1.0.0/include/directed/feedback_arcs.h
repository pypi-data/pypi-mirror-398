#ifndef GRAPHLAYOUT_FEEDBACK_ARCS_H
#define GRAPHLAYOUT_FEEDBACK_ARCS_H

#include <unordered_set>
#include "common/graph_def.h"

namespace graph_layout {

    enum class FeedbackArcsMethod {
        // Eades, P., Lin, X., & Smyth, W. F. (1993).
        // A fast and effective heuristic for the feedback arc set problem.
        // Information processing letters, 47(6), 319-323.
        EADES_93,
        MIN_ID,
    };

    /** Find the feedback arcs from a directed graph. */
    class FeedbackArcsFinder {
    public:
        explicit FeedbackArcsFinder(FeedbackArcsMethod method = FeedbackArcsMethod::MIN_ID);
        ~FeedbackArcsFinder() = default;

        void setMethod(FeedbackArcsMethod method);

        /** Find the feedback arcs from a directed graph.
         *
         * @param graph A graph.
         * @return A set of edge IDs representing the feedback arcs.
         */
        [[nodiscard]] std::unordered_set<int> findFeedbackArcs(SPDirectedGraph& graph) const;
    private:
        FeedbackArcsMethod _method;

        static std::unordered_set<int> findFeedbackArcsEades93(SPDirectedGraph& graph) ;
        static std::unordered_set<int> findFeedbackArcsMinID(SPDirectedGraph& graph) ;
    };

}

#endif //GRAPHLAYOUT_FEEDBACK_ARCS_H