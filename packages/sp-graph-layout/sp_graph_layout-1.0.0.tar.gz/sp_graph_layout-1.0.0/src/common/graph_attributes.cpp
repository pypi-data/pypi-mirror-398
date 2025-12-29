#include "common/graph_attributes.h"

#include <functional>
#include <utility>
#include <ranges>
using namespace std;
using namespace graph_layout;

const string AttributeRankDir::TOP_TO_BOTTOM = "tb";
const string AttributeRankDir::BOTTOM_TO_TOP = "bt";
const string AttributeRankDir::LEFT_TO_RIGHT = "lr";
const string AttributeRankDir::RIGHT_TO_LEFT = "rl";

const string AttributeShape::NONE = "none";
const string AttributeShape::CIRCLE = "circle";
const string AttributeShape::DOUBLE_CIRCLE = "doublecircle";
const string AttributeShape::ELLIPSE = "ellipse";
const string AttributeShape::RECT = "rect";

unordered_map<string, string> Attributes::DEFAULT_GRAPH_ATTRIBUTE_VALUES = {
    {ATTRIBUTE_KEY_RANK_DIR, AttributeRankDir::TOP_TO_BOTTOM},
    {ATTRIBUTE_KEY_BG_COLOR, "none"},
    {ATTRIBUTE_KEY_FONT_NAME, "Times,serif"},
    {ATTRIBUTE_KEY_FONT_SIZE, "14"},
};

unordered_map<string, string> Attributes::DEFAULT_VERTEX_ATTRIBUTE_VALUES = {
    {ATTRIBUTE_KEY_LABEL, ""},
    {ATTRIBUTE_KEY_SHAPE, AttributeShape::CIRCLE},
};

unordered_map<string, string> Attributes::DEFAULT_EDGE_ATTRIBUTE_VALUES = {
    {ATTRIBUTE_KEY_LABEL, ""},
};

Attribute::Attribute() = default;

Attribute::Attribute(const string& value) : _raw(value) {
}

void Attribute::set(const string &value) {
    _raw = value;
}

const string& Attribute::value() const {
    return _raw;
}

tuple<double, double, double> AttributeColor::toRGB(const string& raw) {
    if (raw == "white") {
        return make_tuple(1.0, 1.0, 1.0);
    }
    return make_tuple(0.0, 0.0, 0.0);
}

string Attributes::graphAttributes(const string &key) const {
    if (const auto it = _graphAttributes.find(key); it != _graphAttributes.end()) {
        return it->second;
    }
    return DEFAULT_GRAPH_ATTRIBUTE_VALUES[key];
}

void Attributes::setGraphAttributes(const string &key, const string &value) {
    _graphAttributes[key] = value;
}

void Attributes::setGraphAttributes(const unordered_map<string, string>& attributes) {
    _graphAttributes = attributes;
}

string Attributes::vertexAttributes(const int u, const string &key) const {
    if (const auto vIt = _vertexAttributes.find(u); vIt != _vertexAttributes.end()) {
        if (const auto it = vIt->second.find(key); it != vIt->second.end()) {
            return it->second;
        }
    }
    if (const auto it = _vertexGlobalAttributes.find(key); it != _vertexGlobalAttributes.end()) {
        return it->second;
    }
    if (const auto it = DEFAULT_VERTEX_ATTRIBUTE_VALUES.find(key); it != DEFAULT_VERTEX_ATTRIBUTE_VALUES.end()) {
        return it->second;
    }
    return graphAttributes(key);
}

void Attributes::setVertexAttributes(const int u, const string &key, const string &value) {
    _vertexAttributes[u][key] = value;
}

void Attributes::setVertexAttributes(const int u, const unordered_map<string, string>& attributes) {
    _vertexAttributes[u] = attributes;
}

string Attributes::edgeAttributes(const int u, const string &key) const {
    if (const auto eIt = _edgeAttributes.find(u); eIt != _edgeAttributes.end()) {
        if (const auto it = eIt->second.find(key); it != eIt->second.end()) {
            return it->second;
        }
    }
    if (const auto it = _edgeGlobalAttributes.find(key); it != _edgeGlobalAttributes.end()) {
        return it->second;
    }
    if (const auto it = DEFAULT_EDGE_ATTRIBUTE_VALUES.find(key); it != DEFAULT_EDGE_ATTRIBUTE_VALUES.end()) {
        return it->second;
    }
    return edgeAttributes(u, key);
}

void Attributes::setEdgeAttributes(const int u, const string &key, const string &value) {
    _edgeAttributes[u][key] = value;
}

void Attributes::setEdgeAttributes(const int u, const unordered_map<string, string>& mapping) {
    _edgeAttributes[u] = mapping;
}

void Attributes::transferEdgeAttributes(const int u, const int v) {
    if (_edgeAttributes.contains(u)) {
        _edgeAttributes[v] = _edgeAttributes[u];
    }
}

string Attributes::rankDir() const {
    return graphAttributes(ATTRIBUTE_KEY_RANK_DIR);
}

void Attributes::setRankDir(const string &value) {
    setGraphAttributes(ATTRIBUTE_KEY_RANK_DIR, value);
}

void Attributes::setVertexShape(const int u, const string &value) {
    setVertexAttributes(u, ATTRIBUTE_KEY_SHAPE, value);
}
