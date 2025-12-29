#ifndef GRAPHLAYOUT_COMPARE_SVG_H
#define GRAPHLAYOUT_COMPARE_SVG_H

#include <string>

namespace graph_layout {
    /** A helper function for unit tests only.
     *
     * @param a
     * @param b
     * @return Whether the two input SVGs are the same.
     */
    bool _compareSVG(const std::string& a, const std::string& b);
}


#endif //GRAPHLAYOUT_COMPARE_SVG_H