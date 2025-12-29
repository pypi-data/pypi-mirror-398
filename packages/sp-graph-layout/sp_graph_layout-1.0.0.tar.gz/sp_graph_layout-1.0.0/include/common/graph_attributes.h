#ifndef GRAPHLAYOUT_GRAPH_ATTRIBUTES_H
#define GRAPHLAYOUT_GRAPH_ATTRIBUTES_H

#include <string>
#include <unordered_map>

namespace graph_layout {

    constexpr std::string ATTRIBUTE_KEY_BG_COLOR = "bgcolor";
    constexpr std::string ATTRIBUTE_KEY_RANK_DIR = "rankdir";
    constexpr std::string ATTRIBUTE_KEY_LABEL = "label";
    constexpr std::string ATTRIBUTE_KEY_SHAPE = "shape";
    constexpr std::string ATTRIBUTE_KEY_FONT_NAME = "fontname";
    constexpr std::string ATTRIBUTE_KEY_FONT_SIZE = "fontsize";
    constexpr std::string ATTRIBUTE_KEY_WIDTH = "width";
    constexpr std::string ATTRIBUTE_KEY_HEIGHT = "height";

    class Attribute {
    public:
        Attribute();
        explicit Attribute(const std::string& value);
        ~Attribute() = default;

        void set(const std::string& value);
        [[nodiscard]] const std::string& value() const;

    protected:
        std::string _raw;
    };

    class AttributeColor : public Attribute {
    public:
        using Attribute::Attribute;

        [[nodiscard]] static std::tuple<double, double, double> toRGB(const std::string& raw);
    };

    class AttributeRankDir : public Attribute {
    public:
        using Attribute::Attribute;

        static const std::string TOP_TO_BOTTOM;
        static const std::string BOTTOM_TO_TOP;
        static const std::string LEFT_TO_RIGHT;
        static const std::string RIGHT_TO_LEFT;
    };

    class AttributeShape : public Attribute {
    public:
        using Attribute::Attribute;

        static const std::string NONE;
        static const std::string CIRCLE;
        static const std::string DOUBLE_CIRCLE;
        static const std::string ELLIPSE;
        static const std::string RECT;
    };

    class Attributes {
    public:
        Attributes() = default;
        ~Attributes() = default;

        [[nodiscard]] std::string graphAttributes(const std::string& key) const;
        void setGraphAttributes(const std::string& key, const std::string& value);
        void setGraphAttributes(const std::unordered_map<std::string, std::string> &attributes);

        [[nodiscard]] std::string vertexAttributes(int u, const std::string& key) const;
        void setVertexAttributes(int u, const std::string& key, const std::string& value);
        void setVertexAttributes(int u, const std::unordered_map<std::string, std::string> &attributes);

        [[nodiscard]] std::string edgeAttributes(int u, const std::string& key) const;
        void setEdgeAttributes(int u, const std::string& key, const std::string& value);
        void setEdgeAttributes(int u, const std::unordered_map<std::string, std::string>& mapping);
        void transferEdgeAttributes(int u, int v);

        [[nodiscard]] std::string rankDir() const;
        void setRankDir(const std::string& value);

        void setVertexShape(int u, const std::string& value);

    private:
        static std::unordered_map<std::string, std::string> DEFAULT_GRAPH_ATTRIBUTE_VALUES;
        static std::unordered_map<std::string, std::string> DEFAULT_VERTEX_ATTRIBUTE_VALUES;
        static std::unordered_map<std::string, std::string> DEFAULT_EDGE_ATTRIBUTE_VALUES;

        std::unordered_map<std::string, std::string> _graphAttributes;
        std::unordered_map<std::string, std::string> _vertexGlobalAttributes;
        std::unordered_map<int, std::unordered_map<std::string, std::string>> _vertexAttributes;
        std::unordered_map<std::string, std::string> _edgeGlobalAttributes;
        std::unordered_map<int, std::unordered_map<std::string, std::string>> _edgeAttributes;
    };

}

#endif //GRAPHLAYOUT_GRAPH_ATTRIBUTES_H