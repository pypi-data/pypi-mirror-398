#include "common/compare_svg.h"
#include "svg_diagram.h"
using namespace std;
using namespace svg_diagram;
using namespace graph_layout;

bool graph_layout::_compareSVG(const string& a, const string& b) {
    XMLElement rootA, rootB;
    rootA.addChildren(XMLElement::parse(a));
    rootB.addChildren(XMLElement::parse(b));
    return rootA == rootB;
}
